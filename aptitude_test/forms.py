from django import forms
from .models import PDFTest

class PDFTestForm(forms.ModelForm):
    answer_key_input = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': '1:B, 2:C, 3:A, 4:D ...'}),
        help_text="Format: QuestionNumber:Option, QuestionNumber:Option. Example: 1:A, 2:B"
    )

    class Meta:
        model = PDFTest
        fields = ['title', 'description', 'pdf_file', 'duration_minutes', 'target_type', 'target_department', 'target_drive']
        widgets = {
            'target_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleTargetFields(this)'}),
            'target_department': forms.Select(attrs={'class': 'form-select'}),
            'target_drive': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_answer_key_input(self):
        # Validate format
        data = self.cleaned_data['answer_key_input']
        valid_items = []
        try:
            items = [item.strip() for item in data.split(',')]
            for item in items:
                if ':' not in item:
                    raise forms.ValidationError(f"Invalid format in item '{item}'. Must be Number:Option (e.g. 1:A)")
                parts = item.split(':')
                if len(parts) != 2:
                    raise forms.ValidationError(f"Invalid item '{item}'")
                
                q_num = parts[0].strip()
                opt = parts[1].strip().upper()
                
                if not q_num.isdigit():
                    raise forms.ValidationError(f"Question number '{q_num}' must be an integer.")
                if opt not in ['A', 'B', 'C', 'D']:
                    raise forms.ValidationError(f"Option '{opt}' must be A, B, C, or D.")
                
                valid_items.append(f"{q_num}:{opt}")
        except Exception as e:
            raise forms.ValidationError(f"Error parsing answer key: {str(e)}")
        
        return ",".join(valid_items)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.answer_key = self.cleaned_data['answer_key_input']
        if commit:
            instance.save()
        return instance
