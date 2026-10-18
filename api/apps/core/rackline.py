"""Rackline's own side of the API (`/api/platform/`): gyms, their admin accounts and, later, prices and invoices.

No X-Gym here: these views work across gyms, so only Rackline admins (`is_superuser`) may call them. Rackline
support (`is_staff` alone) can't: it only ever reads inside a gym, through a window the gym's admin grants.
"""
from rest_framework import permissions


def is_rackline_admin(user) -> bool:
    return bool(user and user.is_authenticated and user.is_active and user.is_superuser)


class IsRacklineAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_rackline_admin(request.user)


class RacklineViewMixin:
    """Base for the Console's views. Every action is for Rackline admins only."""

    permission_classes = [IsRacklineAdmin]
