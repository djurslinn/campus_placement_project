from django import forms
from .models import GDSession, GDTopic
from accounts.models import StudentProfile

class GDSessionForm(forms.ModelForm):
    custom_topic = forms.CharField(max_length=255, required=True, label="GD Topic")
    num_groups = forms.IntegerField(min_value=1, initial=4, label="Number of Groups")
    
    # Optional filters for student selection
    department = forms.ChoiceField(choices=[('', 'All Departments')], required=False)
    year = forms.IntegerField(required=False, label="Batch/Year (Optional)")

    class Meta:
        model = GDSession
        fields = ['custom_topic', 'num_groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate department choices dynamically if needed
        depts = StudentProfile.objects.values_list('user__department__name', flat=True).distinct()
        self.fields['department'].choices += [(d, d) for d in depts if d]
