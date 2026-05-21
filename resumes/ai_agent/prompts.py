"""
Prompt templates for AI agents.
"""


# ATS Analysis Prompts
ATS_SYSTEM_PROMPT = """You are an expert ATS (Applicant Tracking System) analyzer. 
Your job is to analyze resumes and provide scores, missing skills, and improvement suggestions.
Be objective, professional, and provide actionable feedback."""


ATS_ANALYSIS_PROMPT = """Analyze the following resume and provide:
1. An ATS score from 0-100 (higher is better)
2. Missing skills that would improve the resume
3. Specific suggestions for improvement

Resume text:
{resume_text}

Respond in JSON format:
{{
    "score": <number 0-100>,
    "missing_skills": "<comma-separated list of skills>",
    "suggestions": "<actionable suggestions for improvement>"
}}
"""


# Resume Generation Prompts
RESUME_BUILDER_SYSTEM_PROMPT = """You are an expert resume writer specializing in ATS-optimized resumes.
Create professional, well-structured resumes that highlight candidate strengths.
Use clear formatting with sections: Summary, Skills, Education, Projects, and Experience.
Focus on achievements and quantifiable results."""


RESUME_GENERATION_PROMPT = """Create a professional, ATS-optimized resume using the following information:

Full Name: {full_name}
Skills: {skills}
Education: {education}
Projects: {projects}
Experience: {experience}

Requirements:
- Use markdown formatting with clear section headers
- Start with a compelling professional summary (2-3 sentences)
- List skills in bullet points or comma-separated
- Highlight achievements with quantifiable metrics where possible
- Use action verbs and professional language
- Keep the tone professional and confident
- Ensure ATS compatibility

Generate a complete, professional resume now:
"""


def get_ats_prompt(resume_text):
    """
    Get formatted ATS analysis prompt.
    
    Args:
        resume_text: The resume text to analyze
        
    Returns:
        tuple: (system_prompt, user_prompt)
    """
    user_prompt = ATS_ANALYSIS_PROMPT.format(resume_text=resume_text)
    return ATS_SYSTEM_PROMPT, user_prompt


def get_resume_generation_prompt(resume_data):
    """
    Get formatted resume generation prompt.
    
    Args:
        resume_data: Dictionary containing resume information
        
    Returns:
        tuple: (system_prompt, user_prompt)
    """
    user_prompt = RESUME_GENERATION_PROMPT.format(
        full_name=resume_data.get('full_name', 'Student'),
        skills=resume_data.get('skills', 'Not provided'),
        education=resume_data.get('education', 'Not provided'),
        projects=resume_data.get('projects', 'Not provided'),
        experience=resume_data.get('experience', 'Not provided')
    )
    return RESUME_BUILDER_SYSTEM_PROMPT, user_prompt
