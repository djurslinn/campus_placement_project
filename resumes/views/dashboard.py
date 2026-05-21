"""
Resume dashboard view - main entry point for resume management
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from ..models import Resume, ATSScore


class ResumeDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Main resume dashboard showing current resume status and options
    """
    template_name = 'resumes/dashboard.html'
    
    def test_func(self):
        """Only students can access"""
        return self.request.user.role == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has a resume
        has_resume = hasattr(self.request.user, 'resume')
        context['has_resume'] = has_resume
        
        if has_resume:
            resume = self.request.user.resume
            context['resume'] = resume
            
            # Get ATS score if exists
            if hasattr(resume, 'ats_score'):
                context['ats_score'] = resume.ats_score
            else:
                context['ats_score'] = None
            
            # Prevent new creation
            context['can_upload'] = False
            context['can_build'] = False
        else:
            context['resume'] = None
            context['ats_score'] = None
            context['can_upload'] = True
            context['can_build'] = True
        
        return context
