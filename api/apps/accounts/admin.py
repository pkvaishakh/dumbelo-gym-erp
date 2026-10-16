from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "is_active", "is_staff"]
    search_fields = ["name", "email", "phone"]
