"""
Resume builder view for AI-powered resume creation
"""
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import Resume
from ..forms import (
    PersonalInfoForm, SummaryForm, SkillsForm,
    EducationFormSet, ExperienceFormSet, ProjectFormSet,
    CertificationFormSet, LanguageFormSet, AchievementFormSet
)
from ..utils.pdf_generator import generate_resume_pdf
import json
import os
from django.conf import settings


class ResumeBuilderView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Multi-step resume builder with formsets
    """
    template_name = 'resumes/builder.html'
    
    def test_func(self):
        return self.request.user.role == 'student'
    
    def get(self, request):
        # Check enforcement
        if hasattr(request.user, 'resume'):
            messages.warning(
                request,
                'You already have a resume. Please download and delete it before creating a new one.'
            )
            return redirect('resumes:dashboard')
        
        # Initialize forms
        context = {
            'personal_form': PersonalInfoForm(),
            'summary_form': SummaryForm(),
            'skills_form': SkillsForm(),
            'education_formset': EducationFormSet(prefix='education'),
            'experience_formset': ExperienceFormSet(prefix='experience'),
            'project_formset': ProjectFormSet(prefix='project'),
            'certification_formset': CertificationFormSet(prefix='certification'),
            'language_formset': LanguageFormSet(prefix='language'),
            'achievement_formset': AchievementFormSet(prefix='achievement'),
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        # Check enforcement
        if hasattr(request.user, 'resume'):
            messages.error(request, 'You already have a resume.')
            return redirect('resumes:dashboard')
        
        # Bind forms with POST data
        personal_form = PersonalInfoForm(request.POST)
        summary_form = SummaryForm(request.POST)
        skills_form = SkillsForm(request.POST)
        education_formset = EducationFormSet(request.POST, prefix='education')
        experience_formset = ExperienceFormSet(request.POST, prefix='experience')
        project_formset = ProjectFormSet(request.POST, prefix='project')
        certification_formset = CertificationFormSet(request.POST, prefix='certification')
        language_formset = LanguageFormSet(request.POST, prefix='language')
        achievement_formset = AchievementFormSet(request.POST, prefix='achievement')
        
        # Validate all forms
        if (personal_form.is_valid() and summary_form.is_valid() and
            skills_form.is_valid() and education_formset.is_valid() and
            experience_formset.is_valid() and project_formset.is_valid() and
            certification_formset.is_valid() and language_formset.is_valid() and
            achievement_formset.is_valid()):
            
            try:
                # Prepare data
                personal_data = personal_form.cleaned_data
                summary_data = summary_form.cleaned_data
                skills_data = skills_form.cleaned_data
                
                # Process formsets into JSON
                education_list = []
                for form in education_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        education_list.append(form.cleaned_data)
                
                experience_list = []
                for form in experience_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        experience_list.append(form.cleaned_data)
                
                project_list = []
                for form in project_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        project_list.append(form.cleaned_data)
                
                certification_list = []
                for form in certification_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        certification_list.append(form.cleaned_data)
                
                language_list = []
                for form in language_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        language_list.append(form.cleaned_data)
                
                achievement_list = []
                for form in achievement_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        achievement_list.append(form.cleaned_data)
                
                # Create skills JSON
                skills_json = {
                    'technical': skills_data.get('technical_skills', ''),
                    'soft': skills_data.get('soft_skills', ''),
                    'tools': skills_data.get('tools', '')
                }
                
                # Create Resume object
                resume = Resume.objects.create(
                    student=request.user,
                    resume_type='generated',
                    full_name=personal_data['full_name'],
                    email=personal_data['email'],
                    phone=personal_data['phone'],
                    linkedin=personal_data.get('linkedin', ''),
                    github=personal_data.get('github', ''),
                    portfolio=personal_data.get('portfolio', ''),
                    address=personal_data.get('address', ''),
                    summary=summary_data['summary'],
                    education_json=education_list,
                    experience_json=experience_list,
                    projects_json=project_list,
                    skills_json=skills_json,
                    certifications_json=certification_list,
                    languages_json=language_list,
                    achievements_json=achievement_list,
                )
                
                # Generate PDF
                try:
                    pdf_path = generate_resume_pdf(resume)
                    # Store relative path in database with forward slashes for Django/URL compatibility
                    rel_path = os.path.relpath(pdf_path, settings.MEDIA_ROOT).replace('\\', '/')
                    resume.file.name = rel_path
                    
                    # Extract text for ATS analysis consistency
                    from ..utils.file_handler import extract_text_from_pdf
                    try:
                        # generate_resume_pdf returns absolute path which extract_text_from_pdf needs
                        resume.extracted_text = extract_text_from_pdf(pdf_path)
                    except Exception as ext_e:
                        print(f"Error extracting text from generated PDF: {ext_e}")
                        
                    resume.save()
                    messages.success(request, 'Resume created and PDF generated successfully!')
                except Exception as e:
                    print(f"Error generating PDF: {e}")
                    messages.success(request, 'Resume data saved, but PDF generation failed. You can try editing and saving again.')
                    messages.warning(request, f"PDF Error: {str(e)}")
                
                return redirect('resumes:dashboard')
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error creating resume record: {str(e)}')
        else:
            # Add a message to inform the user about validation errors
            messages.error(request, 'Please correct the errors in the form below.')
        
        # If validation fails, show errors
        context = {
            'personal_form': personal_form,
            'summary_form': summary_form,
            'skills_form': skills_form,
            'education_formset': education_formset,
            'experience_formset': experience_formset,
            'project_formset': project_formset,
            'certification_formset': certification_formset,
            'language_formset': language_formset,
            'achievement_formset': achievement_formset,
        }
        
        return render(request, self.template_name, context)
