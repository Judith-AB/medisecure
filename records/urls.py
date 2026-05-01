from django.urls import path
from . import views

urlpatterns = [
    path('', views.record_list, name='record_list'),
    path('<int:pk>/', views.record_detail, name='record_detail'),
    path('create/', views.create_record, name='create_record'),
    path('<int:pk>/delete/', views.delete_record, name='delete_record'),
]