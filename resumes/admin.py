from django.contrib import admin
from .models import Resume, ATSScore


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['student', 'resume_type', 'get_filename', 'created_at']
    list_filter = ['resume_type', 'created_at']
    search_fields = ['student__username', 'student__email', 'full_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'resume_type')
        }),
        ('Uploaded Resume', {
            'fields': ('file', 'extracted_text'),
            'classes': ('collapse',)
        }),
        ('AI Generated Resume Data', {
            'fields': ('full_name', 'email', 'phone', 'linkedin', 'github', 'portfolio', 'address', 'summary', 
                      'education_json', 'experience_json', 'projects_json', 'skills_json', 
                      'certifications_json', 'languages_json', 'achievements_json', 'ai_generated_content', 'ai_enhanced'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_filename(self, obj):
        return obj.get_filename() or 'N/A'
    get_filename.short_description = 'File Name'


@admin.register(ATSScore)
class ATSScoreAdmin(admin.ModelAdmin):
    list_display = ['resume', 'score', 'get_score_category', 'analyzed_at']
    list_filter = ['score', 'analyzed_at', 'target_role']
    search_fields = ['resume__student__username', 'resume__student__email']
    readonly_fields = ['analyzed_at']
    
    fieldsets = (
        ('Resume Reference', {
            'fields': ('resume', 'target_role')
        }),
        ('Overall Score', {
            'fields': ('score', 'ai_adjustment', 'role_fit_score')
        }),
        ('Score Breakdown', {
            'fields': ('structure_score', 'keyword_score', 'skills_score', 
                      'experience_score', 'action_verb_score', 'ats_safety_score'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('missing_keywords', 'weak_sections', 'improvement_suggestions', 'analysis_data'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('analyzed_at',)
        }),
    )
    
    def get_score_category(self, obj):
        return obj.get_score_category()
    get_score_category.short_description = 'Category'
