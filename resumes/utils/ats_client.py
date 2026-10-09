"""
ATS microservice client — secure, resilient, with explicit timeouts and
safe error handling. Failures never crash the main application.
"""
import logging
import os
from typing import Any, Dict, Optional

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

# Read from settings (env-configurable, never hard-coded)
ATS_SERVICE_URL = getattr(settings, 'ATS_SERVICE_URL', 'http://127.0.0.1:8001').rstrip('/')

# Sensible timeouts: 5 s to connect, 60 s total for the response
_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 60.0
_TIMEOUT = httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT)


async def call_ats_analyze_service(
    resume_file_path: str, job_description: str
) -> Optional[Dict[str, Any]]:
    """
    Call the FastAPI ATS microservice to analyse a resume.

    Returns the parsed JSON dict on success, or None on any failure.
    Never raises — callers can always treat None as "service unavailable".
    """
    if not resume_file_path or not os.path.isfile(resume_file_path):
        logger.warning("ATS: resume file does not exist (path withheld for security)")
        return None

    url = f"{ATS_SERVICE_URL}/analyze-resume"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            with open(resume_file_path, 'rb') as fh:
                response = await client.post(
                    url,
                    files={"resume": (os.path.basename(resume_file_path), fh, "application/pdf")},
                    data={"job_description": job_description[:4096]},  # cap JD length
                )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                "ATS service returned HTTP %s (url=%s)",
                response.status_code,
                url,
            )
            return None

    except httpx.ConnectError:
        logger.warning("ATS: cannot connect to %s — is the microservice running?", ATS_SERVICE_URL)
        return None
    except httpx.TimeoutException:
        logger.warning("ATS: request timed out after %.1f s", _READ_TIMEOUT)
        return None
    except httpx.HTTPStatusError as exc:
        logger.error("ATS: HTTP error %s", exc.response.status_code)
        return None
    except Exception:
        logger.exception("ATS: unexpected error during analysis")
        return None


def sync_analyze_resume(
    resume_instance, job_description: str
) -> Optional[Dict[str, Any]]:
    """
    Synchronous wrapper for Django views that call the async microservice.
    Always returns None on service unavailability — never raises.
    """
    file_path = getattr(resume_instance.file, 'path', None)
    if not file_path:
        logger.warning("ATS: resume instance has no file path")
        return None

    try:
        from asgiref.sync import async_to_sync
        return async_to_sync(call_ats_analyze_service)(file_path, job_description)
    except Exception:
        logger.exception("ATS: sync wrapper failed")
        return None
