"""
Views for the supermarket app.

A view receives a web request, does some work, and returns a web page.
Every view has @login_required, so only logged-in users can open it.
"""

from datetime import date, timedelta

import django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.db.models import Count, ProtectedError, Sum
from django.shortcuts import redirect, render

from .billing_logic import BillingError, create_sale, parse_cart
from .forms import CustomerForm, ProductForm, RestockForm, SupplierForm
from .inventory import low_stock_products, out_of_stock_products, stock_summary
from .models import Category, Customer, Product, Sale, Supplier

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


# ---------------------------------------------------------------
# INVENTORY: overview page (Phase 7)
# ---------------------------------------------------------------
@login_required
def inventory_list(request):
    """
    Stock overview: summary cards, 'needs attention' lists and the full stock table.
    Search and status filtering happen in the browser (jQuery, filters.js).
    """
    today = date.today()

    context = {
        'products': Product.objects.select_related('category', 'supplier'),
        'summary': stock_summary(),
        'low_stock_products': low_stock_products(),
        'out_of_stock_products': out_of_stock_products(),
        'restock_form': RestockForm(),
        'today': today,
        'expiry_soon': today + timedelta(days=7),   # "expiring soon" = within 7 days
    }
    return render(request, 'inventory/inventory_list.html', context)


# ---------------------------------------------------------------
# INVENTORY: restock (increase stock)
# ---------------------------------------------------------------
@login_required
def inventory_restock(request, pk):
    """
    Adds newly received units to a product's stock.
    Only POST is accepted; the form lives in a modal on the inventory page.
    """
    product = Product.objects.filter(pk=pk).first()
    if product is None:
        messages.error(request, 'Product not found. It may have been deleted.')
        return redirect('inventory_list')

    if request.method != 'POST':
        return redirect('inventory_list')

    form = RestockForm(request.POST)
    if form.is_valid():                              # server-side validation
        units = form.cleaned_data['quantity']
        product.add_stock(units)                     # method from models.py (Phase 4)
        messages.success(
            request,
            f'Added {units} unit(s) to "{product.name}". New stock: {product.quantity}.'
        )
    else:
        error_text = form.errors['quantity'][0]
        messages.error(request, f'Restock failed for "{product.name}": {error_text}')

    return redirect('inventory_list')


# ---------------------------------------------------------------
# BILLING (Phase 8)
# ---------------------------------------------------------------
def remember_cart(request, cart_json, payment_method, customer_id):
    """
    When a bill fails, keep the cashier's cart in the session so the page can
    show it again (otherwise a stock error would force them to retype everything).
    """
    try:
        quantities = parse_cart(cart_json)
        items = [{'product_id': pid, 'quantity': qty} for pid, qty in quantities.items()]
    except BillingError:
        items = []

    request.session['saved_cart'] = {
        'items': items,
        'payment_method': payment_method,
        'customer': customer_id,
    }


@login_required
def billing_page(request):
    """
    GET  -> shows the billing screen (product picker + cart).
    POST -> saves the bill, then redirects to the receipt.
    """
    if request.method == 'POST':
        cart_json = request.POST.get('cart_data', '')
        payment_method = request.POST.get('payment_method', '')
        customer_id = request.POST.get('customer', '')

        try:
            sale = create_sale(cart_json, payment_method, customer_id)
        except BillingError as error:
            messages.error(request, str(error))
            remember_cart(request, cart_json, payment_method, customer_id)
            return redirect('billing')
        except DatabaseError:
            messages.error(
                request,
                'A database error occurred, so the bill was NOT saved. Please try again.'
            )
            remember_cart(request, cart_json, payment_method, customer_id)
            return redirect('billing')

        messages.success(request, f'Bill {sale.bill_number} generated. Stock has been updated.')
        return redirect('billing_receipt', pk=sale.pk)

    # GET: restore a cart saved after a failed attempt (pop = read it once, then forget it)
    saved = request.session.pop('saved_cart', {})

    context = {
        'products': Product.objects.select_related('category').order_by('name'),
        'categories': Category.objects.all(),
        'customers': Customer.objects.all(),
        'payment_choices': Sale.PAYMENT_CHOICES,
        'saved_items': saved.get('items', []),
        'selected_payment': saved.get('payment_method') or Sale.CASH,
        'selected_customer': str(saved.get('customer', '')),
    }
    return render(request, 'billing/billing.html', context)


@login_required
def billing_receipt(request, pk):
    sale = Sale.objects.select_related('customer').filter(pk=pk).first()
    if sale is None:
        messages.error(request, 'Bill not found.')
        return redirect('billing')

    items = list(sale.items.select_related('product'))

    return render(request, 'billing/receipt.html', {
        'sale': sale,
        'items': items,
        'total_units': sum(item.quantity for item in items),
    })


