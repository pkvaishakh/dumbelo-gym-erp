"""Gym owners who asked for a demo on the landing page: Dumbelo's sales, worked from the Console."""
from django.conf import settings
from django.db import models


class Lead(models.Model):
    BRANCHES = [("1", "1 branch"), ("2-3", "2 to 3 branches"), ("4+", "4 or more branches")]
    NEW, CONTACTED, WON, LOST = "new", "contacted", "won", "lost"
    STATUSES = [(NEW, "New"), (CONTACTED, "Contacted"), (WON, "Signed up"), (LOST, "Not now")]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=13, help_text="+91XXXXXXXXXX")
    email = models.EmailField(blank=True)
    gym_name = models.CharField(max_length=120)
    city = models.CharField(max_length=80)
    branches = models.CharField(max_length=3, choices=BRANCHES)
    note = models.TextField(blank=True)
    # Where they came from, to know which campaigns bring gyms in. Blank when the page had no utm_ tags.
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUSES, default=NEW)
    status_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    status_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["phone", "created_at"])]

    def __str__(self):
        return f"{self.gym_name} ({self.name})"
