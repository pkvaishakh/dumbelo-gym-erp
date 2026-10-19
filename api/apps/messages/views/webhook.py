"""`/api/whatsapp/webhook/`: where Meta tells us about the messages we sent and the replies people send.

No sign-in and no gym: Meta can't send either. Instead each call must be signed with the account's app secret
(`X-Hub-Signature-256`), and the setup handshake must bring the account's verify token. Both answer 403 when they
don't, and a gym's address that doesn't exist answers 404. Left out of the API schema: only Meta calls these.
"""
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import WhatsAppAccount
from ..webhook import receive, signed, verified

BAD_SIGNATURE = {"error": {"code": "bad_signature", "message": "This call isn't signed by Meta for this number."}}
BAD_TOKEN = {"error": {"code": "bad_verify_token", "message": "The verify token doesn't match this number's."}}
NOT_FOUND = {"error": {"code": "not_found", "message": "Not found."}}


class WhatsAppWebhookView(APIView):
    """GET is Meta's one-time handshake; POST is every status and reply after that. Without a slug, Dumbelo's
    shared number; with one, a gym's own."""

    authentication_classes = []
    permission_classes = [AllowAny]  # checked by the signature instead: see the module's docstring

    def account(self, slug: str | None) -> WhatsAppAccount | None:
        accounts = WhatsAppAccount.objects.filter(gym=None) if slug is None else WhatsAppAccount.objects.filter(webhook_slug=slug, gym__isnull=False)
        return accounts.first()  # with its credentials: the app secret checks the signature

    @extend_schema(exclude=True)
    def get(self, request, slug: str | None = None):
        account = self.account(slug)
        if account is None:
            return Response(NOT_FOUND, status=404)
        if not verified(account, request.query_params.get("hub.mode", ""), request.query_params.get("hub.verify_token", "")):
            return Response(BAD_TOKEN, status=403)
        # Meta wants its challenge back as it sent it, as plain text, not JSON
        return HttpResponse(request.query_params.get("hub.challenge", ""), content_type="text/plain")

    @extend_schema(exclude=True)
    def post(self, request, slug: str | None = None):
        account = self.account(slug)
        if account is None:
            return Response(NOT_FOUND, status=404)
        body = request.body  # the bytes as Meta signed them, read before anything parses them
        if not signed(account, body, request.headers.get("X-Hub-Signature-256", "")):
            return Response(BAD_SIGNATURE, status=403)
        receive(account, body)
        return Response({"ok": True})
