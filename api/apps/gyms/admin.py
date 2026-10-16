from django.contrib import admin

from .models import Branch, BranchSession, Gym, GymRole, SupportAccess


class SessionInline(admin.TabularInline):
    model = BranchSession
    extra = 0


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "status", "created_at"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ["name", "gym", "is_active"]
    list_filter = ["gym"]
    inlines = [SessionInline]


@admin.register(GymRole)
class GymRoleAdmin(admin.ModelAdmin):
    list_display = ["user", "gym", "role", "is_owner", "is_active"]
    list_filter = ["gym", "role"]


admin.site.register(SupportAccess)
