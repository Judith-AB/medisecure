from django.db import models
from django.contrib.auth.models import User
import bleach

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField(max_length=500)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # A03 - sanitize text fields on save
        self.reason = bleach.clean(self.reason, tags=[], strip=True)
        self.notes = bleach.clean(self.notes, tags=[], strip=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient.username} → Dr.{self.doctor.username} on {self.date}"