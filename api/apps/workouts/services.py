"""The rules for coaching plans, the same for workouts and diets: who changes a plan, and giving one to a member."""
from django.db import transaction
from django.utils import timezone

from apps.core.errors import RuleBroken
from apps.members.models import Member

from .models import CoachPlan, PlanAssignment


def can_change(plan: CoachPlan, by) -> bool:
    """Its author and admins change a plan; other trainers copy it."""
    return by.role == "admin" or plan.created_by_id == by.id


@transaction.atomic
def assign_plan(plan: CoachPlan, member: Member, by, note: str = "") -> PlanAssignment:
    """Give a member a plan. The one of its kind they're on now ends, kept as history."""
    Member.objects.select_for_update().filter(pk=member.pk).first()  # two taps at once give one plan
    if not plan.is_active:
        raise RuleBroken("archived", f"{plan.name} is archived. Restore it to give it to members.")
    given = plan.assignments.model.objects
    current = given.filter(member=member, ended_at__isnull=True).first()
    if current and current.plan_id == plan.pk:
        raise RuleBroken("already_assigned", f"{member.name} is already on {plan.name}")
    if current:
        _end(current, by)
    return given.create(gym=member.gym, plan=plan, member=member, assigned_by=by, note=note.strip())


@transaction.atomic
def end_plan(a: PlanAssignment, by) -> PlanAssignment:
    """Take a member off a plan, with nothing in its place."""
    a = type(a).objects.select_for_update().get(pk=a.pk)
    if a.ended_at:
        raise RuleBroken("ended", "This plan has already ended for them")
    return _end(a, by)


def _end(a: PlanAssignment, by) -> PlanAssignment:
    a.ended_at, a.ended_by = timezone.now(), by
    a.save(update_fields=["ended_at", "ended_by", "updated_at"])
    return a
