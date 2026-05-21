from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_gd_sessions, name='manage_gd_sessions'),
    path('create/', views.create_gd_session, name='create_gd_session'),
    path('session/<int:session_id>/', views.view_gd_session, name='view_gd_session'),
    path('session/<int:session_id>/delete/', views.delete_gd_session, name='delete_gd_session'),
    path('my-gd/', views.student_gd_sessions, name='student_gd_sessions'),
]
