"""
Main URL configuration for SmartMart.

Every request first arrives here. We send:
  /admin/  -> Django's built-in admin site
  anything else -> the URLs defined in the supermarket app
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('supermarket.urls')),
]