from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('manage/', views.manage_sessions, name='manage_sessions'),
    path('delete/<int:session_id>/', views.delete_session, name='delete_session'),
    path('mark/<int:session_id>/', views.mark_attendance, name='mark_attendance'),
    path('performance/', views.performance_dashboard, name='performance_dashboard'),
    path('activity/', views.activity_log, name='activity_log'),
]
