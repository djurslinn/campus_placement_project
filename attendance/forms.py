from django import forms
from .models import physicalSession, Attendance
from accounts.models import User

class SessionForm(forms.ModelForm):
    class Meta:
        model = physicalSession
        fields = ['title', 'description', 'date', 'time', 'location', 'target_type', 'department', 'target_drive']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter session title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter session description'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter location'}),
            'target_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_target_type'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'target_drive': forms.Select(attrs={'class': 'form-select'}),
        }
