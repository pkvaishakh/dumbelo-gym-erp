"""Coaching plans a trainer writes once for the gym and gives to members: workout plans and diet plans. Both work the
same way (CoachPlan, PlanAssignment); only what's in them differs."""
from django.db import models
from django.utils import timezone

from apps.core.models import GymScoped


class CoachPlan(GymScoped):
    """A plan for the gym. Every trainer at the gym sees every plan and gives it to their members; only its author or
    an admin changes it. Archived, never deleted."""

    name = models.CharField(max_length=120)
    goal = models.CharField(max_length=160, blank=True, help_text="Who it's for, like Fat loss for beginners")
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    is_active = models.BooleanField(default=True, help_text="Archived plans can't be given to more members")

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlanAssignment(GymScoped):
    """A plan given to a member. A member follows one of each kind at a time: giving another ends this one, which
    stays as history. Concrete models add `plan`."""

    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="+")
    assigned_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    assigned_at = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=300, blank=True, help_text="For the member, like Start light this week")
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.ForeignKey("gyms.GymRole", null=True, blank=True, on_delete=models.PROTECT, related_name="+")

    class Meta:
        abstract = True
        ordering = ["-assigned_at"]


class WorkoutPlan(CoachPlan):
    days = models.JSONField(default=list, help_text="Each day: title, body_parts and exercises (name, sets, reps, load)")

    class Meta(CoachPlan.Meta):
        indexes = [models.Index(fields=["gym", "name"], name="workoutplan_gym_name")]


class WorkoutAssignment(PlanAssignment):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.PROTECT, related_name="assignments")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="workouts")

    class Meta(PlanAssignment.Meta):
        constraints = [models.UniqueConstraint(fields=["member"], condition=models.Q(ended_at__isnull=True), name="one_workout_plan_at_a_time")]
        indexes = [models.Index(fields=["gym", "member"], name="workoutassign_gym_member")]


class DietPlan(CoachPlan):
    """A day of eating: the targets, then each meal with what's in it."""

    kcal = models.PositiveIntegerField(null=True, blank=True, help_text="Calories a day")
    protein_g = models.PositiveSmallIntegerField(null=True, blank=True)
    carbs_g = models.PositiveSmallIntegerField(null=True, blank=True)
    fat_g = models.PositiveSmallIntegerField(null=True, blank=True)
    meals = models.JSONField(default=list, help_text="Each meal: name, time, food and kcal, in the day's order")

    class Meta(CoachPlan.Meta):
        indexes = [models.Index(fields=["gym", "name"], name="dietplan_gym_name")]


class DietAssignment(PlanAssignment):
    plan = models.ForeignKey(DietPlan, on_delete=models.PROTECT, related_name="assignments")
    member = models.ForeignKey("members.Member", on_delete=models.PROTECT, related_name="diets")

    class Meta(PlanAssignment.Meta):
        constraints = [models.UniqueConstraint(fields=["member"], condition=models.Q(ended_at__isnull=True), name="one_diet_plan_at_a_time")]
        indexes = [models.Index(fields=["gym", "member"], name="dietassign_gym_member")]
