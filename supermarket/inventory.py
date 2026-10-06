"""
Inventory helper functions.

These return the low-stock and out-of-stock products using database queries.
The rules MUST match Product.stock_status in models.py:

    quantity == 0                          -> OUT OF STOCK
    0 < quantity <= minimum_stock          -> LOW STOCK
    quantity > minimum_stock               -> IN STOCK
"""

from django.db.models import F

from .models import Product


def low_stock_products():
    """Products that are running low but are not completely finished."""
    return (
        Product.objects
        .filter(quantity__gt=0, quantity__lte=F('minimum_stock'))   # F() compares two columns
        .select_related('category', 'supplier')
        .order_by('quantity')                                        # emptiest first
    )


def out_of_stock_products():
    """Products with zero stock."""
    return (
        Product.objects
        .filter(quantity=0)
        .select_related('category', 'supplier')
    )


def stock_summary():
    """Counts shown in the summary cards."""
    total = Product.objects.count()
    low = low_stock_products().count()
    out = out_of_stock_products().count()
    return {
        'total': total,
        'in_stock': total - low - out,
        'low': low,
        'out': out,
    }