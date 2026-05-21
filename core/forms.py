from django import forms
from .models import PlacementDrive, Announcement
from accounts.models import Course

class PlacementDriveForm(forms.ModelForm):
    eligible_departments = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-grid'}),
        required=False,
        help_text="Select all departments that are eligible for this drive"
    )
    
    eligible_batch = forms.ChoiceField(choices=[], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    eligible_year = forms.ChoiceField(choices=[(0, "All Years")] + [(i, f"Year {i}") for i in range(1, 5)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = PlacementDrive
        fields = ['company_name', 'category', 'job_role', 'package', 'description', 
                  'min_cgpa', 'is_for_all_departments', 'eligible_departments', 'eligible_batch', 'eligible_year',
                  'registration_link', 'registration_deadline', 'drive_date']
        widgets = {
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'drive_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_role': forms.TextInput(attrs={'class': 'form-control'}),
            'package': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_cgpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Optional'}),
            'is_for_all_departments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'registration_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/register'}),
            'category': forms.Select(choices=[('A', 'Category A'), ('B', 'Category B'), ('C', 'Category C'), ('D', 'Category D')], attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import StudentProfile
        import datetime
        
        # 1. Get current year
        current_year = datetime.date.today().year
        
        # 2. Get batches from existing students
        db_batches = set(StudentProfile.objects.values_list('batch', flat=True).distinct().exclude(batch__isnull=True))
        
        # 3. Create a generous default range
        range_batches = set(range(current_year - 5, current_year + 4))
        
        # 4. Combine and sort
        all_batches = sorted(list(db_batches.union(range_batches)), reverse=True)
        
        # 5. Add 'All' option
        self.fields['eligible_batch'].choices = [(0, "All Batches")] + [(b, str(b)) for b in all_batches]
        self.fields['eligible_year'].choices = [(0, "All Years")] + [(i, f"Year {i}") for i in range(1, 5)]

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'message', 'target_type', 'drive']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_type': forms.Select(attrs={'class': 'form-control'}),
            'drive': forms.Select(attrs={'class': 'form-control'}),
        }


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['category', 'type', 'name', 'year']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bachelor of Technology (B.Tech.)'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Computer Science'}),
            'year': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'year': 'Course Duration (Years)',
        }
