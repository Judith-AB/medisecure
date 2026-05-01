from django.db import models
from django.contrib.auth.models import User
import bleach

class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_records')
    title = models.CharField(max_length=200)
    diagnosis = models.TextField()
    prescription = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    attachment = models.FileField(upload_to='records/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # A03 - sanitize all text fields
        self.title = bleach.clean(self.title, tags=[], strip=True)
        self.diagnosis = bleach.clean(self.diagnosis, tags=[], strip=True)
        self.prescription = bleach.clean(self.prescription, tags=[], strip=True)
        self.notes = bleach.clean(self.notes, tags=[], strip=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.patient.username}"