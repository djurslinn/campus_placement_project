# Resume Management System - Django App

AI-powered resume management system for campus placement with ATS scoring and resume generation.

## Features

✅ **Resume Upload** - Upload PDF resumes with text extraction  
✅ **ATS Score Check** - AI-powered ATS analysis with scores and suggestions  
✅ **Resume Builder** - AI-generated ATS-optimized resumes  
✅ **PDF Export** - Generate and download professional PDF resumes  
✅ **Student-only Access** - Secure, per-student resume management  
✅ **PII Protection** - Automatic masking of sensitive data before AI processing  

---

## Installation

### 1. Extract the app into your Django project

```bash
# Extract the zip file into your project root
unzip resumes.zip
# This creates a 'resumes' folder in your project
```

### 2. Install Required Dependencies

```bash
pip install pdfplumber reportlab
# Optional for Ollama AI integration:
pip install requests
```

### 3. Update Django Settings

Add to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'resumes',
]
```

Configure media files in `settings.py`:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 4. Update Project URLs

Add to your project's `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... existing patterns ...
    path('resumes/', include('resumes.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 5. Run Migrations

```bash
python manage.py makemigrations resumes
python manage.py migrate
```

### 6. Create Media Directories

```bash
mkdir -p media/resumes/uploads
mkdir -p media/resumes/generated
```

---

## AI Configuration

### Option 1: Use Mock AI (Default - No Setup Required)

The app works out of the box with mock AI responses. Perfect for testing!

### Option 2: Configure Ollama (Recommended for Production)

1. **Install Ollama:**
   ```bash
   # Visit https://ollama.ai for installation instructions
   ```

2. **Start Ollama and pull a model:**
   ```bash
   ollama serve
   ollama pull llama2
   ```

3. **Update environment variables:**
   ```bash
   # In your .env file or environment
   export USE_MOCK_LLM=false
   export OLLAMA_URL=http://localhost:11434
   ```

### Option 3: Other AI Providers

Edit `resumes/ai_agent/llm_client.py` to integrate with your preferred AI service.

---

## Usage

### For Students

1. **Upload Resume**
   - Navigate to `/resumes/upload/`
   - Upload PDF resume (max 5MB)
   - Text is automatically extracted

2. **Check ATS Score**
   - Go to "My Resumes"
   - Click "Check ATS Score" on any uploaded resume
   - View score, missing skills, and suggestions

3. **Build Resume with AI**
   - Navigate to `/resumes/builder/`
   - Fill in your details
   - AI generates optimized resume
   - Preview and download as PDF

4. **Manage Resumes**
   - View all resumes at `/resumes/my-resumes/`
   - Download PDFs
   - Check multiple ATS scores

---

## Security Features

✅ **Login Required** - All views require authentication  
✅ **Per-Student Access** - Students can only access their own resumes  
✅ **PII Masking** - Email, phone, IDs masked before AI processing  
✅ **File Validation** - PDF-only uploads with size limits  
✅ **Secure File Storage** - User-specific upload directories  

---

## File Structure

```
resumes/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py              # App configuration
├── models.py            # Resume and ATSScore models
├── urls.py              # URL routing
├── views/
│   ├── upload.py        # Resume upload views
│   ├── ats_check.py     # ATS analysis views
│   ├── builder.py       # Resume builder views
│   └── pdf_export.py    # PDF generation views
├── ai_agent/
│   ├── llm_client.py    # LLM interface (Ollama/Mock)
│   ├── ats_agent.py     # ATS scoring logic
│   ├── resume_agent.py  # Resume generation logic
│   └── prompts.py       # AI prompts
├── services/
│   ├── file_handler.py  # PDF text extraction
│   ├── data_masking.py  # PII protection
│   └── pdf_generator.py # PDF creation
├── templates/resumes/   # HTML templates
├── static/resumes/      # CSS and JS
└── migrations/          # Database migrations
```

---

## Admin Panel

Access Django admin to manage resumes and ATS scores:

```bash
python manage.py createsuperuser
# Then visit /admin/
```

---

## API Endpoints

- `/resumes/upload/` - Upload resume
- `/resumes/my-resumes/` - List all resumes
- `/resumes/ats-check/<id>/` - Check ATS score
- `/resumes/ats-result/<score_id>/` - View ATS results
- `/resumes/builder/` - AI resume builder
- `/resumes/preview/<id>/` - Preview resume
- `/resumes/generate-pdf/<id>/` - Generate PDF
- `/resumes/download/<id>/` - Download PDF

---

## Dependencies

**Required:**
- Django >= 3.2
- pdfplumber >= 0.9.0
- reportlab >= 3.6.0

**Optional:**
- requests >= 2.28.0 (for Ollama integration)
- xhtml2pdf >= 0.2.8 (alternative PDF generation)

---

## Troubleshooting

### PDF Text Extraction Fails
```bash
pip install pdfplumber --upgrade
```

### PDF Generation Fails
```bash
pip install reportlab --upgrade
# Or use alternative:
pip install xhtml2pdf
```

### AI Not Working
- Check if `USE_MOCK_LLM=true` in environment (default mode)
- For Ollama: ensure `ollama serve` is running
- Check Ollama model: `ollama list`

### Permission Denied Errors
```bash
chmod -R 755 media/resumes/
```

---

## Production Deployment

1. **Set DEBUG=False** in settings
2. **Configure proper media file serving** (use nginx/S3)
3. **Set up Ollama** on a dedicated server
4. **Enable HTTPS** for file uploads
5. **Set up proper backup** for media files
6. **Configure logging** for AI errors

---

## License

This app is provided as-is for educational and commercial use in campus placement systems.

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Check Django and dependency documentation

---

## Version

**v1.0.0** - Initial Release
- Resume upload and management
- ATS scoring with AI
- AI resume builder
- PDF generation
- Complete security implementation
