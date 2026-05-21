"""
Data masking service for protecting Personally Identifiable Information (PII).
Masks sensitive data before sending to AI services.
"""

import re
import logging

logger = logging.getLogger(__name__)


def mask_pii(text):
    """
    Mask PII (Personally Identifiable Information) in text.
    
    This function masks:
    - Email addresses
    - Phone numbers
    - Potential ID numbers
    - URLs (partially)
    
    Args:
        text: Text containing potential PII
        
    Returns:
        str: Text with PII masked
    """
    if not text:
        return text
    
    masked_text = text
    
    # Mask email addresses
    masked_text = mask_emails(masked_text)
    
    # Mask phone numbers
    masked_text = mask_phone_numbers(masked_text)
    
    # Mask potential ID numbers (like roll numbers, SSN patterns)
    masked_text = mask_id_numbers(masked_text)
    
    # Mask URLs (keep domain, mask path)
    masked_text = mask_urls(masked_text)
    
    return masked_text


def mask_emails(text):
    """
    Mask email addresses in text.
    
    Example: john.doe@example.com -> [EMAIL_MASKED]
    
    Args:
        text: Input text
        
    Returns:
        str: Text with emails masked
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    masked = re.sub(email_pattern, '[EMAIL_MASKED]', text)
    return masked


def mask_phone_numbers(text):
    """
    Mask phone numbers in text.
    
    Handles various formats:
    - (123) 456-7890
    - 123-456-7890
    - 123.456.7890
    - +1 123 456 7890
    - +91-1234567890
    
    Args:
        text: Input text
        
    Returns:
        str: Text with phone numbers masked
    """
    # Pattern for various phone number formats
    phone_patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}',  # International
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
        r'\d{10}',  # 10 consecutive digits
    ]
    
    masked = text
    for pattern in phone_patterns:
        masked = re.sub(pattern, '[PHONE_MASKED]', masked)
    
    return masked


def mask_id_numbers(text):
    """
    Mask potential ID numbers (roll numbers, student IDs, SSN, etc.).
    
    Masks patterns like:
    - Roll No: 12345
    - Student ID: ABC123
    - ID: 123-45-6789
    
    Args:
        text: Input text
        
    Returns:
        str: Text with ID numbers masked
    """
    # Pattern for common ID prefixes followed by numbers/alphanumeric
    id_patterns = [
        r'\b(?:Roll\s*No\.?|Roll\s*Number|Student\s*ID|ID\s*No\.?|Employee\s*ID)[\s:]*[A-Za-z0-9-]+\b',
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN-like pattern
        r'\b[A-Z]{2,3}\d{4,8}\b',  # Alphanumeric IDs
    ]
    
    masked = text
    for pattern in id_patterns:
        masked = re.sub(pattern, '[ID_MASKED]', masked, flags=re.IGNORECASE)
    
    return masked


def mask_urls(text):
    """
    Partially mask URLs to protect privacy while preserving context.
    
    Example: https://github.com/user/private-repo -> https://github.com/[USER]/[REPO]
    
    Args:
        text: Input text
        
    Returns:
        str: Text with URLs partially masked
    """
    url_pattern = r'https?://[^\s]+'
    
    def mask_url(match):
        url = match.group(0)
        # Keep protocol and domain, mask path
        parts = url.split('/', 3)
        if len(parts) >= 4:
            return f"{parts[0]}//{parts[2]}/[PATH_MASKED]"
        return url
    
    masked = re.sub(url_pattern, mask_url, text)
    return masked


def unmask_template_fields(text, field_values):
    """
    Replace masked placeholders with actual values.
    
    This is used when we need to restore certain masked fields
    for display or processing.
    
    Args:
        text: Text with masked values
        field_values: Dictionary mapping mask types to actual values
        
    Returns:
        str: Text with specified fields unmasked
    """
    result = text
    
    for mask_type, actual_value in field_values.items():
        result = result.replace(mask_type, actual_value)
    
    return result


def extract_unmasked_entities(original_text):
    """
    Extract PII entities from text before masking.
    
    This can be used to store PII separately in a secure manner.
    
    Args:
        original_text: Original text with PII
        
    Returns:
        dict: Dictionary containing extracted entities
    """
    entities = {
        'emails': [],
        'phones': [],
        'urls': []
    }
    
    # Extract emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    entities['emails'] = re.findall(email_pattern, original_text)
    
    # Extract phone numbers
    phone_pattern = r'\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
    entities['phones'] = re.findall(phone_pattern, original_text)
    
    # Extract URLs
    url_pattern = r'https?://[^\s]+'
    entities['urls'] = re.findall(url_pattern, original_text)
    
    return entities


def is_text_masked(text):
    """
    Check if text appears to be already masked.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text contains masking patterns
    """
    masking_patterns = [
        r'\[EMAIL_MASKED\]',
        r'\[PHONE_MASKED\]',
        r'\[ID_MASKED\]',
        r'\[PATH_MASKED\]'
    ]
    
    for pattern in masking_patterns:
        if re.search(pattern, text):
            return True
    
    return False
