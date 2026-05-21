from django.db import models
from accounts.models import User, StudentProfile, Course

class PlacementDrive(models.Model):
    company_name = models.CharField(max_length=200)
    job_role = models.CharField(max_length=200)
    package = models.DecimalField(max_digits=10, decimal_places=2) # in LPA
    description = models.TextField()
    
    # Eligibility
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    eligible_departments = models.ManyToManyField(Course, related_name='placement_drives')
    is_for_all_departments = models.BooleanField(default=False, help_text="If checked, all departments/courses are eligible")
    eligible_batch = models.IntegerField(null=True, blank=True, help_text="Admission batch (e.g., 2022). Leave blank for All.")
    eligible_year = models.IntegerField(null=True, blank=True, default=0, help_text="Eligible year of study (1, 2, 3, or 4). Use 0 or Blank for All.")
    CATEGORY_CHOICES = (
        ('A', 'Category A'),
        ('B', 'Category B'),
        ('C', 'Category C'),
        ('D', 'Category D'),
    )
    # Hierarchy: A is highest, D is lowest
    CATEGORY_RANK = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES, default='A')
    
    registration_link = models.URLField(max_length=500, null=True, blank=True)
    registration_deadline = models.DateTimeField()
    drive_date = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.company_name} - {self.job_role}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.registration_deadline

    @property
    def is_active(self):
        return not self.is_expired

class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('placed', 'Placed'),
    )
    
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    is_accepted = models.BooleanField(default=False, help_text="Ready to Work: student's chosen final placement")
    applied_at = models.DateTimeField(auto_now_add=True)
    placed_at = models.DateTimeField(null=True, blank=True, help_text="Date coordinator marked this student as Placed")

    def get_category_rank(self):
        """Return numeric rank of this drive's category (higher = better)."""
        return PlacementDrive.CATEGORY_RANK.get(self.drive.category.upper(), 0)

    class Meta:
        unique_together = ('drive', 'student')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.drive.company_name}"

class Announcement(models.Model):
    TARGET_CHOICES = (
        ('all', 'All Students'),
        ('drive', 'Specific Drive'),
        ('personal', 'Personal Message'),
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    target_type = models.CharField(max_length=10, choices=TARGET_CHOICES, default='all')
    drive = models.ForeignKey(PlacementDrive, on_delete=models.SET_NULL, null=True, blank=True)
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'announcement')

    def __str__(self):
        return f"Notification for {self.user.email} - {self.announcement.title}"


# --- Aptitude Test Module ---
class Test(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration_minutes = models.IntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )

    def __str__(self):
        return f"Q: {self.text[:50]}"


class TestAttempt(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'test')

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.test.title} - {self.score}"


# --- Mock Interview Module ---
class MockInterview(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mock_interviews')
    interviewer_name = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Interview with {self.interviewer_name} for {self.student.user.get_full_name()}"
