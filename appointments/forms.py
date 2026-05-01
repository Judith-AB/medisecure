from django import forms
from django.contrib.auth.models import User
from .models import Appointment
from accounts.models import UserProfile
import bleach
import re
from datetime import date

class BookAppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='doctor'),
        empty_label="Select a Doctor",
    )

    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'reason': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your symptoms or reason for visit...',
                'maxlength': 500,
            }),
        }

    def clean_reason(self):
        reason = self.cleaned_data.get('reason', '')
        # A03 - strip all HTML tags (XSS prevention)
        reason = bleach.clean(reason, tags=[], strip=True)
        if len(reason.strip()) < 10:
            raise forms.ValidationError("Please describe your reason in at least 10 characters.")
        return reason

    def clean_date(self):
        appt_date = self.cleaned_data.get('date')
        if appt_date and appt_date < date.today():
            raise forms.ValidationError("Appointment date cannot be in the past.")
        return appt_date

    def clean_doctor(self):
        doctor = self.cleaned_data.get('doctor')
        if doctor:
            try:
                if not doctor.profile.is_doctor():
                    raise forms.ValidationError("Selected user is not a doctor.")
            except UserProfile.DoesNotExist:
                raise forms.ValidationError("Invalid doctor selection.")
        return doctor

class UpdateAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'maxlength': 500}),
        }

    def clean_notes(self):
        notes = self.cleaned_data.get('notes', '')
        return bleach.clean(notes, tags=[], strip=True)