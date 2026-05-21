from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import resume_parser
import ats_scoring

app = FastAPI(title="AI-Powered ATS Optimizer API", version="1.0.0")

# Enable CORS for frontend/Django integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "ats-ai-microservice"}

@app.post("/analyze-resume")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Analyzes a resume against a job description.
    1. Extract text from PDF/DOCX.
    2. Runs scoring logic.
    3. Returns detailed JSON results.
    """
    # Verify file type
    if not (resume.filename.endswith('.pdf') or resume.filename.endswith('.docx')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are supported.")

    try:
        # Read file content
        content = await resume.read()
        
        # Extract text from resume
        resume_text = resume_parser.extract_text(content, resume.filename)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from the provided file.")

        # Calculate ATS score and insights
        result = ats_scoring.calculate_ats_score(resume_text, job_description)
        
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during processing: {str(e)}")

if __name__ == "__main__":
    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8001)
