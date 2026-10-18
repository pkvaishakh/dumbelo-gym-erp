import re
import secrets

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, Value
from django.db.models.functions import Coalesce

from apps.core.models import GymScoped, TimeStamped

from .crypto import EncryptedTextField

PLACEHOLDER = re.compile(r"\{\{\s*(\d+)\s*\}\}")  # {{1}}, {{2}}… in a template's text


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
                      "end_date": "The day the plan ends", "days_left": "How soon: tomorrow, or in 7 days"},
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

    def fill(self, values: list[str]) -> str:
        """The approved text with the values in place of {{1}}, {{2}}…: the words the person reads."""
        return PLACEHOLDER.sub(lambda m: values[int(m[1]) - 1] if 0 < int(m[1]) <= len(values) else m[0], self.body)


class Message(GymScoped):
    """One WhatsApp message to a member or a staff member, from the moment it is queued to Meta's last word on it.

    The row is written before anything is sent, under a key unique in its gym (`dedupe_key`), so the same message
    can't go twice: a second run, a retry or a crash finds the row already there. A member's reminder for a day is
    `member:<id>:reminder:<date>`, which is also what keeps them to one a day. The words are kept as the person read
    them, filled in from the template, so the desk can see exactly what went.
    """

    #: What a message is about: the template it goes out on. A plan ending soon says how soon in its words.
    KINDS = WhatsAppTemplate.KINDS

    QUEUED, SENT, DELIVERED, READ, FAILED = "queued", "sent", "delivered", "read", "failed"
    STATUSES = [(QUEUED, "Sending"), (SENT, "Sent"), (DELIVERED, "Delivered"), (READ, "Read"), (FAILED, "Failed")]

    member = models.ForeignKey("members.Member", null=True, blank=True, on_delete=models.CASCADE, related_name="messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="+",
                             help_text="A staff member it went to; empty when it went to a member")
    kind = models.CharField(max_length=32, choices=KINDS)
    dedupe_key = models.CharField(max_length=80, help_text="Unique in the gym: the same message is never sent twice")
    # RESTRICT: accounts and templates are never deleted, but a gym's own number goes with the gym and its messages
    account = models.ForeignKey(WhatsAppAccount, null=True, blank=True, on_delete=models.RESTRICT, related_name="messages",
                                help_text="The number it went from; empty when there was none to send from")
    template = models.ForeignKey(WhatsAppTemplate, null=True, blank=True, on_delete=models.RESTRICT, related_name="messages")
    parameters = models.JSONField(default=list, help_text="What filled the template's {{1}}, {{2}}…, in order")
    to = models.CharField(max_length=13, help_text="The number it was sent to, as it was that day")
    text = models.TextField(help_text="The template's words, filled in")
    for_date = models.DateField(help_text="The day in the gym's time zone it was for")
    status = models.CharField(max_length=10, choices=STATUSES, default=QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0, help_text="Times it was handed to the provider")
    next_retry_at = models.DateTimeField(null=True, blank=True, help_text="When a temporary failure is tried again")
    provider = models.CharField(max_length=20, help_text="Which sender handled it (see senders.py)")
    provider_id = models.CharField(max_length=128, blank=True, help_text="The provider's own id for the message")
    error_code = models.CharField(max_length=16, blank=True, help_text="Meta's error code, when it gave one")
    error = models.CharField(max_length=200, blank=True, help_text="Why it failed, in the provider's words")
    # From Meta's webhook, in UTC. Read means delivered too, so a read message always has `delivered_at`.
    delivered_at = models.DateTimeField(null=True, blank=True, help_text="When Meta says it reached their phone")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When Meta says they opened it")
    # Shared-number messages are billed per delivered message, at the gym's rate for the template's category
    billable = models.BooleanField(default=False, help_text="Sent from Rackline's shared number, so billed to the gym")
    rate_paise = models.PositiveIntegerField(default=0, help_text="What it costs the gym once delivered")

    class Meta:
        ordering = ["-for_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["gym", "dedupe_key"], name="one_message_per_key"),
            models.CheckConstraint(condition=Q(member__isnull=False, user__isnull=True) | Q(member__isnull=True, user__isnull=False),
                                   name="message_to_a_member_or_a_user"),
        ]
        indexes = [
            models.Index(fields=["gym", "for_date"], name="message_gym_day"),
            models.Index(fields=["status", "next_retry_at"], name="message_retry_due"),
            models.Index(fields=["account", "provider_id"], name="message_account_meta_id"),  # the webhook's lookup
            models.Index(fields=["gym", "delivered_at"], condition=Q(billable=True), name="message_billable_delivered"),
            models.Index(fields=["status", "updated_at"], name="message_status_changed"),  # Server: failed today
            models.Index(fields=["-created_at", "-id"], name="message_latest"),  # the Console's log, newest first
            models.Index(fields=["delivered_at"], name="message_delivered"),  # Console Home: delivered today and this month
        ]

    def __str__(self):
        return f"{self.member or self.user} · {self.get_kind_display()} · {self.get_status_display()}"

    @staticmethod
    def reminder_key(member_id: int, for_date) -> str:
        """One reminder a member a day: the key every reminder for that day shares."""
        return f"member:{member_id}:reminder:{for_date.isoformat()}"

    #: How far along a message is. Meta's word on it only ever moves it forward; failed is only possible before
    #: it reached the phone.
    PROGRESS = {QUEUED: 0, SENT: 1, DELIVERED: 2, READ: 3}

    @classmethod
    def moves_to(cls, status: str) -> list[str]:
        """The statuses a message may be in for Meta's `status` to replace: only those behind it."""
        if status == cls.FAILED:
            return [cls.QUEUED, cls.SENT]
        return [s for s, rank in cls.PROGRESS.items() if rank < cls.PROGRESS[status]]


