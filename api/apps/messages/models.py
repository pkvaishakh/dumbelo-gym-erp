import secrets

from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Coalesce

from apps.core.models import GymScoped, TimeStamped
from apps.reminders.models import ReminderDue

from .crypto import EncryptedTextField


class Message(GymScoped):
    """One reminder that went to a member, or the record of one that didn't.

    A member hears from us at most once a day: that is what the unique constraint says, and it means a
    member whose plan is ending *and* who owes money gets the more pressing of the two, and a provider
    having a bad morning can't turn into a pile of retries. The text is kept as it was sent, so the desk
    can see exactly what the member read.
    """

    SENT, FAILED = "sent", "failed"
    STATUSES = [(SENT, "Sent"), (FAILED, "Failed")]

    member = models.ForeignKey("members.Member", on_delete=models.CASCADE, related_name="messages")
    kind = models.CharField(max_length=12, choices=ReminderDue.KINDS)
    to = models.CharField(max_length=13, help_text="The number it was sent to, as it was that day")
    text = models.TextField()
    for_date = models.DateField(help_text="The day in the gym's time zone this reminder was for")
    status = models.CharField(max_length=8, choices=STATUSES)
    provider = models.CharField(max_length=20, help_text="Which sender handled it (see senders.py)")
    provider_id = models.CharField(max_length=80, blank=True, help_text="The provider's own id for the message")
    error = models.CharField(max_length=200, blank=True, help_text="Why it failed, in the provider's words")

    class Meta:
        ordering = ["-for_date", "-created_at"]
        constraints = [models.UniqueConstraint(fields=["gym", "member", "for_date"], name="one_message_per_member_per_day")]
        indexes = [models.Index(fields=["gym", "for_date"], name="message_gym_day")]

    def __str__(self):
        return f"{self.member} · {self.get_kind_display()} · {self.get_status_display()}"


def _webhook_slug() -> str:
    return secrets.token_hex(8)


def _verify_token() -> str:
    return secrets.token_urlsafe(24)


class WhatsAppAccount(TimeStamped):
    """A WhatsApp number Rackline sends from: Rackline's shared number (no gym) or a gym's own Meta account.

    Rackline admins set it up in the Console. The access token and app secret are encrypted (`crypto.py`) and
    write-only: all anyone reads back is their last 4 characters. The verify token is Rackline's own, made here and
    typed into Meta's webhook settings, so the Console shows it; a gym's admins never see any of these.
    """

    NEW, WORKING, FAILING = "new", "working", "failing"
    STATUS = [(NEW, "Not checked yet"), (WORKING, "Working"), (FAILING, "Not working")]

    gym = models.ForeignKey("gyms.Gym", null=True, blank=True, on_delete=models.CASCADE, related_name="whatsapp_accounts",
                            help_text="Empty for Rackline's shared number")
    waba_id = models.CharField(max_length=32, help_text="Meta's id for the WhatsApp Business account")
    phone_number_id = models.CharField(max_length=32, unique=True, help_text="Meta's id for the number, which messages are sent through")
    display_number = models.CharField(max_length=24, help_text="The number people see, e.g. +91 98000 00000")
    verified_name = models.CharField(max_length=120, blank=True, help_text="The name Meta shows, from the last Test Connection")
    access_token = EncryptedTextField()
    access_token_last4 = models.CharField(max_length=4)
    app_secret = EncryptedTextField(help_text="Checks that a webhook call really came from Meta")
    app_secret_last4 = models.CharField(max_length=4)
    webhook_slug = models.CharField(max_length=32, unique=True, default=_webhook_slug, help_text="A gym's own number's webhook path")
    verify_token = models.CharField(max_length=64, default=_verify_token, help_text="Meta sends it back to prove the webhook is ours")
    status = models.CharField(max_length=8, choices=STATUS, default=NEW)
    checked_at = models.DateTimeField(null=True, blank=True, help_text="When Test Connection last ran")
    last_error = models.CharField(max_length=200, blank=True, help_text="Why the last Test Connection failed, in Meta's words")

    #: Left out of every queryset that only shows an account, so a list never decrypts (or holds) a credential.
    SECRET_FIELDS = ("access_token", "app_secret")

    class Meta:
        ordering = [models.F("gym").asc(nulls_first=True), "display_number"]
        constraints = [
            # One account per gym, and one shared number: no gym counts as gym 0.
            models.UniqueConstraint(Coalesce("gym", Value(0)), name="one_whatsapp_account_per_gym"),
        ]

    def __str__(self):
        return self.display_number

    @property
    def is_shared(self) -> bool:
        return self.gym_id is None

    def set_credentials(self, *, access_token: str | None = None, app_secret: str | None = None) -> list[str]:
        """Put new credentials in place (unsaved). Says which ones changed, by name, for the audit log."""
        changed = []
        if access_token:
            self.access_token, self.access_token_last4 = access_token, access_token[-4:]
            changed.append("access_token")
        if app_secret:
            self.app_secret, self.app_secret_last4 = app_secret, app_secret[-4:]
            changed.append("app_secret")
        return changed


