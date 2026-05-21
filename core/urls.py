from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('logout/', views.user_logout, name='logout'),
    path('sys-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('sys-admin/users/', views.admin_user_management, name='admin_user_management'),
    path('sys-admin/users/toggle/<int:user_id>/', views.admin_toggle_user_status, name='admin_toggle_user_status'),
    path('sys-admin/security/', views.security_overview, name='security_overview'),
    path('sys-admin/courses/', views.admin_manage_courses, name='admin_manage_courses'),
    path('coordinator/dashboard/', views.coordinator_dashboard, name='coordinator_dashboard'),
    
    # Manage Students
    path('coordinator/students/', views.manage_students, name='manage_students'),
    path('coordinator/students/approve/<int:student_id>/', views.approve_student, name='approve_student'),
    path('coordinator/students/toggle/<int:student_id>/', views.toggle_student_status, name='toggle_student_status'),
    path('coordinator/students/mark-placed/<int:student_id>/', views.mark_student_placed, name='mark_student_placed'),
    path('coordinator/students/view/<int:student_id>/', views.view_student_detail, name='view_student_detail'),
    path('coordinator/students/notify/<int:student_id>/', views.send_personal_notification, name='send_personal_notification'),
    
    # Manage Drives
    path('coordinator/drives/', views.manage_drives, name='manage_drives'),
    path('coordinator/drives/create/', views.create_drive, name='create_drive'),
    path('coordinator/drives/edit/<int:drive_id>/', views.edit_drive, name='edit_drive'),
    path('coordinator/drives/delete/<int:drive_id>/', views.delete_drive, name='delete_drive'),
    path('coordinator/drives/view/<int:drive_id>/', views.view_drive_students, name='view_drive_students'),
    
    # Reports
    path('coordinator/reports/', views.reports, name='reports'),
    path('coordinator/reports/export/', views.export_reports_csv, name='export_reports_csv'),
    
    # Notifications
    path('coordinator/notifications/', views.notifications, name='notifications'),

    # Manage Courses
    path('coordinator/courses/', views.manage_courses, name='manage_courses'),
    path('coordinator/courses/create/', views.create_course, name='create_course'),
    path('coordinator/courses/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('coordinator/courses/delete/<int:course_id>/', views.delete_course, name='delete_course'),

    # --- Student Module URLs ---
    # Aptitude Tests
    path('student/tests/', views.student_aptitude_tests, name='student_aptitude_tests'),
    path('student/tests/take/<int:test_id>/', views.take_test, name='take_test'),
    
    # Mock Interviews
    path('student/interviews/', views.student_mock_interviews, name='student_mock_interviews'),
    
    path('coordinator/drives/mark-placed-bulk/<int:drive_id>/', views.mark_students_placed_bulk, name='mark_students_placed_bulk'),
    
    # Placement Drives
    path('student/drives/', views.student_placement_drives, name='student_placement_drives'),
    path('student/drives/apply/<int:drive_id>/', views.apply_drive, name='apply_drive'),
    path('student/drives/withdraw/<int:drive_id>/', views.withdraw_application, name='withdraw_application'),
    path('student/drives/ready-to-work/<int:application_id>/', views.select_ready_to_work, name='select_ready_to_work'),
    
    # Notifications
    path('student/notifications/', views.student_notifications, name='student_notifications'),
]
