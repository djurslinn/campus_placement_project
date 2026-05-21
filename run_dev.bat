@echo off
echo Starting Campus Placement Project...
echo ===================================
start "ATS AI Service" cmd /k "cd ats-ai-service && ..\venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8001"
echo [✓] ATS AI Service command sent (Port 8001)
echo.
echo Starting Django Server...
..\venv\Scripts\activate && python manage.py runserver 0.0.0.0:8000
pause
