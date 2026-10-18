from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema

from apps.tasks.models import Task
from apps.tasks.services import overdue

from ..period import PARAMS, Period, ReportView
from ..serializers import Tasks


@extend_schema(parameters=PARAMS, responses=Tasks)
class TasksView(ReportView):
    """Tasks due in these days: where they stand, each person's share, and the oldest overdue ones to chase."""

    def report(self, p: Period) -> dict:
        late = overdue(p.gym)
        counts = {
            "total": Count("id"), "todo": Count("id", filter=Q(status=Task.TODO)), "doing": Count("id", filter=Q(status=Task.DOING)),
            "done": Count("id", filter=Q(status=Task.DONE)), "overdue": Count("id", filter=late),
        }
        _, done_before = p.compare("tasks", only=Q(status=Task.DONE))
        people = (
            p.tasks.values("assignee", "assignee__user__name", "assignee__role")
            .annotate(total=counts["total"], done=counts["done"], overdue=counts["overdue"])
            .order_by("-overdue", "-total", "assignee__user__name")
        )
        oldest = p.tasks.filter(late).select_related("assignee__user").order_by("due_date", "due_time", "id")[:5]
        return {
            "totals": p.tasks.aggregate(**counts),
            "before": {"done": done_before},
            "people": [{"id": x["assignee"], "name": x["assignee__user__name"], "role": x["assignee__role"], "total": x["total"], "done": x["done"],
                        "overdue": x["overdue"]} for x in people],
            "late": [{"id": t.pk, "title": t.title, "assignee_name": t.assignee.user.name, "due_date": t.due_date, "due_time": t.due_time,
                      "status": t.status} for t in oldest],
        }
