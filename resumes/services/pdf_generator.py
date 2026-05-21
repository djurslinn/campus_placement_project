"""
PDF generation service for creating resume PDFs from structured data.
Optimized for xhtml2pdf (pisa) for maximum compatibility on Windows environments,
while maintaining support for professional HTML/CSS templates.
"""

import os
import logging
from datetime import datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.text import slugify

logger = logging.getLogger(__name__)

def generate_resume_pdf(resume):
    """
    Generate PDF from structured resume data using the HTML template.
    Uses xhtml2pdf for reliable Windows compatibility.
    """
    try:
        from xhtml2pdf import pisa
        
        # Create directory if it doesn't exist
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'resumes', 'generated', str(resume.student.id))
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = slugify(resume.full_name or resume.student.username)
        filename = f"resume_{safe_name}_{timestamp}.pdf"
        file_path = os.path.join(pdf_dir, filename)
        
        # Prepare context for template
        # Note: mapping JSON fields to context variables
        context = {
            'full_name': resume.full_name or resume.student.get_full_name() or resume.student.username,
            'email': resume.email or resume.student.email,
            'phone': resume.phone,
            'address': resume.address,
            'linkedin': resume.linkedin,
            'github': resume.github,
            'portfolio': resume.portfolio,
            'summary': resume.summary,
            'education': resume.education_json,
            'experience': resume.experience_json,
            'projects': resume.projects_json,
            'skills': resume.skills_json,
            'certifications': resume.certifications_json,
            'languages': resume.languages_json,
            'achievements': resume.achievements_json,
        }
        
        # Render HTML
        html_string = render_to_string('resumes/pdf_template.html', context)
        
        # Generate PDF using xhtml2pdf
        with open(file_path, 'wb') as pdf_file:
            pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)
            
        if pisa_status.err:
            logger.error(f"xhtml2pdf error: {pisa_status.err}")
            return _reportlab_fallback(resume)
            
        # Return absolute path (builder.py seems to expect absolute path)
        return file_path
        
    except ImportError:
        logger.error("xhtml2pdf not installed.")
        return _reportlab_fallback(resume)
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return _reportlab_fallback(resume)

def _reportlab_fallback(resume):
    """Last resort: simple reportlab generation"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        pdf_dir = os.path.join(settings.MEDIA_ROOT, 'resumes', 'generated', str(resume.student.id))
        os.makedirs(pdf_dir, exist_ok=True)
        filename = f"resume_{resume.id}_simple.pdf"
        file_path = os.path.join(pdf_dir, filename)
        
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        story.append(Paragraph(resume.full_name or resume.student.username, styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(resume.summary or "Resume Summary", styles['Normal']))
        
        doc.build(story)
        return file_path
    except Exception:
        return None
