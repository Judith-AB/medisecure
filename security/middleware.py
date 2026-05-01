from .models import SecurityLog
import re

# A03 - patterns to detect SQLi and XSS attempts
SQLI_PATTERNS = [
    r"(\'|\"|;|--|\bOR\b|\bAND\b|\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\bEXEC\b)",
]
XSS_PATTERNS = [
    r"(<script|</script|javascript:|onerror=|onload=|<img|<svg|alert\(|document\.cookie)",
]

class SecurityLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.sqli_re = re.compile('|'.join(SQLI_PATTERNS), re.IGNORECASE)
        self.xss_re = re.compile('|'.join(XSS_PATTERNS), re.IGNORECASE)

    def __call__(self, request):
        self._scan_request(request)
        response = self.get_response(request)
        return response

    def _scan_request(self, request):
        # Scan all GET and POST params for attack patterns
        all_values = list(request.GET.values()) + list(request.POST.values())
        for value in all_values:
            if self.sqli_re.search(str(value)):
                SecurityLog.log(
                    request,
                    'SQLI_ATTEMPT',
                    f"Possible SQLi detected in input: {str(value)[:100]}",
                    is_threat=True
                )
            if self.xss_re.search(str(value)):
                SecurityLog.log(
                    request,
                    'XSS_ATTEMPT',
                    f"Possible XSS detected in input: {str(value)[:100]}",
                    is_threat=True
                )