from django.db import models
from django.conf import settings

class physicalSession(models.Model):
    TARGET_CHOICES = (
        ('everyone', 'Everyone'),
        ('department', 'Specific Department'),
        ('drive', 'Specific Placement Drive'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200, blank=True)
    
    # Targeting
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='everyone')
    department = models.ForeignKey('accounts.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions')
    target_drive = models.ForeignKey('core.PlacementDrive', on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_sessions')

    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='conducted_sessions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.date}"

class Attendance(models.Model):
    session = models.ForeignKey(physicalSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='session_attendances'
    )
    is_present = models.BooleanField(default=False)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.email} - {self.session.title} - {'Present' if self.is_present else 'Absent'}"
