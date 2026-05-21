from django.contrib import admin
from .models import GDTopic, GDSession, GDGroup, GDGroupMember

@admin.register(GDTopic)
class GDTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)

@admin.register(GDSession)
class GDSessionAdmin(admin.ModelAdmin):
    list_display = ('topic', 'custom_topic', 'coordinator', 'num_groups', 'scheduled_at')
    list_filter = ('coordinator', 'scheduled_at')

class GDGroupMemberInline(admin.TabularInline):
    model = GDGroupMember
    extra = 1

@admin.register(GDGroup)
class GDGroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'session')
    inlines = [GDGroupMemberInline]

@admin.register(GDGroupMember)
class GDGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'score')
    list_filter = ('group__session', 'score')
