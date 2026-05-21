from django.db import models
from accounts.models import User, StudentProfile

class GDTopic(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class GDSession(models.Model):
    coordinator = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'coordinator'})
    topic = models.ForeignKey(GDTopic, on_delete=models.SET_NULL, null=True)
    custom_topic = models.CharField(max_length=255, blank=True, null=True, help_text="Use this if topic is not in predefined list")
    num_groups = models.PositiveIntegerField()
    scheduled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        topic_name = self.topic.title if self.topic else self.custom_topic
        return f"GD Session: {topic_name} at {self.scheduled_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_evaluated(self):
        """Returns True if all members in all groups have scores assigned."""
        total_members = 0
        scored_members = 0
        for group in self.groups.all():
            m = group.members.all()
            total_members += m.count()
            scored_members += m.filter(score__isnull=False).count()
        
        return total_members > 0 and total_members == scored_members

    @property
    def evaluation_status(self):
        """Returns a string status: Evaluated, Partially Evaluated, or Not Evaluated."""
        total_members = 0
        scored_members = 0
        
        groups = self.groups.all()
        if not groups.exists():
            return "No Groups"
            
        for group in groups:
            m = group.members.all()
            total_members += m.count()
            scored_members += m.filter(score__isnull=False).count()
            
        if total_members == 0:
            return "No Members"
        
        if scored_members == 0:
            return "Not Evaluated"
        elif scored_members < total_members:
            return "Partially Evaluated"
        else:
            return "Evaluated"

class GDGroup(models.Model):
    session = models.ForeignKey(GDSession, on_delete=models.CASCADE, related_name='groups')
    group_name = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.group_name} - {self.session}"

class GDGroupMember(models.Model):
    group = models.ForeignKey(GDGroup, on_delete=models.CASCADE, related_name='members')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('group', 'student')

    def __str__(self):
        return f"{self.student.user.get_full_name()} in {self.group.group_name}"
