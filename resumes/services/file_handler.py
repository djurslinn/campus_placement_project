"""
File handling utilities for resume uploads.
Handles PDF validation and text extraction.
"""

import os
import logging

logger = logging.getLogger(__name__)


def validate_pdf_file(uploaded_file):
    """
    Validate uploaded PDF file.
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check file extension
    file_name = uploaded_file.name.lower()
    if not file_name.endswith('.pdf'):
        return False, 'Only PDF files are allowed.'
    
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if uploaded_file.size > max_size:
        return False, 'File size must not exceed 5MB.'
    
    # Check if file is empty
    if uploaded_file.size == 0:
        return False, 'File is empty.'
    
    # Check content type
    content_type = uploaded_file.content_type
    if content_type and content_type not in ['application/pdf']:
        return False, 'Invalid file type. Only PDF files are accepted.'
    
    return True, None


def extract_text_from_pdf(file_path):
    """
    Extract text content from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        import pdfplumber
        
        text_content = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        full_text = '\n\n'.join(text_content)
        
        # Clean up extracted text
        full_text = _clean_extracted_text(full_text)
        
        return full_text
        
    except ImportError:
        logger.error("pdfplumber not installed. Install with: pip install pdfplumber")
        return _fallback_text_extraction(file_path)
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        return f"Error extracting text: {str(e)}"


def _clean_extracted_text(text):
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    # Remove excessive whitespace
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    
    # Join lines
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Remove excessive newlines
    while '\n\n\n' in cleaned_text:
        cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
    
    return cleaned_text


def _fallback_text_extraction(file_path):
    """
    Fallback text extraction using PyPDF2 if pdfplumber is not available.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        str: Extracted text or error message
    """
    try:
        import PyPDF2
        
        text_content = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        full_text = '\n\n'.join(text_content)
        return _clean_extracted_text(full_text)
        
    except ImportError:
        error_msg = "PDF text extraction libraries not installed. Please install pdfplumber: pip install pdfplumber"
        logger.error(error_msg)
        return error_msg
        
    except Exception as e:
        logger.error(f"Fallback PDF extraction failed: {e}")
        return f"Unable to extract text from PDF: {str(e)}"


def get_file_size_mb(file_path):
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        float: File size in MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_mb = size_bytes / (1024 * 1024)
        return round(size_mb, 2)
    except Exception:
        return 0.0


def delete_file_safe(file_path):
    """
    Safely delete a file if it exists.
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        bool: True if deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False
