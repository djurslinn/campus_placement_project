# AI-Powered ATS Resume Score Crawler (Microservice)

A high-performance, completely free, and unlimited ATS scoring engine built with FastAPI, spaCy, and Sentence-Transformers.

## Features
- **PDF & DOCX Support**: Extract text from standard resume formats.
- **Semantic Matching**: Uses `sentence-transformers` (SBERT) to compare the meaning of the resume against the job description.
- **Skill Detection**: Matches skills against a configurable JSON database.
- **Scoring System**:
  - Keyword Match (40%)
  - Skills Match (30%)
  - Experience Detection (20%)
  - Education Match (10%)
- **Actionable Insights**: Returns a list of missing skills and suggestions for improvement.

## Installation

### Prerequisites
- Python 3.10+
- `pip`

### 1. Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Run the Service
```bash
python main.py
```
The service will start at `http://localhost:8001`.

## API Documentation

### POST `/analyze-resume`
Analyzes a resume file against a job description text.

**Request (Multipart Form-Data):**
- `resume`: Binary file (PDF/DOCX)
- `job_description`: Text string

**Example Response:**
```json
{
  "ats_score": 75,
  "keyword_score": 68,
  "skills_score": 85,
  "experience_score": 70,
  "education_score": 100,
  "missing_skills": ["Docker", "Kubernetes"],
  "matched_skills": ["Python", "SQL", "Machine Learning"],
  "suggestions": [
     "Add missing technical skills mentioned in the job description",
     "Include quantified achievements"
  ]
}
```

### GET `/health`
Check if the service is alive.

## Docker Deployment
```bash
docker build -t ats-ai-service .
docker run -p 8001:8001 ats-ai-service
```

## Django Integration Code (Example)
```python
import httpx

async def get_ats_score(resume_path, jd_text):
    async with httpx.AsyncClient() as client:
        with open(resume_path, 'rb') as f:
            response = await client.post(
                "http://localhost:8001/analyze-resume",
                files={"resume": f},
                data={"job_description": jd_text}
            )
        return response.json()
```
