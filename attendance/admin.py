from django.contrib import admin
from .models import physicalSession, Attendance

@admin.register(physicalSession)
class physicalSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'coordinator')
    list_filter = ('date', 'coordinator')
    search_fields = ('title', 'description')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'is_present', 'marked_at')
    list_filter = ('session', 'is_present')
    search_fields = ('student__email', 'session__title')
