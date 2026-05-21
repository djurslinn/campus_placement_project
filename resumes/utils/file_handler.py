"""
File handling utilities for resume upload and processing
"""
import os
import re
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from werkzeug.utils import secure_filename as werkzeug_secure_filename
import PyPDF2
import pdfplumber


MAX_FILE_SIZE_MB = 5
ALLOWED_EXTENSIONS = ['pdf']


def validate_pdf_file(file: UploadedFile) -> tuple[bool, str]:
    """
    Validate uploaded PDF file
    
    Args:
        file: Django UploadedFile object
    
    Returns:
        (is_valid, error_message): tuple
    """
    # Check if file exists
    if not file:
        return False, "No file provided"
    
    # Check file size (5MB max)
    max_size = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
    if file.size > max_size:
        return False, f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
    
    # Check file extension
    ext = file.name.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Only PDF files are allowed"
    
    # Check content type
    if not file.content_type or 'pdf' not in file.content_type.lower():
        return False, "Invalid file type. Only PDF files are accepted"
    
    return True, ""


def secure_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    return werkzeug_secure_filename(filename)


def extract_text_from_pdf(filepath: str) -> str:
    """
    Extract text content from PDF file
    
    Args:
        filepath: Path to PDF file
    
    Returns:
        Extracted text as string
    """
    text = ""
    
    try:
        # Try using pdfplumber first (better extraction)
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                # x_tolerance=1 helps with character spacing issues
                page_text = page.extract_text(x_tolerance=1)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
        # Fallback to PyPDF2
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as pdf_error:
            print(f"PyPDF2 extraction failed: {pdf_error}")
            return ""
    
    # Clean up text
    # Remove excessive newlines and spaces
    text = re.sub(r'\n\s*\n', '\n\n', text)  # normalize paragraph breaks
    text = re.sub(r'[ \t]+', ' ', text)      # normalize horizontal whitespace
    
    return text.strip()


def delete_resume_file(resume):
    """
    Safely delete resume file from filesystem
    
    Args:
        resume: Resume model instance
    
    Returns:
        bool: True if file was deleted, False otherwise
    """
    if not resume.file:
        return False
    
    try:
        file_path = resume.file.path
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False
    
    return False


def get_file_size_mb(file) -> float:
    """
    Get file size in megabytes
    
    Args:
        file: File object
    
    Returns:
        Size in MB
    """
    if hasattr(file, 'size'):
        return file.size / (1024 * 1024)
    return 0.0
