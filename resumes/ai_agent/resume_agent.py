"""
Resume Generation Agent for creating ATS-optimized resumes using AI.
"""

import logging
from .llm_client import get_llm_client
from .prompts import get_resume_generation_prompt

logger = logging.getLogger(__name__)


def generate_resume_content(resume_data):
    """
    Generate professional resume content using AI.
    
    Args:
        resume_data: Dictionary containing:
            - full_name: Student's full name
            - skills: List or text of skills
            - education: Education details
            - projects: Project descriptions
            - experience: Work experience
    
    Returns:
        str: AI-generated resume content in markdown format
    """
    try:
        # Get LLM client
        llm = get_llm_client()
        
        # Get prompts
        system_prompt, user_prompt = get_resume_generation_prompt(resume_data)
        
        # Generate resume
        resume_content = llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        # Clean up the content
        resume_content = _clean_resume_content(resume_content)
        
        return resume_content
        
    except Exception as e:
        logger.error(f"Error generating resume: {e}")
        
        # Fallback: generate basic resume template
        return _generate_fallback_resume(resume_data)


def _clean_resume_content(content):
    """
    Clean and format AI-generated resume content.
    
    Args:
        content: Raw AI-generated content
        
    Returns:
        str: Cleaned resume content
    """
    # Remove any markdown code fences if present
    content = content.replace('```markdown', '').replace('```', '')
    
    # Remove excessive newlines
    while '\n\n\n' in content:
        content = content.replace('\n\n\n', '\n\n')
    
    # Ensure content starts fresh (remove any preamble)
    lines = content.split('\n')
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('#') or line.strip().upper() in ['PROFESSIONAL SUMMARY', 'SUMMARY', 'OBJECTIVE']:
            start_idx = i
            break
    
    content = '\n'.join(lines[start_idx:])
    
    return content.strip()


def _generate_fallback_resume(resume_data):
    """
    Generate a basic resume template when AI is not available.
    
    Args:
        resume_data: Resume information dictionary
        
    Returns:
        str: Basic resume template
    """
    full_name = resume_data.get('full_name', 'Student Name')
    skills = resume_data.get('skills', 'Not provided')
    education = resume_data.get('education', 'Not provided')
    projects = resume_data.get('projects', 'Not provided')
    experience = resume_data.get('experience', 'Not provided')
    
    resume_template = f"""# {full_name}

## PROFESSIONAL SUMMARY
Motivated and detail-oriented professional with strong technical skills and a passion for continuous learning. Proven ability to work effectively in team environments and deliver high-quality results.

## TECHNICAL SKILLS
{_format_skills(skills)}

## EDUCATION
{_format_section(education)}

## PROJECTS
{_format_section(projects)}

## EXPERIENCE
{_format_section(experience) if experience and experience != 'Not provided' else 'Seeking opportunities to apply skills and contribute to innovative projects.'}

## KEY COMPETENCIES
- Problem-solving and analytical thinking
- Team collaboration and communication
- Adaptability and quick learning
- Attention to detail and quality
"""
    
    return resume_template


def _format_skills(skills):
    """Format skills section."""
    if not skills or skills == 'Not provided':
        return '- Technical skills to be added'
    
    # If skills are comma-separated, convert to bullet points
    if ',' in skills:
        skill_list = [s.strip() for s in skills.split(',') if s.strip()]
        return '\n'.join([f'- {skill}' for skill in skill_list])
    
    # If skills are already in lines
    if '\n' in skills:
        lines = [line.strip() for line in skills.split('\n') if line.strip()]
        return '\n'.join([f'- {line}' if not line.startswith('-') else line for line in lines])
    
    return f'- {skills}'


def _format_section(content):
    """Format a resume section."""
    if not content or content == 'Not provided':
        return 'To be added'
    
    # If content doesn't have proper formatting, add basic structure
    if '\n' not in content and len(content) > 100:
        # Long single paragraph - add some structure
        sentences = content.split('.')
        return '\n'.join([f'- {s.strip()}.' for s in sentences if s.strip()])
    
    return content


def enhance_resume_section(section_content, section_type):
    """
    Enhance a specific resume section using AI.
    
    Args:
        section_content: Original section content
        section_type: Type of section (e.g., 'summary', 'experience', 'projects')
        
    Returns:
        str: Enhanced section content
    """
    try:
        llm = get_llm_client()
        
        prompt = f"""Enhance the following {section_type} section of a resume. 
Make it more professional, ATS-friendly, and impactful. Use action verbs and quantifiable achievements where possible.

Original content:
{section_content}

Enhanced version:"""
        
        enhanced = llm.generate(
            prompt=prompt,
            temperature=0.7
        )
        
        return _clean_resume_content(enhanced)
        
    except Exception as e:
        logger.error(f"Error enhancing section: {e}")
        return section_content
