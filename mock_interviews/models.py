from django.db import models
from django.utils import timezone
from accounts.models import StudentProfile, User


class MockInterviewSession(models.Model):
    STATUS_CHOICES = (
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    TARGET_CHOICES = (
        ('everyone', 'Everyone'),
        ('department', 'Specific Department'),
        ('drive', 'Specific Placement Drive'),
    )

    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mi_sessions_created')
    created_at  = models.DateTimeField(default=timezone.now)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    label       = models.CharField(max_length=120, blank=True, default='')
    
    # Targeting
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES, default='everyone')
    department  = models.ForeignKey('accounts.Course', on_delete=models.SET_NULL, null=True, blank=True, help_text="Filter students by department")
    year        = models.IntegerField(null=True, blank=True, help_text="Filter students by year")
    target_drive = models.ForeignKey('core.PlacementDrive', on_delete=models.SET_NULL, null=True, blank=True, related_name='mi_sessions')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"MI Session #{self.pk} – {self.get_status_display()} ({self.created_at.strftime('%d %b %Y')})"

    @property
    def total_pairs(self):
        return self.pairs.count()

    @property
    def submissions_count(self):
        """Number of unique evaluators who have submitted at least once."""
        return (
            MockInterviewEvaluation.objects
            .filter(session=self)
            .values('evaluator')
            .distinct()
            .count()
        )

    @property
    def expected_submissions(self):
        """Every student in every pair can submit once about their partner."""
        return self.pairs.count() * 2  # each pair → 2 evaluations

    @property
    def completion_pct(self):
        exp = self.expected_submissions
        if exp == 0:
            return 0
        return round(self.submissions_count / exp * 100, 1)


class MockInterviewPair(models.Model):
    """
    Represents a single peer pairing within a session.
    student1 evaluates student2, student2 evaluates student1.
    Trio groups: a third 'extra' student evaluates student1.
    """
    session  = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='pairs')
    student1 = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mi_pairs_as_s1')
    student2 = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mi_pairs_as_s2')
    # optional 3rd member for odd-numbered groups
    student3 = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                  related_name='mi_pairs_as_s3', null=True, blank=True)

    class Meta:
        unique_together = ('session', 'student1', 'student2')

    def __str__(self):
        s3 = f" + {self.student3.user.get_full_name()}" if self.student3 else ""
        return (f"{self.student1.user.get_full_name()} ↔ "
                f"{self.student2.user.get_full_name()}{s3}")

    def members(self):
        """Returns all students in this pair/trio."""
        result = [self.student1, self.student2]
        if self.student3:
            result.append(self.student3)
        return result

    def partner_of(self, student_profile):
        """Given a StudentProfile, return the partner(s) in this pair."""
        members = self.members()
        return [m for m in members if m != student_profile]


class MockInterviewEvaluation(models.Model):
    """
    A student's evaluation of their partner.
    No unique constraint → students may update by re-submitting (latest row wins logically,
    but we INSERT every time so history is preserved; views show the latest).
    """
    session      = models.ForeignKey(MockInterviewSession, on_delete=models.CASCADE, related_name='evaluations')
    evaluator    = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='evaluations_given')
    evaluatee    = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='evaluations_received')

    communication   = models.DecimalField(max_digits=3, decimal_places=1)   # 1-10
    confidence      = models.DecimalField(max_digits=3, decimal_places=1)
    technical       = models.DecimalField(max_digits=3, decimal_places=1)
    body_language   = models.DecimalField(max_digits=3, decimal_places=1)
    problem_solving = models.DecimalField(max_digits=3, decimal_places=1)
    feedback        = models.TextField(blank=True, default='')
    submitted_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('session', 'evaluator', 'evaluatee')

    def __str__(self):
        return (f"{self.evaluator.user.get_full_name()} → "
                f"{self.evaluatee.user.get_full_name()} (Session #{self.session_id})")

    @property
    def average_score(self):
        scores = [
            float(self.communication),
            float(self.confidence),
            float(self.technical),
            float(self.body_language),
            float(self.problem_solving),
        ]
        return round(sum(scores) / len(scores), 2)

    @property
    def performance_level(self):
        avg = self.average_score
        if avg >= 8:
            return 'Excellent'
        elif avg >= 6:
            return 'Good'
        return 'Needs Improvement'
