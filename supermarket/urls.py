"""
URLs for the supermarket app.

Each path() connects a web address to a view function.
We will add more paths here in every phase.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import SmartMartLoginForm

urlpatterns = [
    # Dashboard (protected: see views.py)
    path('', views.dashboard, name='dashboard'),

    # Authentication: Django's built-in views, so we write no login logic ourselves
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=SmartMartLoginForm,
            redirect_authenticated_user=True,   # already logged in? skip the login page
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]