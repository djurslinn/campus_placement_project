from django import forms
from core.models import PlacementDrive
from .models import MockInterviewEvaluation, MockInterviewSession


class GenerateSessionForm(forms.Form):
    """Coordinator form to kick off a new session."""
    label      = forms.CharField(
        max_length=120, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Week-3 Practice', 'class': 'form-input'}),
        label='Session Label (optional)',
    )
    target_type = forms.ChoiceField(
        choices=MockInterviewSession.TARGET_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleTargetFields(this)'}),
        label='Target Audience',
        initial='everyone'
    )
    department = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Specific Department',
    )
    year       = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Filter by Year',
    )
    target_drive = forms.ModelChoiceField(
        queryset=PlacementDrive.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Specific Placement Drive'
    )

    def __init__(self, *args, departments=None, years=None, **kwargs):
        super().__init__(*args, **kwargs)
        dept_choices = [('', 'All Departments')]
        if departments:
            dept_choices += [(d.id, str(d)) for d in departments]
        self.fields['department'].widget.choices = dept_choices

        year_choices = [('', 'All Years')]
        if years:
            year_choices += [(y, f'Year {y}') for y in sorted(years)]
        self.fields['year'].widget.choices = year_choices


SCORE_WIDGET = forms.NumberInput(attrs={'min': 1, 'max': 10, 'step': '0.5', 'class': 'score-input'})


class EvaluationForm(forms.ModelForm):
    class Meta:
        model  = MockInterviewEvaluation
        fields = ['communication', 'confidence', 'technical',
                  'body_language', 'problem_solving', 'feedback']
        widgets = {
            'communication':   SCORE_WIDGET,
            'confidence':      SCORE_WIDGET,
            'technical':       SCORE_WIDGET,
            'body_language':   SCORE_WIDGET,
            'problem_solving': SCORE_WIDGET,
            'feedback': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea',
                'placeholder': 'Write your honest feedback for your partner…',
            }),
        }
        labels = {
            'communication':   'Communication (1-10)',
            'confidence':      'Confidence (1-10)',
            'technical':       'Technical Knowledge (1-10)',
            'body_language':   'Body Language (1-10)',
            'problem_solving': 'Problem Solving (1-10)',
            'feedback':        'Written Feedback',
        }

    def clean(self):
        cleaned = super().clean()
        for field in ['communication', 'confidence', 'technical',
                      'body_language', 'problem_solving']:
            val = cleaned.get(field)
            if val is not None and not (1 <= float(val) <= 10):
                self.add_error(field, 'Score must be between 1 and 10.')
        return cleaned
