from django.db import models
from accounts.models import User, StudentProfile
from django.core.validators import FileExtensionValidator

class PDFTest(models.Model):
    TARGET_CHOICES = (
        ('everyone', 'Everyone'),
        ('department', 'Specific Department'),
        ('drive', 'Specific Placement Drive'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    pdf_file = models.FileField(
        upload_to='aptitude_pdfs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    answer_key = models.TextField(
        help_text="Format: 1:A,2:B,3:C... No spaces typically."
    )
    total_questions = models.PositiveIntegerField(
        help_text="Automatically calculated from the answer key on save, but can be manually set.",
        default=0
    )
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Targeting
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='everyone')
    target_department = models.ForeignKey('accounts.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_tests')
    target_drive = models.ForeignKey('core.PlacementDrive', on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_tests')
    
    is_published = models.BooleanField(default=True, help_text="If unchecked, students cannot see this test.")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Auto-calculate total questions from key if possible
        if self.answer_key:
            try:
                # Assuming format "1:A,2:B,..."
                items = [x for x in self.answer_key.split(',') if x.strip()]
                self.total_questions = len(items)
            except:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class PDFTestResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='pdf_test_results')
    test = models.ForeignKey(PDFTest, on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    submitted_answers = models.TextField(blank=True, null=True, help_text="Stored as logical string e.g. 1:A,2:B...")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.test.title} ({self.score})"
