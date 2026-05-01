from django.contrib import admin
from .models import SecurityLog

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'event_type', 'user', 'ip_address', 'is_threat', 'description']
    list_filter = ['event_type', 'is_threat']
    search_fields = ['description', 'user__username', 'ip_address']
    readonly_fields = ['timestamp']