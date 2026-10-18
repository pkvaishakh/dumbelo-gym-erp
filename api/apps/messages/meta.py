"""Talking to Meta's Graph API for a WhatsApp account: the number's own details, and sending a template.

The access token goes in the Authorization header, never in the URL, and Meta's error messages are scrubbed of
the account's credentials before they're kept, so nothing that leaves here can carry one.
"""
import json
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

from .models import WhatsAppAccount, WhatsAppTemplate

GRAPH = "https://graph.facebook.com"
TIMEOUT = 10  # seconds: Test Connection is someone waiting on a screen

#: Meta's error codes that mean "not now" rather than "no": rate limits, throughput, and Meta having trouble. As
#: text, since Meta's are numbers. Anything else (a bad number, a template Meta doesn't know, an expired token)
#: won't go better by trying again.
TEMPORARY_CODES = {
    "1", "2",  # unknown error; service temporarily unavailable
    "4", "80007", "130429",  # too many calls; the account's rate limit; Cloud API throughput reached
    "131000", "131016",  # something went wrong; service unavailable
    "131048", "131056",  # spam rate limit; too many messages to the same person
    "133004",  # server temporarily unavailable
}
TEMPORARY_HTTP = {429, 500, 502, 503, 504}

UNREACHABLE = "Couldn't reach Meta. Try again in a minute."
NO_ANSWER = "Meta didn't answer, so it may or may not have gone. It won't be sent again on its own."


class MetaError(Exception):
    """Meta said no, or couldn't be reached. The message is safe to show and keep.

    `code` is Meta's error code (or what went wrong, when Meta gave none). `temporary` means trying again later
    may work and can't send anything twice: Meta turned the request away, or never got it.
    """

    def __init__(self, reason: str, code: str = "", temporary: bool = False):
        super().__init__(reason)
        self.code, self.temporary = code, temporary


def _scrub(text: str, account: WhatsAppAccount) -> str:
    for secret in (account.access_token, account.app_secret):
        if secret:
            text = text.replace(secret, "…")
    return text


def _error(e: HTTPError, account: WhatsAppAccount) -> MetaError:
    """Meta's own words for an error ("Invalid OAuth access token (code 190)"), or the HTTP status without them."""
    try:
        error = json.loads(e.read().decode())["error"]
        message, code = error["message"], error.get("code")
    except (ValueError, KeyError, TypeError, AttributeError):
        message = code = None
    if code is None:  # no code of Meta's: go by the HTTP status
        text, code, temporary = message or f"Meta answered {e.code}", e.code, e.code in TEMPORARY_HTTP
    else:
        text, temporary = f"{message} (code {code})", str(code) in TEMPORARY_CODES
    return MetaError(_scrub(text, account)[:200], code=str(code)[:16], temporary=temporary)


def _call(account: WhatsAppAccount, request: Request, no_answer: str) -> dict:
    """Make one call. Raises MetaError with a reason that is safe to keep. `from None` throughout: the original
    error carries the request, and nothing about the request belongs in a log."""
    request.add_header("Authorization", f"Bearer {account.access_token}")
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
    except HTTPError as e:  # before URLError, which it is: Meta answered, with an error
        raise _error(e, account) from None
    except URLError:
        # urllib raises URLError only while connecting and sending, so Meta never had the request.
        raise MetaError(UNREACHABLE, code="unreachable", temporary=True) from None
    except (TimeoutError, OSError, HTTPException):
        # The request went, but the answer didn't come back: Meta may have acted on it.
        raise MetaError(no_answer, code="no_answer") from None
    try:
        return json.loads(body.decode())
    except ValueError:
        raise MetaError(no_answer, code="bad_answer") from None


def _url(path: str) -> str:
    return f"{GRAPH}/{settings.WHATSAPP_API_VERSION}/{path}"


def get(account: WhatsAppAccount, path: str, **params) -> dict:
    """GET `/<version>/<path>` with the account's token."""
    url = _url(path) + (f"?{urlencode(params)}" if params else "")
    return _call(account, Request(url), no_answer=UNREACHABLE)


def post(account: WhatsAppAccount, path: str, body: dict) -> dict:
    """POST JSON to `/<version>/<path>` with the account's token. Not retried here: see TEMPORARY_CODES."""
    request = Request(_url(path), data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return _call(account, request, no_answer=NO_ANSWER)


def number_details(account: WhatsAppAccount) -> dict:
    """What Meta knows about the number: `display_phone_number`, `verified_name` and `quality_rating`."""
    return get(account, account.phone_number_id, fields="display_phone_number,verified_name,quality_rating")


def template_payload(to: str, template: WhatsAppTemplate, values: list[str]) -> dict:
    """Meta's shape for a template message: the number without its +, the template by name and language, and the
    values for {{1}}, {{2}}… in order."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to.lstrip("+"),
        "type": "template",
        "template": {"name": template.name, "language": {"code": template.language}},
    }
    if values:
        payload["template"]["components"] = [{"type": "body", "parameters": [{"type": "text", "text": v} for v in values]}]
    return payload


def send_template(account: WhatsAppAccount, to: str, template: WhatsAppTemplate, values: list[str]) -> str:
    """Send one template message from the account's number. Answers with Meta's id for it (`wamid.…`)."""
    answer = post(account, f"{account.phone_number_id}/messages", template_payload(to, template, values))
    try:
        return str(answer["messages"][0]["id"])[:128]
    except (KeyError, IndexError, TypeError):
        raise MetaError(NO_ANSWER, code="bad_answer") from None
