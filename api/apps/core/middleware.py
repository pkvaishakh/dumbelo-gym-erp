"""Middleware the whole project needs. One: letting the load balancer's health check through."""
from django.conf import settings

HEALTH_PATH = "/api/health/"


class HealthCheckHost:
    """Answers `/api/health/` whatever name it was asked by.

    A load balancer (App Runner, an ALB in front of ECS) checks the container at its own address, so the Host
    header is an IP that ALLOWED_HOSTS can't know in advance and Django would answer 400 — an unhealthy server,
    then a rolled-back deploy. For that one path, which tells nobody anything, we read it as the API's own name.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_PATH and settings.ALLOWED_HOSTS:  # request.path never looks at the Host header
            request.META["HTTP_HOST"] = settings.ALLOWED_HOSTS[0]
        return self.get_response(request)
