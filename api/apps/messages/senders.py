"""How a message leaves Rackline. Nothing here calls a real provider yet.

`WHATSAPP_PROVIDER` picks one. The default, `fake`, keeps what it would have sent in memory, so a laptop and
the tests can read the exact words without a WhatsApp account. The real one is a stub until sending through Meta
is built (`docs/decisions.md`, Messages): it finds Rackline's shared number and refuses, so a server switched on
too early records why nothing went out instead of dropping reminders quietly.
"""
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .models import WhatsAppAccount


class SendFailed(Exception):
    """The provider wouldn't take the message. The reason goes on the Message row for the gym to read."""


class Sender(Protocol):
    """What the sending service needs from a provider: a name for the record, and one way to send."""

    name: str

    def send(self, to: str, text: str) -> str:
        """Send `text` to an Indian mobile number and answer with the provider's id for the message."""
        ...


class FakeSender:
    """Sends nothing and remembers everything, the way Django's test mail backend does."""

    name = "fake"
    outbox: list[tuple[str, str]] = []  # (to, text) for every message, newest last

    def send(self, to: str, text: str) -> str:
        self.outbox.append((to, text))
        return f"fake-{len(self.outbox)}"


class CloudSender:
    """Meta's WhatsApp Cloud API: the shape of the real sender, with the call still to come.

    The numbers and their keys are WhatsApp accounts (`models.WhatsAppAccount`), set up in the Console; Rackline's
    shared number is the one with no gym. Until sending through Meta is built, every send is recorded as failed,
    saying why.
    """

    name = "whatsapp_cloud"

    def __init__(self):
        self.account = WhatsAppAccount.objects.defer(*WhatsAppAccount.SECRET_FIELDS).filter(gym=None).first()

    def send(self, to: str, text: str) -> str:
        if self.account is None:
            raise SendFailed("WhatsApp isn't set up: Rackline's shared number hasn't been added in the Console")
        raise SendFailed("WhatsApp isn't connected yet: sending through Meta comes next")


SENDERS = {FakeSender.name: FakeSender, CloudSender.name: CloudSender}


def get_sender() -> Sender:
    """The sender this server is set up with."""
    name = settings.WHATSAPP_PROVIDER
    if name not in SENDERS:
        raise ImproperlyConfigured(f"WHATSAPP_PROVIDER is {name!r}; it must be one of {', '.join(SENDERS)}")
    return SENDERS[name]()
