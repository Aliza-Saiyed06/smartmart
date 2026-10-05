"""
Views for the supermarket app.

A view receives a web request, does some work, and returns a web page.
Every view has @login_required, so only logged-in users can open it.
"""

import django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import ProtectedError, Sum
from django.shortcuts import redirect, render

from .forms import ProductForm
from .models import Category, Product


# ---------------------------------------------------------------
# Dashboard (temporary until Phase 12)
# ---------------------------------------------------------------
@login_required
def dashboard(request):
    """
    Temporary dashboard (Phase 3).

    It only checks that Django can talk to MySQL.
    The real dashboard with sales cards and low-stock alerts is built in Phase 12.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT VERSION()')
            mysql_version = cursor.fetchone()[0]
        database_ok = True
    except Exception:
        mysql_version = None
        database_ok = False

    context = {
        'django_version': django.get_version(),
        'database_ok': database_ok,
        'mysql_version': mysql_version,
        'database_name': connection.settings_dict['NAME'],
    }
    return render(request, 'dashboard.html', context)


# ---------------------------------------------------------------
# PRODUCTS: list (Read)
# ---------------------------------------------------------------
@login_required
def product_list(request):
    """
    Shows all products.
    Category filter -> done here on the server with the ORM  (?category=3)
    Text search and stock-status filter -> done in the browser by jQuery (static/js/filters.js)
    """
    products = Product.objects.select_related('category', 'supplier')

    selected_category = request.GET.get('category', '')
    if selected_category.isdigit():
        products = products.filter(category_id=int(selected_category))
    else:
        selected_category = ''

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'selected_category': selected_category,
    }
    return render(request, 'products/product_list.html', context)


# ---------------------------------------------------------------
# PRODUCTS: detail (Read one)
# ---------------------------------------------------------------
@login_required
def product_detail(request, pk):
    product = Product.objects.select_related('category', 'supplier').filter(pk=pk).first()
    if product is None:
        messages.error(request, 'Product not found. It may have been deleted.')
        return redirect('product_list')

    # Total units of this product sold so far (0 if never sold)
    total_sold = product.sale_items.aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'products/product_detail.html', {
        'product': product,
        'total_sold': total_sold,
    })


# ---------------------------------------------------------------
# PRODUCTS: create
# ---------------------------------------------------------------
@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():                      # runs ALL server-side validation
            product = form.save()
            messages.success(request, f'Product "{product.name}" was added successfully.')
            return redirect('product_list')      # redirect after POST: avoids double-submit on refresh
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {
        'form': form,
        'page_title': 'Add Product',
        'is_edit': False,
    })


# ---------------------------------------------------------------
# PRODUCTS: update
# ---------------------------------------------------------------
@login_required
def product_update(request, pk):
    product = Product.objects.filter(pk=pk).first()
    if product is None:
        messages.error(request, 'Product not found. It may have been deleted.')
        return redirect('product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)   # instance= means "edit this one"
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" was updated.')
            return redirect('product_detail', pk=product.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product,
        'page_title': 'Edit Product',
        'is_edit': True,
    })


# ---------------------------------------------------------------
# PRODUCTS: delete
# ---------------------------------------------------------------
@login_required
def product_delete(request, pk):
    product = Product.objects.filter(pk=pk).first()
    if product is None:
        messages.error(request, 'Product not found. It may have been deleted.')
        return redirect('product_list')

    if request.method == 'POST':
        product_name = product.name
        try:
            product.delete()
        except ProtectedError:
            # The product is used in past sales (SaleItem uses on_delete=PROTECT).
            messages.error(
                request,
                f'"{product_name}" cannot be deleted because it appears in past sales. '
                'Set its stock to 0 instead.'
            )
            return redirect('product_detail', pk=pk)

        messages.success(request, f'Product "{product_name}" was deleted.')
        return redirect('product_list')

    # GET request: show the "Are you sure?" page
    return render(request, 'products/product_confirm_delete.html', {'product': product})