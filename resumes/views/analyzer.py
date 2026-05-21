"""
ATS analysis view using the new AI-powered microservice
"""
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Resume, ATSScore
from ..utils.ats_client import sync_analyze_resume


class ResumeAnalysisView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    ATS analysis view - analyze resume and show results using FastAPI microservice
    """
    template_name = 'resumes/analysis.html'
    
    def test_func(self):
        return self.request.user.role == 'student'
    
    def get(self, request):
        if not hasattr(request.user, 'resume'):
            messages.error(request, 'No resume found for analysis')
            return redirect('resumes:dashboard')
        
        resume = request.user.resume
        
        # Check if analysis exists
        if hasattr(resume, 'ats_score'):
            ats_score = resume.ats_score
            
            # Map ATSScore model to analysis context
            analysis_data = ats_score.analysis_data or {}
            
            analysis_summary = {
                'overall_score': ats_score.score,
                'category': ats_score.get_score_category(),
                'color': ats_score.get_score_color(),
                'breakdown': {
                    'Semantic Keyword Match': ats_score.keyword_score,
                    'Skills Alignment': ats_score.skills_score,
                    'Experience Detection': ats_score.experience_score,
                    'Education Check': getattr(ats_score, 'education_score', ats_score.experience_score),
                },
                'missing_keywords': ats_score.missing_keywords,
                'weak_sections': ats_score.weak_sections,
                'suggestions': ats_score.improvement_suggestions,
                'target_role': ats_score.target_role or 'General',
                'sections_found': analysis_data.get('sections_found', {}),
                'discovered_details': analysis_data.get('discovered_details', {}),
                'matched_skills': analysis_data.get('matched_skills', []),
            }
            
            context = {
                'resume': resume,
                'ats_score': ats_score,
                'analysis': analysis_summary,
            }
            
            return render(request, self.template_name, context)
        else:
            messages.info(request, 'No analysis found. Click "Analyze" to generate ATS score.')
            return redirect('resumes:dashboard')
    
    def post(self, request):
        if not hasattr(request.user, 'resume'):
            messages.error(request, 'No resume found')
            return redirect('resumes:dashboard')
        
        resume = request.user.resume
        
        # Get target role or job description from form
        target_role = request.POST.get('target_role', 'General Software Engineer')
        job_description = request.POST.get('job_description', target_role) # Use full JD if available
        
        try:
            # Run analysis using the microservice
            result = sync_analyze_resume(resume, job_description)
            
            if not result:
                messages.error(request, 'ATS Analysis service is unavailable. Please check if the microservice is running.')
                return redirect('resumes:dashboard')
            
            # Create or update ATSScore model
            ats_score, created = ATSScore.objects.update_or_create(
                resume=resume,
                defaults={
                    'score': result['ats_score'],
                    'keyword_score': result['keyword_score'],
                    'skills_score': result['skills_score'],
                    'experience_score': result['experience_score'],
                    'education_score': result['education_score'],
                    'missing_keywords': result['missing_skills'],
                    'weak_sections': [s for s, found in result.get('sections_found', {}).items() if not found],
                    'improvement_suggestions': result['suggestions'],
                    'target_role': target_role,
                    'analysis_data': result # Storing full result for future use
                }
            )
            
            messages.success(request, 'AI-powered ATS analysis completed successfully!')
            
        except Exception as e:
            messages.error(request, f'Error analyzing resume: {str(e)}')
            return redirect('resumes:dashboard')
        
        return redirect('resumes:analysis')
