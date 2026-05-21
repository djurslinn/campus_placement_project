"""
Views package
"""
from .dashboard import ResumeDashboardView
from .upload import ResumeUploadView, DownloadResumeView, ViewResumeView, DeleteResumeView
from .builder import ResumeBuilderView
from .analyzer import ResumeAnalysisView

__all__ = [
    'ResumeDashboardView',
    'ResumeUploadView',
    'DownloadResumeView',
    'ViewResumeView',
    'DeleteResumeView',
    'ResumeBuilderView',
    'ResumeAnalysisView',
]
