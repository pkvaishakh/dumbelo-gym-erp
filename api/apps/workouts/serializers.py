from rest_framework import serializers

from apps.members.models import Member
from apps.members.pt_serializers import BodyPartsField

from .models import DietAssignment, DietPlan, WorkoutAssignment, WorkoutPlan
from .services import can_change

# ---- what's in a plan ----


class ExerciseSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    sets = serializers.IntegerField(min_value=1, max_value=20, required=False, allow_null=True)
    reps = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="8, 8-10 or 30 sec")
    load = serializers.CharField(max_length=30, required=False, allow_blank=True, help_text="50 kg, 16 kg each or Bodyweight")

    def to_internal_value(self, data):
        d = super().to_internal_value(data)
        return {"name": " ".join(d["name"].split()), "sets": d.get("sets"), "reps": d.get("reps", "").strip(), "load": d.get("load", "").strip()}


class WorkoutDaySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=60, help_text="Day 1, or Push day")
    body_parts = BodyPartsField(required=False)
    exercises = ExerciseSerializer(many=True)

    def validate_exercises(self, v):
        if not v:
            raise serializers.ValidationError("Add an exercise to this day")
        if len(v) > 30:
            raise serializers.ValidationError("A day takes at most 30 exercises")
        return v

    def to_internal_value(self, data):
        d = super().to_internal_value(data)
        return {"title": d["title"].strip(), "body_parts": d.get("body_parts", []), "exercises": d["exercises"]}


class MealSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=60, help_text="Breakfast, or Pre-workout snack")
    time = serializers.CharField(max_length=20, required=False, allow_blank=True, help_text="7:30 AM, or After the workout")
    food = serializers.CharField(max_length=300, help_text="What's in it: Oats with banana, or grilled chicken or paneer")
    kcal = serializers.IntegerField(min_value=0, max_value=3000, required=False, allow_null=True)

    def to_internal_value(self, data):
        d = super().to_internal_value(data)
        return {"name": d["name"].strip(), "time": d.get("time", "").strip(), "food": d["food"].strip(), "kcal": d.get("kcal")}


# ---- plans ----


class CoachPlanSerializer(serializers.ModelSerializer):
    """What every plan shows besides what's in it: who wrote it, how many members are on it, and whether you may
    change it."""

    created_by_name = serializers.CharField(source="created_by.user.name", read_only=True)
    members_count = serializers.IntegerField(read_only=True, help_text="Members on it now")
    can_change = serializers.SerializerMethodField(help_text="You wrote it, or you're an admin")

    BASE = ["id", "name", "goal", "is_active", "created_by", "created_by_name", "members_count", "can_change", "created_at", "updated_at"]

    def get_can_change(self, p) -> bool:
        return can_change(p, self.context["request"].gym_role)


class WorkoutPlanSerializer(CoachPlanSerializer):
    days = WorkoutDaySerializer(many=True)

    class Meta:
        model = WorkoutPlan
        fields = CoachPlanSerializer.BASE + ["days"]
        read_only_fields = ["created_by"]

    def validate_days(self, v):
        if not v:
            raise serializers.ValidationError("Add a day to the plan")
        if len(v) > 14:
            raise serializers.ValidationError("A plan takes at most 14 days")
        return v


class DietPlanSerializer(CoachPlanSerializer):
    kcal = serializers.IntegerField(min_value=500, max_value=6000, required=False, allow_null=True, help_text="Calories a day")
    protein_g = serializers.IntegerField(min_value=0, max_value=600, required=False, allow_null=True)
    carbs_g = serializers.IntegerField(min_value=0, max_value=1000, required=False, allow_null=True)
    fat_g = serializers.IntegerField(min_value=0, max_value=400, required=False, allow_null=True)
    meals = MealSerializer(many=True)

    class Meta:
        model = DietPlan
        fields = CoachPlanSerializer.BASE + ["kcal", "protein_g", "carbs_g", "fat_g", "meals"]
        read_only_fields = ["created_by"]

    def validate_meals(self, v):
        if not v:
            raise serializers.ValidationError("Add a meal to the plan")
        if len(v) > 12:
            raise serializers.ValidationError("A day takes at most 12 meals")
        return v


# ---- giving plans to members ----


class PlanAssignmentSerializer(serializers.ModelSerializer):
    """A member's plan with what's in it, so the member's screen draws it from this alone."""

    plan_name = serializers.CharField(source="plan.name", read_only=True)
    goal = serializers.CharField(source="plan.goal", read_only=True)
    member_name = serializers.CharField(source="member.name", read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.user.name", read_only=True)
    current = serializers.SerializerMethodField()

    BASE = ["id", "plan", "plan_name", "goal", "member", "member_name", "assigned_by_name", "assigned_at", "note", "ended_at", "current"]

    def get_current(self, a) -> bool:
        return a.ended_at is None


class WorkoutAssignmentSerializer(PlanAssignmentSerializer):
    days = WorkoutDaySerializer(source="plan.days", many=True, read_only=True)

    class Meta:
        model = WorkoutAssignment
        fields = PlanAssignmentSerializer.BASE + ["days"]
        read_only_fields = fields


class DietAssignmentSerializer(PlanAssignmentSerializer):
    kcal = serializers.IntegerField(source="plan.kcal", read_only=True, allow_null=True)
    protein_g = serializers.IntegerField(source="plan.protein_g", read_only=True, allow_null=True)
    carbs_g = serializers.IntegerField(source="plan.carbs_g", read_only=True, allow_null=True)
    fat_g = serializers.IntegerField(source="plan.fat_g", read_only=True, allow_null=True)
    meals = MealSerializer(source="plan.meals", many=True, read_only=True)

    class Meta:
        model = DietAssignment
        fields = PlanAssignmentSerializer.BASE + ["kcal", "protein_g", "carbs_g", "fat_g", "meals"]
        read_only_fields = fields


class AssignSerializer(serializers.Serializer):
    """Who gets which plan. The view narrows both to what the caller may give: the gym's plans of that kind, and a
    trainer's own members (an admin's: the gym's)."""

    plan = serializers.PrimaryKeyRelatedField(queryset=WorkoutPlan.objects.none())
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects.none())
    note = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def __init__(self, *a, plans=None, members=None, **kw):
        super().__init__(*a, **kw)
        if plans is not None:
            self.fields["plan"].queryset = plans
        if members is not None:
            self.fields["member"].queryset = members
