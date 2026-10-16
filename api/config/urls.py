from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from apps.accounts.views import LoginView, LogoutView, MeView, RefreshView
from apps.attendance.views import CheckInViewSet, DevicePunchView, DeviceViewSet, QRCheckInView
from apps.expenses.views import ExpenseViewSet
from apps.gyms.views import BranchViewSet, GymSettingsView, StaffViewSet, SupportAccessViewSet
from apps.members.views import MemberViewSet, OfferViewSet, PaymentViewSet, PlanViewSet, SubscriptionViewSet
from apps.messages.views import MessageViewSet
from apps.reports.views import SummaryView
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
router.register("checkins", CheckInViewSet, basename="checkin")
router.register("devices", DeviceViewSet, basename="device")
router.register("tasks", TaskViewSet, basename="task")
router.register("expenses", ExpenseViewSet, basename="expense")
router.register("messages", MessageViewSet, basename="message")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/refresh/", RefreshView.as_view(), name="refresh"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/me/", MeView.as_view(), name="me"),
    path("api/checkins/qr/", QRCheckInView.as_view(), name="qr-checkin"),
    path("api/devices/punch/", DevicePunchView.as_view(), name="device-punch"),  # before the router: never shadowed by devices/<pk>/
    path("api/reports/summary/", SummaryView.as_view(), name="summary"),
    path("api/gym/settings/", GymSettingsView.as_view(), name="gym-settings"),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
