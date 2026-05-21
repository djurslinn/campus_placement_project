from django.urls import path
from . import views

app_name = 'mock_interviews'

urlpatterns = [
    # Coordinator
    path('coordinator/',                       views.coordinator_dashboard, name='coordinator_dashboard'),
    path('coordinator/session/<int:session_id>/',  views.session_detail,    name='session_detail'),
    path('coordinator/session/<int:session_id>/delete/', views.delete_session, name='delete_session'),

    # Student
    path('student/',                           views.student_dashboard,     name='student_dashboard'),
    path('student/report/',                    views.student_report,        name='student_report'),
    path('student/evaluate/<int:session_id>/<int:evaluatee_id>/',
         views.submit_evaluation, name='submit_evaluation'),
]
