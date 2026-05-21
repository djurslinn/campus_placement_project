"""
URL patterns for accounts app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('register/student/', views.student_register, name='student_register'),
    path('register/coordinator/', views.coordinator_register, name='coordinator_register'),
    path('verify-otp-registration/', views.verify_otp_reg, name='verify_otp_reg'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp-reset/', views.verify_otp_reset, name='verify_otp_reset'),
    path('reset-password-confirm/', views.reset_password_new, name='reset_password_new'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('coordinator/profile/', views.coordinator_profile, name='coordinator_profile'),
]

