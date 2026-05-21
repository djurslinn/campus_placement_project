# Installation Guide - Resume Management System

This guide will help you integrate the Resume Management app into your Django project.

---

## Quick Start (5 Minutes)

### Step 1: Extract the App
```bash
# Extract the resumes folder into your Django project root
# Your project structure should look like:
# your_project/
# ├── manage.py
# ├── your_project/
# │   ├── settings.py
# │   └── urls.py
# └── resumes/  ← This folder
```

### Step 2: Install Dependencies
```bash
pip install pdfplumber reportlab requests
```

### Step 3: Update settings.py
```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Add this line:
    'resumes',
]

# Add media configuration (if not already present)
import os

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Step 4: Update urls.py (Project Root)
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Add this line:
    path('resumes/', include('resumes.urls')),
]

# Add media serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Step 5: Run Migrations
```bash
python manage.py makemigrations resumes
python manage.py migrate
```

### Step 6: Create Media Folders
```bash
mkdir -p media/resumes/uploads
mkdir -p media/resumes/generated
```

### Step 7: Test It!
```bash
python manage.py runserver

# Visit: http://127.0.0.1:8000/resumes/upload/
```

---

## AI Configuration

### Using Mock AI (Default - Recommended for Testing)

**No setup required!** The app uses intelligent mock responses by default.

### Using Real AI with Ollama (Production)

1. **Install Ollama:**
   ```bash
   # Mac/Linux
   curl https://ollama.ai/install.sh | sh
   
   # Or visit: https://ollama.ai
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Pull a Model:**
   ```bash
   ollama pull llama2
   # or
   ollama pull mistral
   ```

4. **Configure Environment:**
   Create a `.env` file in your project root:
   ```
   USE_MOCK_LLM=false
   OLLAMA_URL=http://localhost:11434
   ```

5. **Load Environment Variables:**
   ```python
   # In settings.py
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   ```

---

## Features Overview

Once installed, students can:

1. **Upload Resumes** → `/resumes/upload/`
2. **View All Resumes** → `/resumes/my-resumes/`
3. **Check ATS Score** → Click "Check ATS Score" on any resume
4. **Build Resume with AI** → `/resumes/builder/`
5. **Download PDFs** → From My Resumes page

---

## Security Notes

✅ **Authentication Required** - All pages require login
✅ **Per-Student Isolation** - Students only see their own data
✅ **PII Protection** - Automatic masking before AI processing
✅ **File Validation** - Only PDF files, max 5MB
✅ **CSRF Protection** - Django CSRF tokens on all forms

---

## Admin Access

```bash
# Create superuser if not exists
python manage.py createsuperuser

# Access admin at: http://127.0.0.1:8000/admin/
# Navigate to: Resumes → Resumes / ATS Scores
```

---

## Testing

### Test Resume Upload:
1. Login as a student
2. Go to `/resumes/upload/`
3. Upload a PDF resume
4. Check "My Resumes" page

### Test ATS Score:
1. Click "Check ATS Score" on uploaded resume
2. View the score and suggestions

### Test Resume Builder:
1. Go to `/resumes/builder/`
2. Fill in the form
3. Click "Generate Resume with AI"
4. Preview the generated resume
5. Click "Generate PDF" to download

---

## Common Issues

### Issue: "No module named 'resumes'"
**Solution:** Ensure the `resumes` folder is in your project root and added to `INSTALLED_APPS`

### Issue: "No such table: resumes_resume"
**Solution:** Run migrations:
```bash
python manage.py makemigrations resumes
python manage.py migrate
```

### Issue: "Media files not loading"
**Solution:** Check `settings.py` has MEDIA_URL and MEDIA_ROOT configured

### Issue: "PDF upload fails"
**Solution:** 
```bash
pip install pdfplumber --upgrade
```

### Issue: "PDF generation fails"
**Solution:**
```bash
pip install reportlab --upgrade
```

---

## Production Deployment

### 1. Security Settings
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Use environment variables for secrets
SECRET_KEY = os.environ.get('SECRET_KEY')
```

### 2. Media File Storage
```python
# Use AWS S3 or similar for production
# Install: pip install django-storages boto3

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
```

### 3. Web Server Configuration (Nginx)
```nginx
# Serve media files
location /media/ {
    alias /path/to/your/project/media/;
}
```

### 4. AI Service Setup
- Deploy Ollama on a separate server
- Update OLLAMA_URL environment variable
- Consider using a managed LLM service for scale

---

## File Permissions (Linux/Mac)

```bash
# Set proper permissions for media directory
chmod -R 755 media/
chown -R www-data:www-data media/  # or your web server user
```

---

## Environment Variables Summary

```bash
# .env file
USE_MOCK_LLM=false              # Set to true for mock AI (testing)
OLLAMA_URL=http://localhost:11434  # Ollama server URL
DEBUG=True                       # Django debug mode
SECRET_KEY=your-secret-key-here
```

---

## Uninstallation

If you need to remove the app:

```bash
# 1. Remove from INSTALLED_APPS in settings.py
# 2. Remove URL pattern from urls.py
# 3. Run migrations to remove database tables
python manage.py migrate resumes zero
# 4. Delete the resumes folder
rm -rf resumes/
# 5. Delete media files (optional)
rm -rf media/resumes/
```

---

## Support & Documentation

- **README.md** - Overview and features
- **INSTALLATION.md** - This file
- Code comments throughout the app
- Django documentation: https://docs.djangoproject.com/

---

## Changelog

**v1.0.0** (Initial Release)
- Resume upload with PDF text extraction
- ATS scoring with AI
- AI-powered resume builder
- PDF generation and download
- Complete security implementation
- Mock AI for testing

---

## Next Steps

After installation, customize:
1. Templates (in `resumes/templates/resumes/`)
2. CSS styles (in `resumes/static/resumes/css/style.css`)
3. AI prompts (in `resumes/ai_agent/prompts.py`)
4. Add your university logo and branding

Enjoy your AI-powered Resume Management System! 🚀
