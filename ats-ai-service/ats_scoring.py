import json
import re
import spacy
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load NLP models
# Note: You need to download spacy model manually: python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load skills database
with open("skills_database.json", "r") as f:
    SKILLS_DB = json.load(f)

ALL_SKILLS = set(SKILLS_DB["technical"] + SKILLS_DB["soft_skills"])

def extract_skills(text: str) -> List[str]:
    """Extract skills from text by matching with database."""
    doc = nlp(text.lower())
    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
    
    # Simple direct matching
    found_skills = []
    text_lower = text.lower()
    for skill in ALL_SKILLS:
        skill_lower = skill.lower()
        if re.search(r'\b' + re.escape(skill_lower) + r'\b', text_lower):
            found_skills.append(skill)
            
    return sorted(list(set(found_skills)))

def get_years_experience(text: str) -> int:
    """Approximate years of experience using regex and spacy entities."""
    doc = nlp(text)
    years = 0
    
    # Search for date ranges or "X years"
    year_patterns = [
        r'(\d+)\s+years?',
        r'(\d{4})\s*-\s*(\d{4}|present|current)',
    ]
    
    # 1. Regex search
    found_numbers = re.findall(r'(\d+)\s*years?', text.lower())
    if found_numbers:
        years = max([int(n) for n in found_numbers])
        
    # 2. Date extraction for ranges
    # (Simplified approach)
    date_ranges = re.findall(r'(\d{4})\s*-\s*(\d{4})', text)
    if date_ranges:
        total = 0
        for start, end in date_ranges:
            total += int(end) - int(start)
        years = max(years, total)
        
    return years

def extract_sections(text: str) -> Dict[str, str]:
    """Extract content for each identified section with improved accuracy."""
    sections_patterns = {
        "Summary": [r"summary", r"objective", r"profile", r"about me", r"professional profile"],
        "Education": [r"education", r"academic", r"qualification", r"academic background"],
        "Experience": [r"experience", r"employment", r"work history", r"professional background", r"work experience"],
        "Projects": [r"projects", r"technical projects", r"personal projects", r"academic projects"],
        "Skills": [r"skills", r"technical expertise", r"competencies", r"abilities", r"technical skills"],
        "Certifications": [r"certifications", r"certificate", r"awards", r"achievements", r"certifications & awards"]
    }
    
    # Pre-process headers to find their positions
    headers = []
    text_lines = text.split('\n')
    
    # Track the start index of each line in the original text
    line_offsets = []
    current_offset = 0
    for line in text_lines:
        line_offsets.append(current_offset)
        current_offset += len(line) + 1 # +1 for newline
        
    for i, line in enumerate(text_lines):
        line_lower = line.strip().lower()
        if not line_lower:
            continue
            
        # Headers are usually short and on their own line or at the start
        if len(line_lower) > 30:
            continue
            
        for section, patterns in sections_patterns.items():
            for pattern in patterns:
                # Match pattern as the whole line or starting the line
                if re.fullmatch(pattern + r':?', line_lower) or re.match(r'^' + pattern + r'\s*$', line_lower):
                    headers.append({
                        'section': section,
                        'start': line_offsets[i],
                        'end': line_offsets[i] + len(line),
                        'line_idx': i
                    })
                    break
    
    # Sort headers by their appearance
    headers.sort(key=lambda x: x['start'])
    
    # Remove overlapping or redundant headers (keep first match for a line)
    unique_headers = []
    seen_lines = set()
    for h in headers:
        if h['line_idx'] not in seen_lines:
            unique_headers.append(h)
            seen_lines.add(h['line_idx'])
            
    # Extract content
    extracted_sections = {}
    for i in range(len(unique_headers)):
        current = unique_headers[i]
        start_pos = current['end']
        
        if i + 1 < len(unique_headers):
            end_pos = unique_headers[i+1]['start']
        else:
            end_pos = len(text)
            
        content = text[start_pos:end_pos].strip()
        
        # If section already exists, append (e.g. multiple "Experience" sections)
        if current['section'] in extracted_sections:
            extracted_sections[current['section']] += "\n" + content
        else:
            extracted_sections[current['section']] = content
            
    return extracted_sections

