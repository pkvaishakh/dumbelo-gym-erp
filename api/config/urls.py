from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.accounts.views import LoginView, LogoutView, MeView, PasswordView, RefreshView
from apps.attendance.views import CheckInViewSet, DevicePunchView, DeviceViewSet, QRCheckInView
from apps.billing.views import (
    BranchRequestViewSet, ChargeViewSet, ConsoleBranchRequestViewSet, ConsoleInvoicePaymentViewSet, ConsoleInvoiceViewSet, GymPlanPricesView,
    GymPlanView, InvoiceViewSet, PriceListViewSet, RacklinePlanView,
)
from apps.core.views import HealthView
from apps.expenses.views import ExpenseDueViewSet, ExpenseViewSet, RecurringExpenseViewSet
from apps.finance.views import AccountViewSet, CashView, DrawerCloseViewSet, MoneyMoveViewSet
from apps.gyms.views import BranchViewSet, GymSettingsView, StaffViewSet, SupportAccessViewSet
from apps.members.views import MemberViewSet, OfferViewSet, PaymentViewSet, PlanViewSet, RefundViewSet, SubscriptionViewSet
from apps.messages.views import (
    AutomationView, ConsoleMessageViewSet, ConsoleUsageView, GymMessagesView, GymMessageTimesView, GymMessageTimeView, GymMessageView, GymWhatsAppView, MessageViewSet,
    WhatsAppAccountViewSet, WhatsAppTemplateViewSet, WhatsAppWebhookView,
)
from apps.payroll.views import PayslipViewSet, SalaryRuleViewSet
from apps.platform.views import GymAdminViewSet, GymViewSet, JobRunNowView, PlatformSummaryView, ServerStatusView
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
router.register("billing/branch-requests", BranchRequestViewSet, basename="branch-request")
router.register("billing/invoices", InvoiceViewSet, basename="rackline-invoice")
# Rackline's own side (the Console): no X-Gym, Rackline admins only.
router.register("platform/gyms", GymViewSet, basename="platform-gym")
router.register(r"platform/gyms/(?P<gym_id>\d+)/admins", GymAdminViewSet, basename="platform-gym-admin")
router.register("platform/prices", PriceListViewSet, basename="platform-price-list")
router.register("platform/branch-requests", ConsoleBranchRequestViewSet, basename="platform-branch-request")
router.register("platform/invoices", ConsoleInvoiceViewSet, basename="platform-invoice")
router.register("platform/invoice-payments", ConsoleInvoicePaymentViewSet, basename="platform-invoice-payment")
router.register("platform/charges", ChargeViewSet, basename="platform-charge")
router.register("platform/whatsapp-accounts", WhatsAppAccountViewSet, basename="platform-whatsapp-account")
router.register("platform/whatsapp-templates", WhatsAppTemplateViewSet, basename="platform-whatsapp-template")
router.register("platform/messages", ConsoleMessageViewSet, basename="platform-message")

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
    path("api/gym/whatsapp/", GymWhatsAppView.as_view(), name="gym-whatsapp"),
    path("api/gym/messages/", GymMessagesView.as_view(), name="gym-messages"),
    path("api/gym/messages/<slug:kind>/", GymMessageView.as_view(), name="gym-message"),
    path("api/whatsapp/webhook/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),  # Rackline's shared number
    path("api/whatsapp/webhook/<slug:slug>/", WhatsAppWebhookView.as_view(), name="whatsapp-webhook-own"),  # a gym's own
    path("api/cash/", CashView.as_view(), name="cash"),
    path("api/billing/plan/", RacklinePlanView.as_view(), name="rackline-plan"),
    path("api/platform/gyms/<int:gym_id>/plan/", GymPlanView.as_view(), name="platform-gym-plan"),
    path("api/platform/gyms/<int:gym_id>/plan/current-prices/", GymPlanPricesView.as_view(), name="platform-gym-plan-prices"),
    path("api/platform/gyms/<int:gym_id>/messages/", GymMessageTimesView.as_view(), name="platform-gym-messages"),
    path("api/platform/gyms/<int:gym_id>/messages/<slug:kind>/", GymMessageTimeView.as_view(), name="platform-gym-message"),
    path("api/platform/automation/", AutomationView.as_view(), name="platform-automation"),
    path("api/platform/whatsapp-usage/", ConsoleUsageView.as_view(), name="platform-whatsapp-usage"),
    path("api/platform/summary/", PlatformSummaryView.as_view(), name="platform-summary"),
    path("api/platform/status/", ServerStatusView.as_view(), name="platform-status"),
    path("api/platform/jobs/<slug:job>/run/", JobRunNowView.as_view(), name="platform-job-run"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
