from django.db import models


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class GymScoped(TimeStamped):
    """Every row that belongs to a gym carries the gym. All queries inside a gym filter on it (see core.tenancy)."""

    gym = models.ForeignKey("gyms.Gym", on_delete=models.CASCADE, related_name="+", db_index=True)

    class Meta:
        abstract = True
