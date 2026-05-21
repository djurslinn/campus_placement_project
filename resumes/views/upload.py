"""
Resume upload and management views
"""
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse, Http404
from ..models import Resume
from ..forms import ResumeUploadForm
from ..utils.file_handler import validate_pdf_file, extract_text_from_pdf, secure_filename


class ResumeUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Handle resume upload with single-resume enforcement
    """
    template_name = 'resumes/upload.html'
    
    def test_func(self):
        return self.request.user.role == 'student'
    
    def get(self, request):
        # Check if user already has a resume
        if hasattr(request.user, 'resume'):
            messages.warning(
                request,
                'You already have a resume. Please download and delete it before uploading a new one.'
            )
            return redirect('resumes:dashboard')
        
        form = ResumeUploadForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        # Check enforcement
        if hasattr(request.user, 'resume'):
            messages.error(request, 'You already have a resume.')
            return redirect('resumes:dashboard')
        
        form = ResumeUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            uploaded_file = form.cleaned_data['resume_file']
            
            # Additional validation
            is_valid, error_message = validate_pdf_file(uploaded_file)
            if not is_valid:
                messages.error(request, error_message)
                return render(request, self.template_name, {'form': form})
            
            try:
                # Create resume object
                resume = Resume.objects.create(
                    student=request.user,
                    resume_type='uploaded',
                    file=uploaded_file
                )
                
                # Extract text from PDF
                if resume.file:
                    extracted_text = extract_text_from_pdf(resume.file.path)
                    resume.extracted_text = extracted_text
                    resume.save()
                
                messages.success(request, 'Resume uploaded successfully!')
                return redirect('resumes:dashboard')
                
            except Exception as e:
                messages.error(request, f'Error uploading resume: {str(e)}')
                return render(request, self.template_name, {'form': form})
        
        return render(request, self.template_name, {'form': form})


class DownloadResumeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Download student's resume
    """
    def test_func(self):
        return self.request.user.role == 'student'
    
    def get(self, request):
        if not hasattr(request.user, 'resume'):
            raise Http404("No resume found")
        
        resume = request.user.resume
        
        if not resume.file:
            messages.error(request, "No file available for download")
            return redirect('resumes:dashboard')
        
        try:
            response = FileResponse(
                open(resume.file.path, 'rb'),
                content_type='application/pdf'
            )
            filename = resume.get_filename() or 'resume.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except FileNotFoundError:
            messages.error(request, "Resume file not found")
            return redirect('resumes:dashboard')


class ViewResumeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View student's resume in browser
    """
    def test_func(self):
        return self.request.user.role == 'student'
    
    def get(self, request):
        if not hasattr(request.user, 'resume'):
            raise Http404("No resume found")
        
        resume = request.user.resume
        
        if not resume.file:
            messages.error(request, "No file available to view")
            return redirect('resumes:dashboard')
        
        try:
            response = FileResponse(
                open(resume.file.path, 'rb'),
                content_type='application/pdf'
            )
            filename = resume.get_filename() or 'resume.pdf'
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        except FileNotFoundError:
            messages.error(request, "Resume file not found")
            return redirect('resumes:dashboard')


class DeleteResumeView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Delete student's resume (POST only)
    """
    def test_func(self):
        return self.request.user.role == 'student'
    
    def post(self, request):
        if not hasattr(request.user, 'resume'):
            messages.error(request, "No resume to delete")
            return redirect('resumes:dashboard')
        
        resume = request.user.resume
        
        try:
            # Delete will automatically remove the file (overridden in model)
            resume.delete()
            messages.success(request, 'Resume deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting resume: {str(e)}')
        
        return redirect('resumes:dashboard')
