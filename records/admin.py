from django.contrib import admin
from .models import MedicalRecord

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'doctor', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'patient__username', 'doctor__username']