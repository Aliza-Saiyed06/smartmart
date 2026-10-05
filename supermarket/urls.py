"""
URLs for the supermarket app.

Each path() connects a web address to a view function.
"""

from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import SmartMartLoginForm

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Authentication (Django's built-in views)
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=SmartMartLoginForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Products (Phase 6)
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
]