from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
import os


def upload_resume_path(instance, filename):
    """Generate upload path for student resumes"""
    return f'resumes/uploads/{instance.student.id}/{filename}'


def generated_resume_path(instance, filename):
    """Generate path for AI-generated resumes"""
    return f'resumes/generated/{instance.student.id}/{filename}'


class Resume(models.Model):
    """
    Single resume per student model.
    Supports both uploaded PDFs and AI-generated resumes.
    """
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resume'
    )

    RESUME_TYPE_CHOICES = [
        ('uploaded', 'Uploaded Resume'),
        ('generated', 'AI Generated Resume'),
    ]
    
    resume_type = models.CharField(
        max_length=20, 
        choices=RESUME_TYPE_CHOICES,
        default='uploaded'
    )
    
    # File field for both uploaded and generated PDFs
    file = models.FileField(
        upload_to=upload_resume_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        null=True,
        blank=True
    )
    extracted_text = models.TextField(blank=True, null=True)
    
    # Personal Information
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    portfolio = models.URLField(blank=True)
    address = models.TextField(blank=True)
    
    # Professional Summary
    summary = models.TextField(blank=True)
    
    # Structured data stored as JSON for builder
    education_json = models.JSONField(default=list, blank=True)
    experience_json = models.JSONField(default=list, blank=True)
    projects_json = models.JSONField(default=list, blank=True)
    skills_json = models.JSONField(default=dict, blank=True)
    certifications_json = models.JSONField(default=list, blank=True)
    languages_json = models.JSONField(default=list, blank=True)
    achievements_json = models.JSONField(default=list, blank=True)
    
    # AI enhancement data
    ai_generated_content = models.TextField(blank=True)
    ai_enhanced = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'
    
    def __str__(self):
        return f"{self.student.username} - {self.resume_type} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def get_filename(self):
        """Get the original filename"""
        if self.file:
            return os.path.basename(self.file.name)
        return None
    
    def delete(self, *args, **kwargs):
        """Override delete to remove file from filesystem"""
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)


class ATSScore(models.Model):
    """Model to store detailed ATS analysis results"""
    
    resume = models.OneToOneField(
        Resume, 
        on_delete=models.CASCADE, 
        related_name='ats_score'
    )
    
    # Overall score
    score = models.IntegerField(default=0)
    
    # Score breakdown
    structure_score = models.IntegerField(default=0)
    keyword_score = models.IntegerField(default=0)
    skills_score = models.IntegerField(default=0)
    experience_score = models.IntegerField(default=0)
    education_score = models.IntegerField(default=0)
    action_verb_score = models.IntegerField(default=0)
    ats_safety_score = models.IntegerField(default=0)
    
    # AI contribution
    ai_adjustment = models.IntegerField(default=0)
    role_fit_score = models.IntegerField(default=0)
    
    # Detailed feedback (stored as JSON)
    missing_keywords = models.JSONField(default=list, blank=True)
    weak_sections = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    
    # Analysis metadata
    target_role = models.CharField(max_length=100, blank=True)
    analysis_data = models.JSONField(default=dict, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-analyzed_at']
        verbose_name = 'ATS Score'
        verbose_name_plural = 'ATS Scores'
    
    def __str__(self):
        return f"{self.resume.student.username} - Score: {self.score}"
    
    def get_score_category(self):
        """Categorize the ATS score"""
        if self.score >= 80:
            return 'Excellent'
        elif self.score >= 60:
            return 'Good'
        elif self.score >= 40:
            return 'Average'
        else:
            return 'Needs Improvement'
    
    def get_score_color(self):
        """Get color for score visualization"""
        if self.score >= 80:
            return 'green'
        elif self.score >= 60:
            return 'yellow'
        elif self.score >= 40:
            return 'orange'
        else:
            return 'red'
