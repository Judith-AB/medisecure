from django.urls import path
from . import views

urlpatterns = [
    path('logs/', views.security_logs, name='security_logs'),
    path('demo/', views.owasp_demo, name='owasp_demo'),
]