from django.urls import path
from .views import (
    ResumeDashboardView, 
    ResumeUploadView, 
    DownloadResumeView,
    ViewResumeView,
    DeleteResumeView,
    ResumeBuilderView, 
    ResumeAnalysisView
)

app_name = 'resumes'

urlpatterns = [
    # Dashboard
    path('', ResumeDashboardView.as_view(), name='dashboard'),
    
    # Upload and management
    path('upload/', ResumeUploadView.as_view(), name='upload'),
    path('download/', DownloadResumeView.as_view(), name='download'),
    path('view/', ViewResumeView.as_view(), name='view'),
    path('delete/', DeleteResumeView.as_view(), name='delete'),
    
    # Builder
    path('builder/', ResumeBuilderView.as_view(), name='builder'),
    
    # ATS Analysis
    path('analysis/', ResumeAnalysisView.as_view(), name='analysis'),
]
