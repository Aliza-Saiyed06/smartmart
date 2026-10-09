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

    # Inventory (Phase 7)
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/<int:pk>/restock/', views.inventory_restock, name='inventory_restock'),

    # Billing (Phase 8)
    path('billing/', views.billing_page, name='billing'),
    path('billing/receipt/<int:pk>/', views.billing_receipt, name='billing_receipt'),

    # Customers (Phase 9)
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/edit/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Suppliers (Phase 10)
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
]