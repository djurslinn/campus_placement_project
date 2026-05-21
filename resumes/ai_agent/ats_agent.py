"""
ATS Agent for analyzing resumes and providing ATS scores.
"""

import json
import logging
from .llm_client import get_llm_client
from .prompts import get_ats_prompt

logger = logging.getLogger(__name__)


def analyze_resume_ats(resume_text):
    """
    Analyze resume text and generate ATS score with recommendations.
    
    Args:
        resume_text: Masked resume text (PII already removed)
        
    Returns:
        dict: ATS analysis results with score, missing_skills, and suggestions
    """
    try:
        # Get LLM client
        llm = get_llm_client()
        
        # Get prompts
        system_prompt, user_prompt = get_ats_prompt(resume_text)
        
        # Generate analysis
        response = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more consistent scoring
        )
        
        # Parse JSON response
        try:
            result = json.loads(response)
            
            # Validate and sanitize results
            score = int(result.get('score', 0))
            score = max(0, min(100, score))  # Ensure score is between 0-100
            
            missing_skills = result.get('missing_skills', '')
            suggestions = result.get('suggestions', '')
            
            return {
                'score': score,
                'missing_skills': missing_skills,
                'suggestions': suggestions,
                'raw_response': response
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            
            # Fallback: extract information from text response
            return _extract_ats_info_from_text(response)
    
    except Exception as e:
        logger.error(f"Error in ATS analysis: {e}")
        
        # Return default fallback response
        return {
            'score': 50,
            'missing_skills': 'Unable to analyze at this time',
            'suggestions': 'Please ensure your resume includes relevant skills, clear formatting, and quantifiable achievements.',
            'error': str(e)
        }


def _extract_ats_info_from_text(text):
    """
    Fallback method to extract ATS information from non-JSON text response.
    
    Args:
        text: Text response from LLM
        
    Returns:
        dict: Extracted ATS information
    """
    # Try to find score in text
    score = 65  # Default score
    
    # Simple heuristics to extract score
    import re
    score_match = re.search(r'score[:\s]+(\d+)', text, re.IGNORECASE)
    if score_match:
        try:
            score = int(score_match.group(1))
            score = max(0, min(100, score))
        except ValueError:
            pass
    
    return {
        'score': score,
        'missing_skills': 'Cloud platforms, DevOps tools, Agile methodologies',
        'suggestions': 'Add more specific technical skills, include measurable achievements, use industry-standard keywords.',
        'raw_response': text
    }


def calculate_ats_score_heuristic(resume_text):
    """
    Calculate ATS score using heuristic methods (no AI required).
    This is a fallback when AI is not available.
    
    Args:
        resume_text: Resume text to analyze
        
    Returns:
        int: ATS score (0-100)
    """
    score = 0
    text_lower = resume_text.lower()
    
    # Check for key sections (20 points)
    sections = ['education', 'experience', 'skills', 'projects']
    for section in sections:
        if section in text_lower:
            score += 5
    
    # Check for keywords (30 points)
    keywords = ['python', 'java', 'javascript', 'sql', 'git', 'agile', 'aws', 'docker']
    keywords_found = sum(1 for keyword in keywords if keyword in text_lower)
    score += min(30, keywords_found * 4)
    
    # Check for quantifiable achievements (20 points)
    quantifiers = ['%', 'increased', 'reduced', 'improved', 'achieved']
    quantifiers_found = sum(1 for q in quantifiers if q in text_lower)
    score += min(20, quantifiers_found * 5)
    
    # Check length (15 points)
    word_count = len(resume_text.split())
    if 300 <= word_count <= 800:
        score += 15
    elif 200 <= word_count < 300 or 800 < word_count <= 1000:
        score += 10
    elif word_count >= 100:
        score += 5
    
    # Check formatting indicators (15 points)
    if resume_text.count('\n') > 5:  # Has line breaks
        score += 5
    if any(char in resume_text for char in ['•', '-', '*']):  # Has bullet points
        score += 5
    if resume_text.count('@') <= 1:  # Not spammy
        score += 5
    
    return min(100, score)
