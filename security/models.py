from django.db import models
from django.contrib.auth.models import User

class SecurityLog(models.Model):
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Login Success'),
        ('LOGIN_FAILED', 'Login Failed'),
        ('LOGOUT', 'Logout'),
        ('REGISTER', 'Registration'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('BRUTE_FORCE', 'Brute Force Attempt'),
        ('XSS_ATTEMPT', 'XSS Attempt'),
        ('SQLI_ATTEMPT', 'SQLi Attempt'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('FILE_UPLOAD_BLOCKED', 'File Upload Blocked'),
        ('SSRF_ATTEMPT', 'SSRF Attempt'),
        ('CSRF_ATTEMPT', 'CSRF Attempt'),
        ('SUSPICIOUS', 'Suspicious Activity'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    path = models.CharField(max_length=300, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_threat = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.event_type}] {self.description[:50]} @ {self.timestamp}"

    @classmethod
    def log(cls, request, event_type, description, is_threat=False):
        """Helper to log from anywhere in the app"""
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        if not ip:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        cls.objects.create(
            user=request.user if request.user.is_authenticated else None,
            event_type=event_type,
            description=description,
            ip_address=ip or '127.0.0.1',
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
            path=request.path[:300],
            is_threat=is_threat,
        )