from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Who changed what, when, with the before and after. Payments corrected or voided, roles changed, support views."""

    gym = models.ForeignKey("gyms.Gym", null=True, blank=True, on_delete=models.CASCADE, related_name="audit_log",
                            help_text="Empty for Rackline changes that belong to no gym (a price list)")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    action = models.CharField(max_length=40)
    object_type = models.CharField(max_length=40)
    object_id = models.CharField(max_length=40)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    via_support = models.BooleanField(default=False)
    at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-at"]


def record(request, action, obj, before=None, after=None, gym=None):
    """`gym` is for the Console, which has no X-Gym: the gym a change belongs to (none for Rackline's own rows).
    `request` is None for a change made from the command line, which has no one signed in."""
    role = getattr(request, "gym_role", None)
    user = getattr(request, "user", None)
    return AuditLog.objects.create(
        gym=gym if gym is not None else getattr(request, "gym", None),
        actor=user if user is not None and user.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(obj.pk),
        before=before,
        after=after,
        via_support=getattr(role, "role", None) == "support",
    )
