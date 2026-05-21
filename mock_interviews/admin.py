from django.contrib import admin
from .models import MockInterviewSession, MockInterviewPair, MockInterviewEvaluation


class MockInterviewPairInline(admin.TabularInline):
    model  = MockInterviewPair
    extra  = 0
    readonly_fields = ('student1', 'student2', 'student3')


class MockInterviewEvaluationInline(admin.TabularInline):
    model  = MockInterviewEvaluation
    extra  = 0
    readonly_fields = ('evaluator', 'evaluatee', 'submitted_at',
                       'communication', 'confidence', 'technical',
                       'body_language', 'problem_solving', 'feedback')


@admin.register(MockInterviewSession)
class MockInterviewSessionAdmin(admin.ModelAdmin):
    list_display  = ('id', 'label', 'created_by', 'status', 'created_at',
                     'total_pairs', 'submissions_count', 'completion_pct')
    list_filter   = ('status',)
    inlines       = [MockInterviewPairInline, MockInterviewEvaluationInline]


@admin.register(MockInterviewPair)
class MockInterviewPairAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'student1', 'student2', 'student3')


@admin.register(MockInterviewEvaluation)
class MockInterviewEvaluationAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'evaluator', 'evaluatee',
                    'average_score', 'performance_level', 'submitted_at')
    list_filter  = ('session',)
