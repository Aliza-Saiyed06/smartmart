"""
Forms for the supermarket app.

A Django form describes the fields of an HTML form and validates the data
on the SERVER. More forms (product, customer, supplier) come in later phases.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm


class SmartMartLoginForm(AuthenticationForm):
    """Django's login form with Bootstrap styling and a friendly error message."""

    error_messages = {
        'invalid_login': 'Incorrect username or password. Please try again.',
        'inactive': 'This account is disabled. Please contact the administrator.',
    }

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )