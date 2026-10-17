from django.db import models
from django.utils import timezone

from apps.core.models import GymScoped, TimeStamped


class Task(GymScoped):
    """Work an admin gives a trainer or receptionist. They start it, post updates and mark it done."""

    TODO, DOING, DONE = "todo", "doing", "done"
    STATUSES = [(TODO, "To do"), (DOING, "In progress"), (DONE, "Done")]

    title = models.CharField(max_length=160)
    details = models.TextField(blank=True)
    assignee = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="tasks")
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="tasks_set")
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True, help_text="Without a time, due by the end of the day")
    status = models.CharField(max_length=6, choices=STATUSES, default=TODO)

    class Meta:
        ordering = ["status", "due_date", "due_time"]
        indexes = [models.Index(fields=["gym", "due_date"], name="task_gym_due")]

    def __str__(self):
        return self.title

    def is_overdue(self, now=None):
        if self.status == self.DONE:
            return False
        now = timezone.localtime(now or timezone.now())
        if self.due_date != now.date():
            return self.due_date < now.date()
        return self.due_time is not None and self.due_time < now.time()


class TaskUpdate(TimeStamped):
    """An update someone posted, or a status change the app logged (started, marked done, reopened)."""

    NOTE, STATUS = "note", "status"
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=6, choices=[(NOTE, "Note"), (STATUS, "Status")], default=NOTE)
    text = models.TextField()

    class Meta:
        ordering = ["created_at"]