# ---------------------------------------------------------------
# CUSTOMERS (Phase 9)
# ---------------------------------------------------------------
@login_required
def customer_list(request):
    """
    All customers, each with the number of bills and the total amount spent.
    annotate() adds these two calculated columns to every customer
    using ONE database query (a GROUP BY), not one query per customer.
    Searching is done in the browser by jQuery (filters.js).
    """
    customers = Customer.objects.annotate(
        bill_count=Count('sales'),
        total_spent=Sum('sales__total_amount'),    # None if the customer has no sales
    )
    return render(request, 'customers/customer_list.html', {'customers': customers})


@login_required
def customer_detail(request, pk):
    """One customer's details and purchase history (Date, Bill Number, Amount)."""
    customer = Customer.objects.filter(pk=pk).first()
    if customer is None:
        messages.error(request, 'Customer not found. They may have been deleted.')
        return redirect('customer_list')

    sales = customer.sales.all()                    # related_name='sales' from Phase 4 (newest first)
    total_spent = sales.aggregate(total=Sum('total_amount'))['total'] or 0

    return render(request, 'customers/customer_detail.html', {
        'customer': customer,
        'sales': sales,
        'bill_count': sales.count(),
        'total_spent': total_spent,
    })


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" was added successfully.')
            return redirect('customer_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm()

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'page_title': 'Add Customer',
        'is_edit': False,
    })


@login_required
def customer_update(request, pk):
    customer = Customer.objects.filter(pk=pk).first()
    if customer is None:
        messages.error(request, 'Customer not found. They may have been deleted.')
        return redirect('customer_list')

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer "{customer.name}" was updated.')
            return redirect('customer_detail', pk=customer.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'customers/customer_form.html', {
        'form': form,
        'customer': customer,
        'page_title': 'Edit Customer',
        'is_edit': True,
    })


@login_required
def customer_delete(request, pk):
    customer = Customer.objects.filter(pk=pk).first()
    if customer is None:
        messages.error(request, 'Customer not found. They may have been deleted.')
        return redirect('customer_list')

    if request.method == 'POST':
        customer_name = customer.name
        try:
            customer.delete()
        except ProtectedError:
            # Sale.customer uses on_delete=PROTECT, so bills keep their customer.
            messages.error(
                request,
                f'"{customer_name}" cannot be deleted because they have bills in the sales history.'
            )
            return redirect('customer_detail', pk=pk)

        messages.success(request, f'Customer "{customer_name}" was deleted.')
        return redirect('customer_list')

    return render(request, 'customers/customer_confirm_delete.html', {
        'customer': customer,
        'bill_count': customer.sales.count(),
    })

# ---------------------------------------------------------------
# SUPPLIERS (Phase 10)
# ---------------------------------------------------------------
@login_required
def supplier_list(request):
    """
    All suppliers, each with the number of products they supply.
    annotate(Count('products')) uses related_name='products' from Phase 4
    and calculates every count in ONE query. Searching is done by jQuery (filters.js).
    """
    suppliers = Supplier.objects.annotate(product_count=Count('products'))
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})


@login_required
def supplier_detail(request, pk):
    """One supplier's details and the list of products they supply."""
    supplier = Supplier.objects.filter(pk=pk).first()
    if supplier is None:
        messages.error(request, 'Supplier not found. They may have been deleted.')
        return redirect('supplier_list')

    products = supplier.products.select_related('category')

    # Products from this supplier that are low or out of stock (needs a restock order)
    attention_count = sum(1 for product in products if product.stock_status != Product.IN_STOCK)

    return render(request, 'suppliers/supplier_detail.html', {
        'supplier': supplier,
        'products': products,
        'attention_count': attention_count,
    })


@login_required
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" was added successfully.')
            return redirect('supplier_list')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm()

    return render(request, 'suppliers/supplier_form.html', {
        'form': form,
        'page_title': 'Add Supplier',
        'is_edit': False,
    })


@login_required
def supplier_update(request, pk):
    supplier = Supplier.objects.filter(pk=pk).first()
    if supplier is None:
        messages.error(request, 'Supplier not found. They may have been deleted.')
        return redirect('supplier_list')

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier "{supplier.name}" was updated.')
            return redirect('supplier_detail', pk=supplier.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'suppliers/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'page_title': 'Edit Supplier',
        'is_edit': True,
    })


@login_required
def supplier_delete(request, pk):
    supplier = Supplier.objects.filter(pk=pk).first()
    if supplier is None:
        messages.error(request, 'Supplier not found. They may have been deleted.')
        return redirect('supplier_list')

    if request.method == 'POST':
        supplier_name = supplier.name
        try:
            supplier.delete()
        except ProtectedError:
            # Product.supplier uses on_delete=PROTECT, so products keep their supplier.
            messages.error(
                request,
                f'"{supplier_name}" cannot be deleted because they still supply products. '
                'Change the supplier of those products first.'
            )
            return redirect('supplier_detail', pk=pk)

        messages.success(request, f'Supplier "{supplier_name}" was deleted.')
        return redirect('supplier_list')

    return render(request, 'suppliers/supplier_confirm_delete.html', {
        'supplier': supplier,
        'product_count': supplier.products.count(),
    })