class WhatsAppTemplate(TimeStamped):
    """A message template Meta approved for one account, and how to fill it.

    Meta sends only approved templates, filled in with values in order: `parameters` says which of the message's
    details goes in `{{1}}`, `{{2}}`… of `body`, the text as approved. The status is copied from Meta's dashboard
    by a Rackline admin. A number has at most one approved template for each message and language.
    """

    PLAN_ENDING, PLAN_ENDS_TODAY, PAYMENT_DUE, PAYMENT_RECEIVED = "plan_ending", "plan_ends_today", "payment_due", "payment_received"
    TASK_ASSIGNED, RACKLINE_INVOICE_DUE, RACKLINE_PAYMENT_RECEIVED = "task_assigned", "rackline_invoice_due", "rackline_payment_received"
    KINDS = [
        (PLAN_ENDING, "Plan ending soon"), (PLAN_ENDS_TODAY, "Plan ends today"), (PAYMENT_DUE, "Payment due"),
        (PAYMENT_RECEIVED, "Payment received"), (TASK_ASSIGNED, "Task assigned"),
        (RACKLINE_INVOICE_DUE, "Rackline invoice due"), (RACKLINE_PAYMENT_RECEIVED, "Rackline payment received"),
    ]
    #: The details each message can fill a template with, and what they are. The sender fills them by these names.
    PARAMETERS = {
        PLAN_ENDING: {"first_name": "Their first name", "plan": "The plan's name", "gym": "The gym's name",
                      "end_date": "The day the plan ends", "days_left": "Days until then"},
        PLAN_ENDS_TODAY: {"first_name": "Their first name", "plan": "The plan's name", "gym": "The gym's name"},
        PAYMENT_DUE: {"first_name": "Their first name", "amount": "What they owe", "plan": "The plan's name", "gym": "The gym's name"},
        PAYMENT_RECEIVED: {"first_name": "Their first name", "amount": "What they paid", "plan": "The plan's name",
                           "gym": "The gym's name", "paid_on": "The day they paid"},
        TASK_ASSIGNED: {"first_name": "The staff member's first name", "task": "The task", "gym": "The gym's name",
                        "due_date": "The day it's due"},
        RACKLINE_INVOICE_DUE: {"first_name": "The owner's first name", "gym": "The gym's name", "invoice_number": "The invoice's number",
                               "amount": "What it still owes", "due_date": "The day it's due"},
        RACKLINE_PAYMENT_RECEIVED: {"first_name": "The owner's first name", "gym": "The gym's name", "amount": "What was paid",
                                    "receipt_number": "The receipt's number"},
    }

    UTILITY, MARKETING, AUTHENTICATION = "utility", "marketing", "authentication"
    CATEGORIES = [(UTILITY, "Utility"), (MARKETING, "Marketing"), (AUTHENTICATION, "Authentication")]  # Meta's, as the price list bills them

    PENDING, APPROVED, REJECTED, PAUSED, DISABLED = "pending", "approved", "rejected", "paused", "disabled"
    STATUS = [(PENDING, "Waiting for Meta"), (APPROVED, "Approved"), (REJECTED, "Rejected"), (PAUSED, "Paused"), (DISABLED, "Disabled")]

    account = models.ForeignKey(WhatsAppAccount, on_delete=models.CASCADE, related_name="templates")
    kind = models.CharField(max_length=32, choices=KINDS)
    name = models.CharField(max_length=512, help_text="The template's name in Meta, e.g. plan_ending_v2")
    language = models.CharField(max_length=8, default="en", help_text="Meta's language code, e.g. en or en_US")
    category = models.CharField(max_length=16, choices=CATEGORIES, default=UTILITY)
    body = models.TextField(max_length=1024, help_text="The text as Meta approved it, with {{1}}, {{2}}… where the details go")
    parameters = models.JSONField(default=list, help_text="Which detail fills {{1}}, {{2}}…, in order (see PARAMETERS)")
    status = models.CharField(max_length=10, choices=STATUS, default=PENDING)

    class Meta:
        ordering = ["kind", "language", "-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["account", "name", "language"], name="one_template_per_meta_name"),
            models.UniqueConstraint(fields=["account", "kind", "language"], condition=Q(status="approved"),
                                    name="one_approved_template_per_kind"),
        ]
        indexes = [models.Index(fields=["account", "kind"], name="template_account_kind")]

    def __str__(self):
        return f"{self.name} ({self.language})"
