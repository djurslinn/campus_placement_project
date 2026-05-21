from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from ..models import Resume
from ..services.pdf_generator import generate_resume_pdf
import os


@login_required
def generate_pdf(request, resume_id):
    """
    Generate PDF from AI-generated resume content.
    Students can only generate PDFs for their own resumes.
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    # Security check: ensure student can only generate PDF for their own resume
    if resume.student != request.user:
        raise PermissionDenied("You don't have permission to access this resume.")
    
    # Only allow PDF generation for AI-generated resumes
    if resume.resume_type != 'generated':
        messages.error(request, 'PDF generation is only available for AI-generated resumes.')
        return redirect('resumes:my_resumes')
    
    try:
        # Generate PDF
        pdf_path = generate_resume_pdf(resume)
        
        # Update resume with PDF file path
        resume.file = pdf_path
        resume.save()
        
        messages.success(request, 'PDF generated successfully! You can now download it.')
        return redirect('resumes:preview', resume_id=resume.id)
        
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('resumes:preview', resume_id=resume.id)


@login_required
def download_pdf(request, resume_id):
    """
    Download resume PDF.
    Students can only download their own resumes.
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    # Security check: ensure student can only download their own resume
    if resume.student != request.user:
        raise PermissionDenied("You don't have permission to access this resume.")
    
    # Check if file exists
    if not resume.file:
        messages.error(request, 'No PDF file available for this resume.')
        return redirect('resumes:my_resumes')
    
    # Check if file physically exists
    if not os.path.exists(resume.file.path):
        messages.error(request, 'PDF file not found.')
        return redirect('resumes:my_resumes')
    
    try:
        # Prepare file for download
        file_handle = resume.file.open('rb')
        response = FileResponse(file_handle, content_type='application/pdf')
        
        # Set filename for download
        filename = f"{resume.student.username}_resume_{resume.id}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('resumes:my_resumes')