class WebhookEvent(TimeStamped):
    """One call Meta made to the webhook, kept exactly as it came, before anything is done with it.

    Only calls signed with the account's app secret are kept. `processed_at` and `error` say how handling it went,
    so a call can be found and run again (`manage.py replay_webhook_events`). Meta is told 200 either way, or it
    would keep sending the same call.
    """

    account = models.ForeignKey(WhatsAppAccount, on_delete=models.CASCADE, related_name="webhook_events")
    body = models.TextField(help_text="What Meta sent, byte for byte as text")
    processed_at = models.DateTimeField(null=True, blank=True)
    error = models.CharField(max_length=200, blank=True, help_text="What went wrong handling it, if anything")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"], name="webhook_event_created"),  # replaying calls since a time
            models.Index(fields=["account", "-created_at"], name="webhook_event_account_latest"),  # Server: Meta's last call
        ]

    def __str__(self):
        return f"{self.account} · {self.created_at:%Y-%m-%d %H:%M}"


class InboundMessage(TimeStamped):
    """A message someone sent to one of the numbers Rackline sends from: the only one acted on is STOP.

    Kept once (Meta's id is unique), so Meta sending the same one twice changes nothing.
    """

    account = models.ForeignKey(WhatsAppAccount, on_delete=models.CASCADE, related_name="inbound_messages")
    meta_id = models.CharField(max_length=128, unique=True, help_text="Meta's id for it (wamid.…)")
    from_number = models.CharField(max_length=16, help_text="Who sent it, with the +")
    kind = models.CharField(max_length=20, help_text="Meta's type: text, button, image…")
    text = models.TextField(blank=True, help_text="Its words, or the button they pressed")
    received_at = models.DateTimeField(help_text="When they sent it, by Meta's clock (UTC)")
    is_stop = models.BooleanField(default=False, help_text="They asked us to stop sending them messages")
    opted_out = models.ManyToManyField("members.Member", blank=True, related_name="+",
                                       help_text="The members it opted out")

    class Meta:
        ordering = ["-received_at"]
        indexes = [models.Index(fields=["account", "from_number"], name="inbound_account_from")]

    def __str__(self):
        return f"{self.from_number}: {self.text[:40]}"


HOURS = [MinValueValidator(0), MaxValueValidator(23)]  # whole hours on a 24-hour clock: 0 is midnight, 18 is 6 PM


