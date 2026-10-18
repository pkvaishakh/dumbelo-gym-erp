"""What each report answers, for the OpenAPI schema and so the web's generated client is typed. The views build
plain dicts; these only describe them. Money is integer paise; days are the gym's local days."""
from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

from apps.expenses.models import Expense
from apps.finance.models import Account, MoneyMove
from apps.gyms.models import GymRole
from apps.members.models import Payment
from apps.tasks.models import Task


def _int(help_text=""):
    return serializers.IntegerField(help_text=help_text)


def _named(name, value="paise"):
    """One row of a breakdown: what it is and how much."""
    return inline_serializer(name, {"key": serializers.CharField(), "label": serializers.CharField(), value: _int()}, many=True)


_PREVIOUS = inline_serializer("ReportPrevious", {"from": serializers.DateField(), "to": serializers.DateField()},
                              help_text="The same number of days just before, which trends compare against")


def report(name: str, *, trend: bool = True, **fields):
    """A report's shape: the days it covers (and the days just before, when it compares), then its own fields."""
    head = {"from": serializers.DateField(), "to": serializers.DateField(), "days": _int("Days counted, both ends included")}
    if trend:
        head["previous"] = _PREVIOUS  # DRF copies declared fields per serializer, so one instance serves every report
    return inline_serializer(name, {**head, **fields})


def _headline(name, help_text):
    return inline_serializer(name, {"value": _int(), "before": _int("The same figure for the days just before")}, help_text=help_text)


Overview = report(
    "ReportsOverview",
    revenue=_headline("OverviewRevenue", "Collected less refunds"),
    expenses=_headline("OverviewExpenses", "Spent, salaries and bills included"),
    money=_headline("OverviewMoney", "Cash and bank on the last day; `before` is what they held before the first"),
    members=_headline("OverviewMembers", "New members"),
    attendance=_headline("OverviewAttendance", "Member check-ins"),
    tasks=inline_serializer("OverviewTasks", {"value": _int("Done"), "before": _int("Done in the days just before"),
                                              "total": _int("Due in these days")}),
)

Revenue = report(
    "RevenueReport",
    totals=inline_serializer("RevenueTotals", {"revenue_paise": _int("Collected less refunds"), "collected_paise": _int(),
                                               "refunds_paise": _int(), "refunds": _int("How many refunds")}),
    before=inline_serializer("RevenueBefore", {"revenue_paise": _int()}),
    series=inline_serializer("RevenueDay", {"date": serializers.DateField(), "revenue_paise": _int()}, many=True),
    by_plan=_named("RevenueByPlan"),
    by_method=_named("RevenueByMethod"),
    by_branch=_named("RevenueByBranch"),
    refund_list=inline_serializer("ReportRefund", {
        "id": _int(), "on": serializers.DateField(), "member": _int(), "member_name": serializers.CharField(),
        "plan": serializers.CharField(), "method": serializers.ChoiceField(choices=Payment.METHODS), "branch_name": serializers.CharField(),
        "amount_paise": _int(), "reason": serializers.CharField(),
    }, many=True, help_text="The latest refunds, at most 50: `totals.refunds` says how many there were"),
    dues=inline_serializer("RevenueDues", {"members": _int(), "total_paise": _int()}, help_text="What members owe now, whatever the days"),
)

Expenses = report(
    "ExpensesReport",
    totals=inline_serializer("ExpensesTotals", {"spent_paise": _int(), "count": _int()}),
    before=inline_serializer("ExpensesBefore", {"spent_paise": _int()}),
    series=inline_serializer("ExpensesDay", {"date": serializers.DateField(), "spent_paise": _int()}, many=True),
    by_category=_named("ExpensesByCategory"),
    by_method=_named("ExpensesByMethod"),
    by_branch=_named("ExpensesByBranch"),
    bills=inline_serializer("ExpensesBills", {
        "count": _int(), "paid_paise": _int(),
        "rows": inline_serializer("ReportBill", {"id": _int(), "name": serializers.CharField(), "due_on": serializers.DateField(),
                                                 "paid_on": serializers.DateField(), "amount_paise": _int()}, many=True),
    }, help_text="Recurring bills paid from Dues in these days (at most 50 rows)"),
    salaries=inline_serializer("ExpensesSalaries", {
        "count": _int("Salary payments"), "paid_paise": _int(),
        "people": inline_serializer("ReportSalary", {"id": _int(), "name": serializers.CharField(), "paid_paise": _int(),
                                                     "payments": _int()}, many=True),
    }, help_text="Salaries paid in these days, by person"),
    owed=inline_serializer("ExpensesOwed", {
        "bills": _int("Bills inside their reminder days"), "overdue_bills": _int(), "bills_paise": _int(),
        "salaries": _int("Approved salaries not paid in full"), "salaries_paise": _int(),
    }, help_text="What the gym owes now, whatever the days"),
)

