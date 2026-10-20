"""Taking a demo request from the landing page, and moving it along from the Console."""
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from .models import Lead

# A second ask from the same number within this long updates the first, so a double tap or a retry after a slow
# answer doesn't put the same gym on the list twice.
SAME_ASK = timedelta(days=1)
OPTIONAL = ("email", "note", "utm_source", "utm_medium", "utm_campaign")


def take_lead(data: dict, *, now: datetime | None = None) -> Lead:
    now = now or timezone.now()
    with transaction.atomic():
        earlier = (Lead.objects.select_for_update().filter(phone=data["phone"], status=Lead.NEW, created_at__gte=now - SAME_ASK)
                   .order_by("-created_at").first())
        if not earlier:
            return Lead.objects.create(**data)
        for field, value in data.items():
            if value or field not in OPTIONAL:  # a retry that leaves the optional ones out keeps what came first
                setattr(earlier, field, value)
        earlier.save()
        return earlier


def set_status(lead: Lead, status: str, *, by, now: datetime | None = None) -> Lead:
    lead.status = status
    lead.status_by = by
    lead.status_at = now or timezone.now()
    lead.save(update_fields=["status", "status_by", "status_at"])
    return lead
