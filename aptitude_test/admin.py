from django.contrib import admin
from .models import PDFTest, PDFTestResult

@admin.register(PDFTest)
class PDFTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'total_questions', 'duration_minutes', 'created_at', 'created_by')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

@admin.register(PDFTestResult)
class PDFTestResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'score', 'percentage', 'submitted_at')
    list_filter = ('test', 'submitted_at')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'student__roll_no')
