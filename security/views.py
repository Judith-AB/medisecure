from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import SecurityLog
from django.db.models import Count

def require_admin(view_func):
    """Custom decorator - only admin role can access"""
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if not request.user.profile.is_admin():
                # A09 - log unauthorized access attempt
                SecurityLog.log(request, 'ACCESS_DENIED',
                    f"Non-admin tried to access security panel: {request.user.username}",
                    is_threat=True)
                messages.error(request, "Access denied. Admins only.")
                return redirect('dashboard')
        except:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@require_admin
def security_logs(request):
    logs = SecurityLog.objects.all()

    # Filter by event type
    event_filter = request.GET.get('event', '')
    if event_filter:
        logs = logs.filter(event_type=event_filter)

    threat_filter = request.GET.get('threats', '')
    if threat_filter == '1':
        logs = logs.filter(is_threat=True)

    paginator = Paginator(logs, 20)
    page = request.GET.get('page')
    logs = paginator.get_page(page)

    # Stats
    from django.db.models import Count
    stats = {
        'total': SecurityLog.objects.count(),
        'threats': SecurityLog.objects.filter(is_threat=True).count(),
        'logins_failed': SecurityLog.objects.filter(event_type='LOGIN_FAILED').count(),
        'xss': SecurityLog.objects.filter(event_type='XSS_ATTEMPT').count(),
        'sqli': SecurityLog.objects.filter(event_type='SQLI_ATTEMPT').count(),
        'locked': SecurityLog.objects.filter(event_type='ACCOUNT_LOCKED').count(),
    }

    return render(request, 'security/logs.html', {
        'logs': logs,
        'stats': stats,
        'event_types': SecurityLog.EVENT_TYPES,
        'event_filter': event_filter,
        'threat_filter': threat_filter,
    })

@login_required
@require_admin
def owasp_demo(request):
    """Live OWASP Top 10 demo panel"""
    return render(request, 'security/owasp_demo.html')