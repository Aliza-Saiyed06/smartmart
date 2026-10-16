"""
Restock recommendation: a simple, explainable, rule-based calculation.

    Average Daily Sales = units sold in the last N days / N
    Recommended Stock   = Average Daily Sales x Planning Days   (rounded UP)
    Restock Quantity    = Recommended Stock - Current Stock     (never below 0)

This is NOT machine learning. It only uses past sales and one multiplication.
"""

from datetime import date, datetime, time, timedelta

from django.db.models import Sum

from .models import Product, SaleItem


def units_sold_per_product(lookback_days):
    """
    Returns {product_id: units sold} for the last `lookback_days` days (today included).
    One query: GROUP BY product.
    """
    first_day = datetime.combine(date.today() - timedelta(days=lookback_days - 1), time.min)
    rows = (
        SaleItem.objects.filter(sale__date__gte=first_day)
        .values('product_id')
        .annotate(units=Sum('quantity'))
    )
    return {row['product_id']: row['units'] for row in rows}


def recommended_stock(units_sold, lookback_days, planning_days):
    """
    Average daily sales x planning days, rounded up.
    Written with whole numbers: ceil(a / b) is -(-a // b), so there are no
    floating-point surprises (10 / 3 * 3 must not become 10.000000000000002).
    """
    return -(-(units_sold * planning_days) // lookback_days)


def restock_quantity(recommended, current_stock):
    """How many units to order. Never negative."""
    return max(0, recommended - current_stock)


def build_recommendations(lookback_days, planning_days):
    """One dictionary per product, the products that need the most restocking first."""
    sold = units_sold_per_product(lookback_days)
    rows = []

    for product in Product.objects.select_related('category', 'supplier'):
        units = sold.get(product.id, 0)
        average = units / lookback_days
        recommended = recommended_stock(units, lookback_days, planning_days)
        to_order = restock_quantity(recommended, product.quantity)

        rows.append({
            'product': product,
            'units_sold': units,
            'average_daily': average,
            'recommended': recommended,
            'restock': to_order,
            'needs_restock': to_order > 0,
            # The calculation written out, so a user can follow it
            'explanation': (
                f'{average:.1f} per day × {planning_days} days = {recommended}; '
                f'{recommended} − {product.quantity} in stock = {to_order}'
                if to_order > 0 else
                f'{average:.1f} per day × {planning_days} days = {recommended}; '
                f'stock of {product.quantity} is enough'
            ),
        })

    rows.sort(key=lambda row: (-row['restock'], row['product'].name))
    return rows