def check_sections(text: str) -> Dict[str, bool]:
    """Check for presence of common resume sections."""
    extracted = extract_sections(text)
    sections = ["Summary", "Education", "Experience", "Projects", "Skills", "Certifications"]
    return {s: (s in extracted and len(extracted[s]) > 0) for s in sections}

def calculate_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
    """Calculate the ATS score and insights."""
    
    # 0. Section Check
    sections_found = check_sections(resume_text)
    
    # 1. Semantic Similarity (Keyword replacement via embeddings)
    # Using small chunks or whole text
    embeddings = model.encode([resume_text, job_description])
    semantic_score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]) * 100
    
    # 2. Extract Skills
    resume_skills = set(extract_skills(resume_text))
    jd_skills = set(extract_skills(job_description))
    
    matched_skills = list(resume_skills.intersection(jd_skills))
    missing_skills = list(jd_skills - resume_skills)
    
    # 3. Calculate Part Scores
    
    # a. Keyword / Semantic Match (40%)
    keyword_score = semantic_score
    
    # b. Skills Match (30%)
    if jd_skills:
        skills_score = (len(matched_skills) / len(jd_skills)) * 100
    else:
        skills_score = 100 if resume_skills else 50
        
    # c. Experience Detection (20%)
    # Look for "Experience" or years of work
    resume_exp = get_years_experience(resume_text)
    jd_exp = get_years_experience(job_description)
    
    if jd_exp > 0:
        exp_score = min((resume_exp / jd_exp) * 100, 100)
    else:
        # Default if jd has no exp mentioned
        exp_score = 75 if resume_exp > 0 else 50
        
    # d. Education Match (10%)
    # Basic check for degrees
    degrees = ["be", "btech", "mtech", "msc", "bsc", "bachelor", "master", "phd", "diploma", "graduate"]
    found_degrees_resume = [d for d in degrees if re.search(r'\b' + d + r'\b', resume_text.lower())]
    found_degrees_jd = [d for d in degrees if re.search(r'\b' + d + r'\b', job_description.lower())]
    
    if found_degrees_jd:
        matched_degrees = set(found_degrees_resume).intersection(set(found_degrees_jd))
        edu_score = 100 if matched_degrees else 0
    else:
        edu_score = 100 if found_degrees_resume else 50
        
    # Final weighted score
    # Bonus for sections (up to 5 points)
    section_bonus = (sum(sections_found.values()) / len(sections_found)) * 5
    
    final_score = (
        (keyword_score * 0.4) +
        (skills_score * 0.3) +
        (exp_score * 0.2) +
        (edu_score * 0.1)
    ) + section_bonus
    
    # Extract actual section content for display
    extracted_sections = extract_sections(resume_text)
    
    # 4. Generate Suggestions
    suggestions = []
    if missing_skills:
        suggestions.append(f"Add missing technical skills: {', '.join(missing_skills[:3])}")
    if exp_score < 70:
        suggestions.append("Clarify work experience durations and include quantified achievements with numbers")
    if keyword_score < 60:
        suggestions.append("Optimize resume language to better align with the job description keywords")
    
    missing_sections = [s for s, found in sections_found.items() if not found]
    if missing_sections:
        suggestions.append(f"Add missing sections: {', '.join(missing_sections)}")
        
    return {
        "ats_score": round(min(final_score, 100)),
        "keyword_score": round(keyword_score),
        "skills_score": round(skills_score),
        "experience_score": round(exp_score),
        "education_score": round(edu_score),
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "sections_found": sections_found,
        "extracted_sections": extracted_sections, # The text content of each section
        "discovered_details": {
            "skills": list(resume_skills),
            "years_experience": resume_exp,
            "degrees": list(set(found_degrees_resume)),
        },
        "suggestions": suggestions
    }
