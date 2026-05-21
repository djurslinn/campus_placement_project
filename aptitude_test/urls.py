from django.urls import path
from . import views

urlpatterns = [
    # Coordinator URLs
    path('manage/', views.manage_pdf_tests, name='manage_pdf_tests'),
    path('create/', views.create_pdf_test, name='create_pdf_test'),
    path('edit/<int:test_id>/', views.edit_pdf_test, name='edit_pdf_test'),
    path('delete/<int:test_id>/', views.delete_pdf_test, name='delete_pdf_test'),
    path('results/<int:test_id>/', views.view_test_results, name='view_test_results'),
    path('eligible/<int:test_id>/', views.view_eligible_students, name='view_eligible_students'),
    path('toggle-visibility/<int:test_id>/', views.toggle_test_visibility, name='toggle_test_visibility'),
    path('reset-results/<int:test_id>/', views.reset_test_results, name='reset_test_results'),
    
    # Student URLs
    path('tests/', views.student_pdf_tests, name='student_pdf_tests'),
    path('take/<int:test_id>/', views.take_pdf_test, name='take_pdf_test'),
]
