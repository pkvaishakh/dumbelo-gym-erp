from django.db import models
from django.utils import timezone

from apps.core.models import GymScoped


class Expense(GymScoped):
    CATEGORIES = [(c.lower(), c) for c in ("Rent", "Salaries", "Utilities", "Equipment", "Maintenance", "Supplies", "Marketing", "Other")]
    METHODS = [("cash", "Cash"), ("upi", "UPI"), ("card", "Card"), ("bank", "Bank transfer")]
    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="expenses")
    category = models.CharField(max_length=12, choices=CATEGORIES)
    amount_paise = models.PositiveIntegerField()
    method = models.CharField(max_length=8, choices=METHODS)
    paid_to = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=200, blank=True)
    spent_on = models.DateField(default=timezone.localdate)
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["-spent_on", "-created_at"]
