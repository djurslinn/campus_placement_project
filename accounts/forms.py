from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import User, Course

class CourseChoiceField(forms.ModelChoiceField):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            try:
                # Handle ModelChoiceIteratorValue or raw string/int PK
                pk = value.value if hasattr(value, 'value') else value
                course_obj = self.queryset.get(pk=pk)
                option['attrs']['data-duration'] = course_obj.year
            except:
                pass
        return option

class StudentRegistrationForm(UserCreationForm):
    """
    Registration form for students
    """
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    course = CourseChoiceField(queryset=Course.objects.all(), required=True, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    year = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(1, 5)], widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    batch = forms.ChoiceField(choices=[(str(i), str(i)) for i in range(2020, 2031)], widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'course', 'year', 'batch', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        year_val = cleaned_data.get('year')
        batch_val = cleaned_data.get('batch')
        
        if course and year_val:
            year = int(year_val)
            if year > course.year:
                self.add_error('year', f"This course only has {course.year} years. You cannot select year {year}.")
            
            if batch_val:
                batch = int(batch_val)
                current_yr = timezone.now().year
                # Logical check: Admission Year + (Year of Study - 1) = Academic Year
                # Allowing some leeway (2 years) for different academic cycles/gaps
                academic_cycle_yr = batch + year - 1
                if abs(academic_cycle_yr - current_yr) > 2:
                    self.add_error('batch', f"Conflict between batch ({batch}) and year of study ({year}). A student in year {year} who started in {batch} should be in academic year {academic_cycle_yr}, not {current_yr}.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.department = self.cleaned_data['course']
        user.role = 'student'
        if commit:
            user.save()
            from .models import StudentProfile
            import random
            roll_no = f"STU{random.randint(1000, 9999)}"
            StudentProfile.objects.create(
                user=user,
                year=int(self.cleaned_data['year']),
                batch=int(self.cleaned_data['batch']),
                roll_no=roll_no,
                phone="" # Will be updated in profile
            )
        return user


class CoordinatorRegistrationForm(UserCreationForm):
    """
    Registration form for coordinators
    """
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm Password'
    }))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = 'coordinator'
        if commit:
            user.save()
        return user


from .models import StudentProfile

class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = StudentProfile
        fields = ['first_name', 'last_name', 'roll_no', 'gender', 'age', 'year', 'batch', 'phone', 'cgpa', 'backlogs', 'linkedin_url', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'roll_no': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'year': forms.Select(choices=[(i, str(i)) for i in range(1, 5)], attrs={'class': 'form-control'}),
            'batch': forms.Select(choices=[(i, str(i)) for i in range(2020, 2031)], attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'cgpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'backlogs': forms.NumberInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.instance and self.instance.user:
            user = self.instance.user
            user.first_name = self.cleaned_data.get('first_name')
            user.last_name = self.cleaned_data.get('last_name')
            if commit:
                user.save()
        if commit:
            profile.save()
        return profile

    def clean(self):
        cleaned_data = super().clean()
        year_val = cleaned_data.get('year')
        batch_val = cleaned_data.get('batch')
        
        # Access course duration through instance's user department
        if self.instance and hasattr(self.instance, 'user') and self.instance.user.department:
            duration = self.instance.user.department.year
            if year_val and int(year_val) > duration:
                self.add_error('year', f"Your course ({self.instance.user.department.name}) only has {duration} years.")
        
        if year_val and batch_val:
            year = int(year_val)
            batch = int(batch_val)
            current_yr = timezone.now().year
            academic_cycle_yr = batch + year - 1
            if abs(academic_cycle_yr - current_yr) > 1:
                self.add_error('batch', f"Conflict between batch ({batch}) and current year of study ({year}). Logically, you should be in academic year {academic_cycle_yr}.")
        
        return cleaned_data

class CoordinatorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
