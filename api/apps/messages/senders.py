"""How a message leaves Rackline.

`WHATSAPP_PROVIDER` picks the sender. The default, `fake`, keeps what it would have sent in memory, so a laptop and
the tests can read the exact words without a WhatsApp account. `whatsapp_cloud` posts the message's template to
Meta's Cloud API from the number the message was queued on (`services.py` picks it from the gym's WhatsApp mode).
"""
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from . import meta
from .models import Message, WhatsAppAccount


class SendFailed(Exception):
    """The provider wouldn't take the message. The reason goes on the Message row for the gym to read.

    `temporary`: trying again later may work, and can't send it twice (the provider turned it away or never got
    it). `code` is the provider's own code for the error, when it gave one.
    """

    def __init__(self, reason: str, code: str = "", temporary: bool = False):
        super().__init__(reason)
        self.code, self.temporary = code, temporary


class Sender(Protocol):
    """What the sending service needs from a provider: a name for the record, and one way to send."""

    name: str

    def send_message(self, message: Message) -> str:
        """Send a queued message to its number and answer with the provider's id for it. Raises SendFailed."""
        ...


class FakeSender:
    """Sends nothing and remembers everything, the way Django's test mail backend does."""

    name = "fake"
    outbox: list[tuple[str, str]] = []  # (to, text) for every message, newest last

    def send_message(self, message: Message) -> str:
        return self.send(message.to, message.text)

    def send(self, to: str, text: str) -> str:
        self.outbox.append((to, text))
        return f"fake-{len(self.outbox)}"


class CloudSender:
    """Meta's WhatsApp Cloud API: the message's template, filled in, from the message's own number."""

    name = "whatsapp_cloud"

    def __init__(self):
        self._accounts: dict[int, WhatsAppAccount] = {}  # with their credentials, read once per run

    def _account(self, account_id: int) -> WhatsAppAccount:
        if account_id not in self._accounts:
            self._accounts[account_id] = WhatsAppAccount.objects.get(pk=account_id)
        return self._accounts[account_id]

    def send_message(self, message: Message) -> str:
        if message.account_id is None or message.template_id is None:
            raise SendFailed("There's no WhatsApp number or template to send this from")
        try:
            return meta.send_template(self._account(message.account_id), message.to, message.template, message.parameters)
        except meta.MetaError as e:
            raise SendFailed(str(e), code=e.code, temporary=e.temporary) from None


SENDERS = {FakeSender.name: FakeSender, CloudSender.name: CloudSender}


def get_sender() -> Sender:
    """The sender this server is set up with."""
    name = settings.WHATSAPP_PROVIDER
    if name not in SENDERS:
        raise ImproperlyConfigured(f"WHATSAPP_PROVIDER is {name!r}; it must be one of {', '.join(SENDERS)}")
    return SENDERS[name]()
