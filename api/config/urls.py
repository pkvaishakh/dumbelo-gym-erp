from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.accounts.views import LoginView, LogoutView, MeView, PasswordView, RefreshView
from apps.attendance.views import CheckInViewSet, DevicePunchView, DeviceViewSet, QRCheckInView
from apps.core.views import HealthView
from apps.expenses.views import ExpenseDueViewSet, ExpenseViewSet, RecurringExpenseViewSet
from apps.finance.views import AccountViewSet, CashView, DrawerCloseViewSet, MoneyMoveViewSet
from apps.gyms.views import BranchViewSet, GymSettingsView, StaffViewSet, SupportAccessViewSet
from apps.members.views import MemberViewSet, OfferViewSet, PaymentViewSet, PlanViewSet, RefundViewSet, SubscriptionViewSet
from apps.messages.views import MessageViewSet
from apps.payroll.views import PayslipViewSet, SalaryRuleViewSet
from apps.platform.views import GymAdminViewSet, GymViewSet
from apps.reports.views import AttendanceView, ExpensesView, MembersView, MoneyView, OverviewView, RevenueView, SummaryView, TasksView
from apps.tasks.views import TaskViewSet

router = DefaultRouter()
router.register("branches", BranchViewSet, basename="branch")
router.register("staff", StaffViewSet, basename="staff")
router.register("support-access", SupportAccessViewSet, basename="support-access")
router.register("plans", PlanViewSet, basename="plan")
router.register("offers", OfferViewSet, basename="offer")
router.register("members", MemberViewSet, basename="member")
router.register("subscriptions", SubscriptionViewSet, basename="subscription")
router.register("payments", PaymentViewSet, basename="payment")
router.register("refunds", RefundViewSet, basename="refund")
router.register("checkins", CheckInViewSet, basename="checkin")
router.register("devices", DeviceViewSet, basename="device")
router.register("tasks", TaskViewSet, basename="task")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("recurring-expenses", RecurringExpenseViewSet, basename="recurring-expense")
router.register("expense-dues", ExpenseDueViewSet, basename="expense-due")
router.register("salary-rules", SalaryRuleViewSet, basename="salary-rule")
router.register("payslips", PayslipViewSet, basename="payslip")
router.register("accounts", AccountViewSet, basename="account")
router.register("money-moves", MoneyMoveViewSet, basename="money-move")
router.register("drawer-closes", DrawerCloseViewSet, basename="drawer-close")
router.register("messages", MessageViewSet, basename="message")
# Rackline's own side (the Console): no X-Gym, Rackline admins only.
router.register("platform/gyms", GymViewSet, basename="platform-gym")
router.register(r"platform/gyms/(?P<gym_id>\d+)/admins", GymAdminViewSet, basename="platform-gym-admin")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", RefreshView.as_view(), name="refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/me/", MeView.as_view(), name="me"),
    path("api/me/password/", PasswordView.as_view(), name="me-password"),
    path("api/checkins/qr/", QRCheckInView.as_view(), name="qr-checkin"),
    path("api/devices/punch/", DevicePunchView.as_view(), name="device-punch"),  # before the router: never shadowed by devices/<pk>/
    path("api/reports/summary/", SummaryView.as_view(), name="summary"),
    path("api/reports/overview/", OverviewView.as_view(), name="report-overview"),
    path("api/reports/revenue/", RevenueView.as_view(), name="report-revenue"),
    path("api/reports/expenses/", ExpensesView.as_view(), name="report-expenses"),
    path("api/reports/money/", MoneyView.as_view(), name="report-money"),
    path("api/reports/members/", MembersView.as_view(), name="report-members"),
    path("api/reports/attendance/", AttendanceView.as_view(), name="report-attendance"),
    path("api/reports/tasks/", TasksView.as_view(), name="report-tasks"),
    path("api/gym/settings/", GymSettingsView.as_view(), name="gym-settings"),
    path("api/cash/", CashView.as_view(), name="cash"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
