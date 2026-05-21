"""
Forms for resume builder and upload functionality
"""
from django import forms
from django.forms import formset_factory
from .models import Resume


class PersonalInfoForm(forms.Form):
    """Personal information form"""
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'john@example.com'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'})
    )
    linkedin = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/johndoe'})
    )
    github = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/johndoe'})
    )
    portfolio = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://johndoe.com'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'City, State, Country'})
    )


class SummaryForm(forms.Form):
    """Professional summary form"""
    summary = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Write a compelling professional summary highlighting your key skills and achievements...'
        })
    )


class EducationForm(forms.Form):
    """Education entry form"""
    degree = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'B.Tech in Computer Science'})
    )
    institution = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XYZ University'})
    )
    year = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2020 - 2024'})
    )
    cgpa = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '8.5/10'})
    )


class ExperienceForm(forms.Form):
    """Experience entry form"""
    role = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Software Engineer Intern'})
    )
    company = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ABC Tech Company'})
    )
    duration = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'June 2023 - August 2023'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your responsibilities and achievements...'
        })
    )


class ProjectForm(forms.Form):
    """Project entry form"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title'})
    )
    tech_stack = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, PostgreSQL'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe the project, its features, and your contributions...'
        })
    )
    github_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/user/project'})
    )


class SkillsForm(forms.Form):
    """Skills form"""
    technical_skills = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Python, Java, JavaScript, SQL, Django, React...'
        })
    )
    soft_skills = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Leadership, Communication, Problem Solving...'
        })
    )
    tools = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Git, Docker, VS Code, Jira...'
        })
    )


class CertificationForm(forms.Form):
    """Certification entry form"""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AWS Certified Developer'})
    )
    issuer = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Amazon Web Services'})
    )
    date = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'January 2024'})
    )


class LanguageForm(forms.Form):
    """Language entry form"""
    language = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'English'})
    )
    proficiency = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select Proficiency'),
            ('native', 'Native'),
            ('fluent', 'Fluent'),
            ('intermediate', 'Intermediate'),
            ('beginner', 'Beginner'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        lang = cleaned_data.get('language')
        prof = cleaned_data.get('proficiency')

        if lang and not prof:
            self.add_error('proficiency', 'Please select proficiency')
        elif prof and not lang:
            self.add_error('language', 'Please enter language')
        
        return cleaned_data


class AchievementForm(forms.Form):
    """Achievement entry form"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Place - Hackathon 2024'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Brief description of the achievement...'
        })
    )


class ResumeUploadForm(forms.Form):
    """Resume upload form"""
    resume_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf'
        }),
        help_text='Only PDF files accepted (Max size: 5MB)'
    )
    
    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file')
        
        if file:
            # Check file extension
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed')
            
            # Check file size (5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('File size exceeds 5MB limit')
        
        return file


# Create formsets for dynamic entries
EducationFormSet = formset_factory(EducationForm, extra=1, max_num=5, can_delete=True)
ExperienceFormSet = formset_factory(ExperienceForm, extra=1, max_num=5, can_delete=True)
ProjectFormSet = formset_factory(ProjectForm, extra=1, max_num=5, can_delete=True)
CertificationFormSet = formset_factory(CertificationForm, extra=1, max_num=10, can_delete=True)
LanguageFormSet = formset_factory(LanguageForm, extra=1, max_num=5, can_delete=True)
AchievementFormSet = formset_factory(AchievementForm, extra=1, max_num=10, can_delete=True)
