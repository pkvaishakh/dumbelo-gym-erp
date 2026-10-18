"""WhatsApp accounts and their templates: the rules for setting them up. Rackline admins do this, in the Console.

A gym has at most one account and Rackline one shared number. Changing where an account points, or its
credentials, puts it back to "not checked yet" until Test Connection says it works.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.billing.models import GymBilling
from apps.core.errors import RuleBroken
from apps.gyms.models import Gym

from . import meta
from .models import WhatsAppAccount, WhatsAppTemplate

WHERE = ("waba_id", "phone_number_id", "display_number")  # what an account points at; audited, unlike its credentials


def _taken(gym: Gym | None, phone_number_id: str, exclude: int | None = None) -> None:
    others = WhatsAppAccount.objects.exclude(pk=exclude)
    if others.filter(phone_number_id=phone_number_id).exists():
        raise RuleBroken("number_taken", "That phone number id is already set up on Rackline.")
    if exclude is None and others.filter(gym=gym).exists():
        if gym is None:
            raise RuleBroken("account_exists", "Rackline's shared number is already set up. Open it to replace its credentials.")
        raise RuleBroken("account_exists", f"{gym.name} already has a WhatsApp account. Open it to replace its credentials.")


def add_account(*, gym: Gym | None, waba_id: str, phone_number_id: str, display_number: str, access_token: str,
                app_secret: str) -> WhatsAppAccount:
    """A new account, for a gym's own number or (no gym) Rackline's shared one. Not checked until Test Connection."""
    _taken(gym, phone_number_id)
    account = WhatsAppAccount(gym=gym, waba_id=waba_id, phone_number_id=phone_number_id, display_number=display_number)
    account.set_credentials(access_token=access_token, app_secret=app_secret)
    try:
        with transaction.atomic():
            account.save()
    except IntegrityError:  # another Rackline admin added the same one a moment ago
        _taken(gym, phone_number_id)
        raise
    return account


def change_account(account: WhatsAppAccount, **where) -> WhatsAppAccount:
    """New ids or display number. Pointing it at another number means checking it again."""
    changed = {k: v for k, v in where.items() if k in WHERE and getattr(account, k) != v}
    if not changed:
        return account
    if "phone_number_id" in changed:
        _taken(account.gym, changed["phone_number_id"], exclude=account.pk)
    for field, value in changed.items():
        setattr(account, field, value)
    fields = [*changed]
    if {"waba_id", "phone_number_id"} & changed.keys():
        account.status, account.last_error = WhatsAppAccount.NEW, ""
        fields += ["status", "last_error"]
    account.save(update_fields=[*fields, "updated_at"])
    return account


def replace_credentials(account: WhatsAppAccount, *, access_token: str | None = None, app_secret: str | None = None) -> list[str]:
    """New credentials, encrypted as they're saved. Says which changed (names only, never values)."""
    changed = account.set_credentials(access_token=access_token, app_secret=app_secret)
    account.status, account.last_error = WhatsAppAccount.NEW, ""
    account.save(update_fields=[*changed, *[f"{c}_last4" for c in changed], "status", "last_error", "updated_at"])
    return changed


def test_connection(account: WhatsAppAccount) -> WhatsAppAccount:
    """Ask Meta for the number's details with the account's token. Sends nothing to anyone.

    Working: the display number and verified name are taken from Meta. Not working: Meta's reason is kept.
    """
    account = WhatsAppAccount.objects.get(pk=account.pk)  # with its credentials, which views leave out
    try:
        details = meta.number_details(account)
    except meta.MetaError as e:
        account.status, account.last_error = WhatsAppAccount.FAILING, str(e)
    else:
        account.status, account.last_error = WhatsAppAccount.WORKING, ""
        account.display_number = str(details.get("display_phone_number") or account.display_number)[:24]
        account.verified_name = str(details.get("verified_name") or "")[:120]
    account.checked_at = timezone.now()
    account.save(update_fields=["status", "last_error", "display_number", "verified_name", "checked_at", "updated_at"])
    return account


def whatsapp_mode(gym: Gym) -> str:
    """Shared, own or off, from the gym's Rackline plan. A gym without one yet is on the shared number."""
    return getattr(getattr(gym, "billing", None), "whatsapp_mode", GymBilling.SHARED)


def account_for(gym: Gym) -> WhatsAppAccount | None:
    """The account a gym's messages go from, by its WhatsApp mode: the shared number, its own, or none when off.
    Without its credentials: the sender asks for those itself."""
    mode = whatsapp_mode(gym)
    if mode == GymBilling.OFF:
        return None
    qs = WhatsAppAccount.objects.defer(*WhatsAppAccount.SECRET_FIELDS)
    return qs.filter(gym=gym if mode == GymBilling.OWN else None).first()


@transaction.atomic
def save_template(template: WhatsAppTemplate | None, **fields) -> WhatsAppTemplate:
    """Add a template (no `template`) or change one. Only one approved template per message and language, so the
    sender never has to choose."""
    template = template or WhatsAppTemplate()
    for field, value in fields.items():
        setattr(template, field, value)
    # Lock the account: two admins approving two templates for the same message can't both win.
    WhatsAppAccount.objects.select_for_update().only("pk").get(pk=template.account_id)
    same = WhatsAppTemplate.objects.filter(account=template.account_id, language=template.language).exclude(pk=template.pk)
    if same.filter(name=template.name).exists():
        raise RuleBroken("template_exists", f"This number already has {template.name} in {template.language}.")
    if template.status == WhatsAppTemplate.APPROVED and same.filter(kind=template.kind, status=WhatsAppTemplate.APPROVED).exists():
        raise RuleBroken(
            "template_approved",
            f"This number already has an approved template for {template.get_kind_display().lower()} in {template.language}. "
            "Mark that one Paused or Disabled first.",
        )
    template.save()
    return template
