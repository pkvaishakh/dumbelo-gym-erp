"""Admin Home's summary, and one report per category for the Reports screens (each fetches only its own figures)."""
from .attendance import AttendanceView
from .expenses import ExpensesView
from .members import MembersView
from .money import MoneyView
from .overview import OverviewView
from .revenue import RevenueView
from .summary import SummaryView
from .tasks import TasksView

__all__ = ["AttendanceView", "ExpensesView", "MembersView", "MoneyView", "OverviewView", "RevenueView", "SummaryView", "TasksView"]
