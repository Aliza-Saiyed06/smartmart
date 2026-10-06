"""
Billing logic: turns a cart into a saved Sale with SaleItems and reduced stock.

The browser sends only product IDs and quantities (as JSON text).
Prices are ALWAYS read from the database here, never trusted from the browser.
"""

import json
from decimal import Decimal

from django.db import transaction

from .models import Customer, InsufficientStockError, Product, Sale, SaleItem


class BillingError(Exception):
    """A problem with the bill whose message is safe to show to the cashier."""


def parse_cart(cart_json):
    """
    Converts the JSON text from the browser into {product_id: quantity}.
    Example input:  '[{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]'
    The same product appearing twice is merged into one line.
    """
    try:
        raw_items = json.loads(cart_json)
    except (TypeError, ValueError):
        raise BillingError('The cart data was invalid. Please try again.')

    if not isinstance(raw_items, list) or len(raw_items) == 0:
        raise BillingError('The cart is empty. Add at least one product.')

    quantities = {}
    for entry in raw_items:
        try:
            product_id = int(entry['product_id'])
            quantity = int(entry['quantity'])
        except (KeyError, TypeError, ValueError):
            raise BillingError('The cart contains an invalid item.')

        if quantity < 1:
            raise BillingError('Quantity must be at least 1.')

        quantities[product_id] = quantities.get(product_id, 0) + quantity

    return quantities


def create_sale(cart_json, payment_method, customer_id=''):
    """
    Saves one bill. Returns the new Sale.
    Raises BillingError (with a friendly message) if anything is wrong.
    """
    # ---------- 1. Check the input ----------
    quantities = parse_cart(cart_json)

    valid_methods = [code for code, label in Sale.PAYMENT_CHOICES]
    if payment_method not in valid_methods:
        raise BillingError('Please select a valid payment method.')

    customer = None
    if customer_id:                                   # empty = walk-in customer
        if not str(customer_id).isdigit():
            raise BillingError('The selected customer was not found.')
        customer = Customer.objects.filter(pk=int(customer_id)).first()
        if customer is None:
            raise BillingError('The selected customer was not found. They may have been deleted.')

    # ---------- 2. Save everything or nothing ----------
    try:
        with transaction.atomic():
            # select_for_update() locks these product rows until the transaction ends,
            # so two cashiers cannot sell the last unit at the same moment.
            locked_products = (
                Product.objects.select_for_update()
                .filter(pk__in=quantities.keys())
                .order_by('pk')
            )
            product_map = {product.pk: product for product in locked_products}

            if len(product_map) != len(quantities):
                raise BillingError('A product in the cart no longer exists. Please rebuild the bill.')

            sale = Sale.objects.create(customer=customer, payment_method=payment_method)

            total = Decimal('0.00')
            for product_id, quantity in quantities.items():
                product = product_map[product_id]
                product.reduce_stock(quantity)        # raises InsufficientStockError if too few
                line = SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    price=product.price,              # price snapshot from the DATABASE
                )
                total += line.subtotal                # subtotal = price x quantity (set in SaleItem.save)

            sale.total_amount = total
            sale.save(update_fields=['total_amount'])

    except InsufficientStockError as error:
        # Leaving the atomic block with an exception undoes every change made inside it.
        raise BillingError(f'Not enough stock: {error}')

    return sale