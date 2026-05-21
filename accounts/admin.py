"""
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model
    """
    list_display = ['email', 'username', 'role', 'department', 'is_staff']
    list_filter = ['role', 'department', 'is_staff', 'is_active']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'department')}),
    )

