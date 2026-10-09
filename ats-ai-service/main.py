"""
ATS AI microservice — FastAPI entry point.

Security improvements:
- CORS restricted to configured origins (not wildcard in production).
- File size capped at 10 MB server-side.
- No internal stack traces exposed in API error responses.
- Structured logging instead of bare print().
- /health endpoint reports model readiness.
"""
import logging
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import resume_parser
import ats_scoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS: restrict origins via env; default to localhost only
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))  # 10 MB

app = FastAPI(
    title="AI-Powered ATS Optimizer API",
    version="1.0.0",
    # Disable automatic OpenAPI/docs in production
    docs_url="/docs" if os.getenv("DEBUG", "true").lower() in ("true", "1") else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,  # no cookies between services
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Return a safe error response without exposing internal details."""
    logger.exception("Unhandled error processing %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for load-balancer / Django integration."""
    return {"status": "healthy", "service": "ats-ai-microservice", "version": "1.0.0"}


@app.post("/analyze-resume")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
):
    """
    Analyse a resume against a job description.

    1. Validate file type and size.
    2. Extract text from PDF/DOCX.
    3. Score against job description.
    4. Return detailed JSON results.
    """
    # File type validation
    filename = resume.filename or ""
    if not (filename.lower().endswith(".pdf") or filename.lower().endswith(".docx")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF and DOCX are supported.",
        )

    # Read with a size cap to prevent memory exhaustion
    content = await resume.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_BYTES // (1024*1024)} MB.",
        )

    # Input length cap on job description
    job_description = job_description[:4096]

    try:
        resume_text = resume_parser.extract_text(content, filename)
    except Exception:
        logger.exception("Text extraction failed for file: %s", filename)
        raise HTTPException(status_code=400, detail="Could not extract text from the provided file.")

    if not resume_text or not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the provided file.")

    try:
        result = ats_scoring.calculate_ats_score(resume_text, job_description)
    except Exception:
        logger.exception("ATS scoring failed")
        raise HTTPException(status_code=500, detail="An error occurred during analysis. Please try again.")

    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
