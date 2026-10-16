"""Endpoints that belong to no gym. Just one: is the API up?"""
import logging

from django.db import Error, connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

log = logging.getLogger(__name__)


def database_ok() -> bool:
    """One trivial query: a server that can't reach its database isn't healthy, however well gunicorn is running."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Error:  # the base of every database error, a dead connection included
        log.exception("The health check could not reach the database")
        return False
    return True


class HealthView(APIView):
    """`/api/health/`: the load balancer's question, and the first thing to check after a deploy. No sign-in, no gym."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        auth=[],
        summary="Is the API up?",
        description="200 with `{\"status\": \"ok\"}` while the API can reach its database, 503 when it can't.",
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        healthy = database_ok()
        body = {"status": "ok" if healthy else "error", "database": "ok" if healthy else "unreachable"}
        return Response(body, status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE)
