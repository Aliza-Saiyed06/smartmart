"""
Registers our models in Django Admin (http://127.0.0.1:8000/admin/).

Admin is a backend tool for us. SmartMart's own pages (built in later phases)
are what the cashier and manager actually use.
"""

from django.contrib import admin

from .models import Category, Customer, Product, Sale, SaleItem, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'email')
    search_fields = ('name', 'company', 'phone')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'quantity', 'minimum_stock',
                    'status_label', 'expiry_date', 'supplier')
    list_filter = ('category', 'supplier')
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')


class SaleItemInline(admin.TabularInline):
    """Shows the bill's lines inside the Sale page."""
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'date', 'customer', 'total_amount', 'payment_method')
    list_filter = ('payment_method', 'date')
    inlines = [SaleItemInline]


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'price', 'subtotal')