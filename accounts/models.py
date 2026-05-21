from django.contrib.auth.models import AbstractUser
from django.db import models


class Course(models.Model):
    CATEGORY_CHOICES = (
        ('UG', 'Undergraduate (UG)'),
        ('PG', 'Postgraduate (PG)'),
    )

    YEAR_CHOICES = (
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
    )

    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    type = models.CharField(max_length=100, help_text="e.g. Bachelor of Arts (B.A.), Master of Science (M.Sc.)")
    name = models.CharField(max_length=200, help_text="e.g. Economics, Physics (Hons)")
    year = models.IntegerField(choices=YEAR_CHOICES, default=3, help_text="Course duration in years")

    def __str__(self):
        return f"{self.type} - {self.name} ({self.category})"


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('coordinator', 'Coordinator'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='admin'   # ⭐ VERY IMPORTANT
    )

    department = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, db_column='department')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"


class StudentProfile(models.Model):
    PLACEMENT_STATUS_CHOICES = (
        ('not_placed', 'Not Placed'),
        ('placed', 'Placed'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=20, unique=True)
    year = models.IntegerField()
    batch = models.IntegerField(null=True, blank=True, help_text="Admission Year (YYYY)")
    phone = models.CharField(max_length=15)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    placement_status = models.CharField(
        max_length=20,
        choices=PLACEMENT_STATUS_CHOICES,
        default='not_placed'
    )
    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        null=True,
        blank=True
    )
    backlogs = models.IntegerField(default=0)
    age = models.PositiveIntegerField(null=True, blank=True)
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.roll_no} - {self.user.get_full_name()}"


# OTP is no longer stored in the database.
# It is generated in views.py, stored in the Django session with a timestamp,
# and verified from the session — fully ephemeral, no migration needed.