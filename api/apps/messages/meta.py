"""Talking to Meta's Graph API for a WhatsApp account. So far one question: the number's own details.

The access token goes in the Authorization header, never in the URL, and Meta's error messages are scrubbed of
the account's credentials before they're kept, so nothing that leaves here can carry one.
"""
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from .models import WhatsAppAccount

GRAPH = "https://graph.facebook.com"
TIMEOUT = 10  # seconds: Test Connection is someone waiting on a screen


class MetaError(Exception):
    """Meta said no, or couldn't be reached. The message is safe to show and keep."""


def _scrub(text: str, account: WhatsAppAccount) -> str:
    for secret in (account.access_token, account.app_secret):
        if secret:
            text = text.replace(secret, "…")
    return text


def _reason(e: HTTPError, account: WhatsAppAccount) -> str:
    """Meta's own words for an error ("Invalid OAuth access token (code 190)"), or the HTTP status without them."""
    try:
        error = json.loads(e.read().decode())["error"]
        text = f"{error['message']} (code {error.get('code', e.code)})"
    except (ValueError, KeyError, TypeError):
        text = f"Meta answered {e.code}"
    return _scrub(text, account)[:200]


def get(account: WhatsAppAccount, path: str, **params) -> dict:
    """GET `/<version>/<path>` with the account's token. Raises MetaError with a reason that is safe to keep."""
    url = f"{GRAPH}/{settings.WHATSAPP_API_VERSION}/{path}" + (f"?{urlencode(params)}" if params else "")
    request = Request(url, headers={"Authorization": f"Bearer {account.access_token}"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        raise MetaError(_reason(e, account)) from None
    except (URLError, TimeoutError, OSError, ValueError):
        # `from None`: the original error carries the request, and nothing about the request belongs in a log.
        raise MetaError("Couldn't reach Meta. Try again in a minute.") from None


def number_details(account: WhatsAppAccount) -> dict:
    """What Meta knows about the number: `display_phone_number`, `verified_name` and `quality_rating`."""
    return get(account, account.phone_number_id, fields="display_phone_number,verified_name,quality_rating")