def _days_ahead() -> list[int]:
    return [7, 3]


class AutomationSchedule(TimeStamped):
    """When Rackline's automation runs, for every gym: one row, set by Rackline admins (the Console's Automation).

    The reminders go out at `reminder_hour` on each gym's own clock, warning members `days_ahead` days before a
    plan ends; a gym's Rackline invoice is written on its billing day at `invoice_hour`. A gym's own times, where a
    Rackline admin set them, are on its `NotificationRule` rows. The jobs read this on every tick, so a change
    applies on the next one without restarting anything.
    """

    reminder_hour = models.PositiveSmallIntegerField(default=6, validators=HOURS, help_text="The hour reminders go out, on each gym's clock")
    days_ahead = models.JSONField(default=_days_ahead, help_text="How many days before a plan ends members are warned")
    invoice_hour = models.PositiveSmallIntegerField(default=0, validators=HOURS,
                                                    help_text="The hour on a gym's billing day its Rackline invoice is written")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(pk=1), name="one_automation_schedule")]

    def __str__(self):
        return f"Reminders at {self.reminder_hour}:00, {self.days_ahead} days ahead; invoices at {self.invoice_hour}:00"

    @classmethod
    def current(cls) -> "AutomationSchedule":
        """The schedule in force. Before a Rackline admin first saves one, the defaults (unsaved): reading it on
        every tick never writes."""
        return cls.objects.filter(pk=1).first() or cls(pk=1)


class NotificationRule(GymScoped):
    """One gym's word on one of its messages: on or paused, and (for the ones sent at an hour) the times a
    Rackline admin set for this gym in place of Rackline's.

    No row means the defaults: on, except the member's receipt, which a gym turns on itself; and Rackline's times.
    The gym's admins pause and resume their own messages; Rackline admins the messages Rackline sends the gym's
    owner, and every time. Pausing stops the messages, never the desk's reminder list.
    """

    PLAN_ENDING, PLAN_ENDS_TODAY, PAYMENT_DUE = WhatsAppTemplate.PLAN_ENDING, WhatsAppTemplate.PLAN_ENDS_TODAY, WhatsAppTemplate.PAYMENT_DUE
    PAYMENT_RECEIVED, TASK_ASSIGNED = WhatsAppTemplate.PAYMENT_RECEIVED, WhatsAppTemplate.TASK_ASSIGNED
    RACKLINE_INVOICE_DUE, RACKLINE_PAYMENT_RECEIVED = WhatsAppTemplate.RACKLINE_INVOICE_DUE, WhatsAppTemplate.RACKLINE_PAYMENT_RECEIVED

    REMINDERS = (PLAN_ENDING, PLAN_ENDS_TODAY, PAYMENT_DUE)  # the daily list's messages, one a member a day
    GYM_KINDS = (*REMINDERS, PAYMENT_RECEIVED, TASK_ASSIGNED)  # the gym's own messages: its admins switch them
    RACKLINE_KINDS = (RACKLINE_INVOICE_DUE, RACKLINE_PAYMENT_RECEIVED)  # Rackline's to the owner: Rackline admins switch them
    SCHEDULED = (*REMINDERS, RACKLINE_INVOICE_DUE)  # sent at an hour, rather than when something happens
    OFF_BY_DEFAULT = (PAYMENT_RECEIVED,)

    kind = models.CharField(max_length=32, choices=WhatsAppTemplate.KINDS)
    is_on = models.BooleanField(default=True)
    hour = models.PositiveSmallIntegerField(null=True, blank=True, validators=HOURS,
                                            help_text="This gym's hour in place of Rackline's; empty means Rackline's")
    days_ahead = models.JSONField(null=True, blank=True, help_text="A plan ending soon: this gym's days in place of Rackline's")

    class Meta:
        ordering = ["gym", "kind"]
        constraints = [models.UniqueConstraint(fields=["gym", "kind"], name="one_rule_per_gym_message")]

    def __str__(self):
        return f"{self.gym_id} · {self.kind} · {'on' if self.is_on else 'paused'}"
