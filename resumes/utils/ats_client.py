import httpx
import os
from django.conf import settings
from typing import Dict, Any, Optional

# Microservice URL (Default to local docker/dev)
ATS_SERVICE_URL = getattr(settings, 'ATS_SERVICE_URL', 'http://127.0.0.1:8001')

async def call_ats_analyze_service(resume_file_path: str, job_description: str) -> Optional[Dict[str, Any]]:
    """
    Call the FastAPI ATS microservice to analyze a resume.
    """
    if not os.path.exists(resume_file_path):
        print(f"ATS Error: Resume file not found at {resume_file_path}")
        return None
        
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            with open(resume_file_path, 'rb') as f:
                response = await client.post(
                    f"{ATS_SERVICE_URL}/analyze-resume",
                    files={"resume": (os.path.basename(resume_file_path), f)},
                    data={"job_description": job_description}
                )
                
            if response.status_code == 200:
                return response.json()
            else:
                print(f"ATS Service error: {response.status_code} - {response.text}")
                return None
                
    except httpx.ConnectError:
        print(f"ATS Connection error: Could not connect to {ATS_SERVICE_URL}. Is the microservice running?")
        return None
    except Exception as e:
        print(f"ATS error: {type(e).__name__}: {e}")
        return None

def sync_analyze_resume(resume_instance, job_description: str):
    """
    Wrapper for sync Django views to call the async microservice.
    """
    import asyncio
    
    # We need to run the async function in a sync environment
    try:
        # Note: In a production Django app with gunicorn/uvicorn, consider using asgiref.sync.async_to_sync
        from asgiref.sync import async_to_sync
        return async_to_sync(call_ats_analyze_service)(resume_instance.file.path, job_description)
    except:
        # Fallback for simple environments
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(call_ats_analyze_service(resume_instance.file.path, job_description))
