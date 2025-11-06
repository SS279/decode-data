"""
URL Configuration for decode_data project
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('learning.urls')),  # Include learning app URLs
]