Money = report(
    "MoneyReport", trend=False,
    totals=inline_serializer("MoneyReportTotals", {
        "cash_opening_paise": _int(), "cash_closing_paise": _int(), "bank_opening_paise": _int(), "bank_closing_paise": _int(),
        "opening_paise": _int(), "closing_paise": _int(),
    }, help_text="Each account counted once, however many branches share it"),
    accounts=inline_serializer("ReportAccount", {
        "id": _int(), "name": serializers.CharField(), "kind": serializers.ChoiceField(choices=Account.KINDS), "is_active": serializers.BooleanField(),
        "opened_on": serializers.DateField(),
        "shared_with": serializers.ListField(child=serializers.CharField(), help_text="Bank accounts: the other branches that use it"),
        "opening_paise": _int("Before the first day"), "closing_paise": _int("After the last day"),
        "in_paise": _int("Payments and money moved in"), "out_paise": _int("Expenses, refunds and money moved out"),
        "moved_in_paise": _int(), "moved_out_paise": _int(),
        "reconciled": inline_serializer("ReportReconciled", {"up_to": serializers.DateField(), "bank_balance_paise": _int(),
                                                             "by_name": serializers.CharField()},
                                        allow_null=True, help_text="Bank accounts: the latest reconciliation up to the last day"),
    }, many=True),
    moves=inline_serializer("ReportMoves", {
        "count": _int(),
        "rows": inline_serializer("ReportMove", {
            "id": _int(), "on": serializers.DateField(), "kind": serializers.ChoiceField(choices=MoneyMove.KINDS),
            "from_name": serializers.CharField(allow_null=True), "to_name": serializers.CharField(allow_null=True),
            "amount_paise": _int(), "note": serializers.CharField(),
        }, many=True),
    }, help_text="Money moves in these days (at most 50 rows)"),
    counts=inline_serializer("ReportCounts", {
        "count": _int(), "short_paise": _int("Counted less than expected, in all"), "over_paise": _int("Counted more than expected, in all"),
        "to_settle": _int("Differences an admin hasn't settled yet"),
        "rows": inline_serializer("ReportCount", {
            "id": _int(), "day": serializers.DateField(), "branch_name": serializers.CharField(), "counted_paise": _int(),
            "expected_paise": _int(), "difference_paise": _int("Above zero: extra cash. Below zero: short"), "settled": serializers.BooleanField(),
        }, many=True),
    }, help_text="The desk's cash counts in these days (at most 50 rows)"),
)

Members = report(
    "MembersReport",
    totals=inline_serializer("MembersTotals", {"new": _int(), "renewals": _int(), "lapsed": _int("Plans that ran out and weren't renewed")}),
    before=inline_serializer("MembersBefore", {"new": _int(), "renewals": _int()}),
    series=inline_serializer("MembersDay", {"date": serializers.DateField(), "new": _int()}, many=True),
    statuses=inline_serializer("MembersStatuses", {
        "total": _int(), "active": _int(), "expiring": _int(), "due": _int(), "frozen": _int(), "expired": _int(), "none": _int(),
    }, help_text="Every member by status on the last day"),
    branches=inline_serializer("MembersBranch", {"id": _int(), "name": serializers.CharField(), "new": _int(), "renewals": _int(),
                                                 "active": _int("Active, expiring or payment due on the last day")},
                               many=True, help_text="Every branch, when the report covers them all; empty for one branch"),
)

Attendance = report(
    "AttendanceReport",
    totals=inline_serializer("AttendanceTotals", {"member": _int(), "trainer": _int(), "receptionist": _int(), "admin": _int()}),
    before=inline_serializer("AttendanceBefore", {"member": _int()}),
    series=inline_serializer("AttendanceDay", {"date": serializers.DateField(), "member": _int(), "staff": _int()}, many=True),
    sessions=inline_serializer("AttendanceSession", {"session": serializers.CharField(), "member": _int(), "trainer": _int(),
                                                     "receptionist": _int(), "admin": _int()}, many=True),
    branches=inline_serializer("AttendanceBranch", {"id": _int(), "name": serializers.CharField(), "member": _int(), "staff": _int()},
                               many=True, help_text="Every branch, when the report covers them all; empty for one branch"),
)

Tasks = report(
    "TasksReport",
    totals=inline_serializer("TasksTotals", {"total": _int(), "todo": _int(), "doing": _int(), "done": _int(), "overdue": _int()}),
    before=inline_serializer("TasksBefore", {"done": _int()}),
    people=inline_serializer("TasksPerson", {
        "id": _int(), "name": serializers.CharField(), "role": serializers.ChoiceField(choices=GymRole.ROLES),
        "total": _int(), "done": _int(), "overdue": _int(),
    }, many=True),
    late=inline_serializer("TasksLate", {
        "id": _int(), "title": serializers.CharField(), "assignee_name": serializers.CharField(), "due_date": serializers.DateField(),
        "due_time": serializers.TimeField(allow_null=True), "status": serializers.ChoiceField(choices=Task.STATUSES),
    }, many=True, help_text="The oldest overdue tasks, at most 5"),
)

#: Expense category and payment method names, for breakdown labels.
CATEGORY = dict(Expense.CATEGORIES)
METHOD = dict(Payment.METHODS)
