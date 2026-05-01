from django import forms
from .models import MedicalRecord
from django.contrib.auth.models import User
import bleach
import magic

ALLOWED_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

class MedicalRecordForm(forms.ModelForm):
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='patient'),
        empty_label="Select Patient",
    )

    class Meta:
        model = MedicalRecord
        fields = ['patient', 'title', 'diagnosis', 'prescription', 'notes', 'attachment']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 4, 'maxlength': 2000}),
            'prescription': forms.Textarea(attrs={'rows': 3, 'maxlength': 1000}),
            'notes': forms.Textarea(attrs={'rows': 3, 'maxlength': 1000}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        # A03 - sanitize
        return bleach.clean(title, tags=[], strip=True)

    def clean_diagnosis(self):
        diagnosis = self.cleaned_data.get('diagnosis', '')
        diagnosis = bleach.clean(diagnosis, tags=[], strip=True)
        if len(diagnosis.strip()) < 10:
            raise forms.ValidationError("Diagnosis must be at least 10 characters.")
        return diagnosis

    def clean_attachment(self):
        file = self.cleaned_data.get('attachment')
        if file:
            # A08 - check real MIME type using magic, not just extension
            mime = magic.from_buffer(file.read(1024), mime=True)
            file.seek(0)
            if mime not in ALLOWED_MIME_TYPES:
                raise forms.ValidationError(
                    f"File type '{mime}' not allowed. Only JPG, PNG, PDF accepted."
                )
            if file.size > MAX_FILE_SIZE:
                raise forms.ValidationError("File must be under 5MB.")
            # A08 - force safe filename
            import os
            ext_map = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'application/pdf': '.pdf',
            }
            file.name = f"record_{file.name[:20]}{ext_map.get(mime, '.bin')}"
        return file