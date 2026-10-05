"""
URLs for the supermarket app.

Each path() connects a web address to a view function.
We will add more paths here in every phase.
"""

from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]