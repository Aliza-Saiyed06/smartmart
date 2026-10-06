"""
Forms for the supermarket app.

A Django form describes the fields of an HTML form and validates the data
on the SERVER (server-side validation). This is the validation that cannot be
bypassed, unlike JavaScript checks which a user can switch off.
"""

from datetime import date

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Customer, Product


# ---------------------------------------------------------------
# Helper: gives every form Bootstrap styling
# ---------------------------------------------------------------
class BootstrapFormMixin:
    """
    Add this before forms.ModelForm in a form's parent classes.
    - Adds the Bootstrap class (form-control / form-select) to every field.
    - Adds data-label, which our JavaScript uses in error messages.
    - After validation, marks fields that have errors with is-invalid (red border).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            else:
                css_class = 'form-control'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' ' + css_class).strip()
            field.widget.attrs.setdefault('data-label', field.label or name)

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    widget = self.fields[name].widget
                    widget.attrs['class'] = widget.attrs.get('class', '') + ' is-invalid'


# ---------------------------------------------------------------
# Login form (from Phase 5)
# ---------------------------------------------------------------
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


# ---------------------------------------------------------------
# Product form (Phase 6)
# ---------------------------------------------------------------
class ProductForm(BootstrapFormMixin, forms.ModelForm):
    """Used for both 'Add product' and 'Edit product'."""

    class Meta:
        model = Product
        fields = ['name', 'category', 'supplier', 'price',
                  'quantity', 'minimum_stock', 'expiry_date']

        labels = {
            'name': 'Product name',
            'quantity': 'Quantity in stock',
            'minimum_stock': 'Minimum stock level',
            'expiry_date': 'Expiry date',
        }
        help_texts = {
            'minimum_stock': 'A LOW STOCK alert appears when stock is at or below this number.',
            'expiry_date': 'Optional. Leave blank for non-perishable items.',
        }
        widgets = {
            'price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'min': '0', 'step': '1', 'data-integer': 'true'}),
            'minimum_stock': forms.NumberInput(attrs={'min': '0', 'step': '1', 'data-integer': 'true'}),
            'expiry_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
        error_messages = {
            'name': {'unique': 'A product with this name already exists.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Select category'
        self.fields['supplier'].empty_label = 'Select supplier'

        # For a NEW product, the browser should also reject past expiry dates.
        # (data-no-past is read by static/js/validation.js)
        if not self.instance.pk:
            self.fields['expiry_date'].widget.attrs['data-no-past'] = 'true'

    # ----- Server-side validation: clean_<fieldname> methods -----
    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Product name must have at least 2 characters.')
        return name

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('Price must be greater than zero.')
        return price

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data['expiry_date']
        # Only reject past dates when adding a new product.
        # (When editing an old, already-expired product we must still be able to save it.)
        if expiry_date and not self.instance.pk and expiry_date < date.today():
            raise forms.ValidationError('Expiry date cannot be in the past.')
        return expiry_date

# ---------------------------------------------------------------
# Restock form (Phase 7)
# ---------------------------------------------------------------
class RestockForm(BootstrapFormMixin, forms.Form):
    """
    One field: how many units arrived from the supplier.
    This is a plain Form (not a ModelForm) because we do not create or edit
    a whole product, we only add a number to its stock.
    """

    quantity = forms.IntegerField(
        label='Quantity received',
        min_value=1,
        max_value=100000,
        widget=forms.NumberInput(attrs={
            'min': '1',
            'max': '100000',
            'step': '1',
            'data-integer': 'true',
            'placeholder': 'e.g. 50',
        }),
        error_messages={
            'required': 'Please enter the quantity received.',
            'invalid': 'Quantity must be a whole number.',
            'min_value': 'Quantity must be at least 1.',
            'max_value': 'Quantity cannot be more than 100000.',
        },
    )

    # ---------------------------------------------------------------
# Customer form (Phase 9)
# ---------------------------------------------------------------
class CustomerForm(BootstrapFormMixin, forms.ModelForm):
    """Used for both 'Add customer' and 'Edit customer'."""

    class Meta:
        model = Customer
        fields = ['name', 'phone', 'email']
        labels = {
            'name': 'Customer name',
            'phone': 'Phone number',
            'email': 'Email',
        }
        help_texts = {
            'phone': '10-digit mobile number starting with 6, 7, 8 or 9.',
            'email': 'Optional.',
        }
        widgets = {
            # pattern + data-pattern-message are read by static/js/validation.js
            'phone': forms.TextInput(attrs={
                'pattern': '[6-9][0-9]{9}',
                'data-pattern-message': 'Enter a valid 10-digit mobile number starting with 6, 7, 8 or 9.',
                'maxlength': '10',
                'inputmode': 'numeric',
                'placeholder': 'e.g. 9876543210',
            }),
            'email': forms.EmailInput(attrs={'placeholder': 'name@example.com'}),
        }
        error_messages = {
            # The database has unique=True on phone, so Django checks duplicates for us
            'phone': {'unique': 'A customer with this phone number already exists.'},
        }

    # ----- Server-side validation -----
    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Name must have at least 2 characters.')
        return name

    def clean_phone(self):
        # Remove spaces and dashes the user may have typed: "98765 43210" -> "9876543210"
        phone = self.cleaned_data['phone'].replace(' ', '').replace('-', '')
        if not phone.isdigit() or len(phone) != 10 or phone[0] not in '6789':
            raise forms.ValidationError(
                'Enter a valid 10-digit mobile number starting with 6, 7, 8 or 9.'
            )
        return phone