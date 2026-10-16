"""One error shape for the whole API: {"error": {"code", "message", "fields"?}}. The web app shows `message` as is."""
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler


class RuleBroken(exceptions.APIException):
    """A business rule said no (expired membership, second check-in today...). 409 with a code the app can switch on."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "rule"

    def __init__(self, code, message):
        super().__init__(detail=message, code=code)
        self.rule_code = code


def exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is None:
        return None
    if isinstance(exc, RuleBroken):
        return Response({"error": {"code": exc.rule_code, "message": str(exc.detail)}}, status=exc.status_code)
    if isinstance(exc, exceptions.ValidationError):
        data = exc.detail
        first = _first_message(data)
        body = {"code": "invalid", "message": first}
        if isinstance(data, dict):
            body["fields"] = data
        return Response({"error": body}, status=response.status_code)
    code = getattr(exc, "default_code", "error")
    detail = exc.detail if hasattr(exc, "detail") else str(exc)
    return Response({"error": {"code": code, "message": str(detail)}}, status=response.status_code)


def _first_message(data):
    if isinstance(data, dict):
        for value in data.values():
            return _first_message(value)
    if isinstance(data, list) and data:
        return _first_message(data[0])
    return str(data)
