"""
Database models for SmartMart.

Each class below becomes one table in MySQL.
Each attribute (models.CharField, etc.) becomes one column.

Relationships:
    Category  1 --- many  Product
    Supplier  1 --- many  Product
    Customer  1 --- many  Sale      (customer is optional: walk-in customers)
    Sale      1 --- many  SaleItem
    Product   1 --- many  SaleItem
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class InsufficientStockError(Exception):
    """Raised when we try to sell more units than the product has in stock."""


# ---------------------------------------------------------------
# 1. CATEGORY
# ---------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = 'categories'   # admin shows "Categories", not "Categorys"
        ordering = ['name']

    def __str__(self):
        return self.name


# ---------------------------------------------------------------
# 2. SUPPLIER
# ---------------------------------------------------------------
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.company})'


# ---------------------------------------------------------------
# 3. PRODUCT
# ---------------------------------------------------------------
class Product(models.Model):
    # Constants for the three stock states (avoids typing the same text many times)
    IN_STOCK = 'IN_STOCK'
    LOW_STOCK = 'LOW_STOCK'
    OUT_OF_STOCK = 'OUT_OF_STOCK'

    name = models.CharField(max_length=150, unique=True)

    # on_delete=PROTECT: a category/supplier that still has products cannot be deleted.
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='products')

    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    quantity = models.PositiveIntegerField(default=0)        # current stock
    minimum_stock = models.PositiveIntegerField(default=10)  # alert level
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    # ----- Stock status (calculated every time, never stored) -----
    @property
    def stock_status(self):
        if self.quantity == 0:
            return self.OUT_OF_STOCK
        if self.quantity <= self.minimum_stock:
            return self.LOW_STOCK
        return self.IN_STOCK

    @property
    def status_label(self):
        """Text shown to the user."""
        labels = {
            self.IN_STOCK: 'In Stock',
            self.LOW_STOCK: 'Low Stock',
            self.OUT_OF_STOCK: 'Out of Stock',
        }
        return labels[self.stock_status]

    @property
    def status_badge(self):
        """Bootstrap colour classes: green / yellow / red."""
        classes = {
            self.IN_STOCK: 'bg-success',
            self.LOW_STOCK: 'bg-warning text-dark',
            self.OUT_OF_STOCK: 'bg-danger',
        }
        return classes[self.stock_status]

    @property
    def is_low_stock(self):
        return self.stock_status == self.LOW_STOCK

    @property
    def is_out_of_stock(self):
        return self.stock_status == self.OUT_OF_STOCK

    # ----- Stock changes (used by billing and restocking) -----
    def reduce_stock(self, units):
        """Decrease stock after a sale. Refuses if there is not enough stock."""
        if units <= 0:
            raise ValueError('Quantity must be at least 1.')
        if units > self.quantity:
            raise InsufficientStockError(
                f'Only {self.quantity} unit(s) of {self.name} in stock.'
            )
        self.quantity -= units
        self.save(update_fields=['quantity'])

    def add_stock(self, units):
        """Increase stock when new goods arrive from the supplier."""
        if units <= 0:
            raise ValueError('Quantity must be at least 1.')
        self.quantity += units
        self.save(update_fields=['quantity'])


# ---------------------------------------------------------------
# 4. CUSTOMER
# ---------------------------------------------------------------
class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, unique=True)   # no duplicate customers
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.phone})'


# ---------------------------------------------------------------
# 5. SALE (one bill)
# ---------------------------------------------------------------
class Sale(models.Model):
    CASH = 'CASH'
    UPI = 'UPI'
    CARD = 'CARD'
    PAYMENT_CHOICES = [
        (CASH, 'Cash'),
        (UPI, 'UPI'),
        (CARD, 'Card'),
    ]

    # null=True, blank=True: walk-in customers do not need to be registered.
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, null=True, blank=True, related_name='sales'
    )
    date = models.DateTimeField(default=timezone.now, db_index=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=4, choices=PAYMENT_CHOICES, default=CASH)

    class Meta:
        ordering = ['-date']   # newest sale first

    def __str__(self):
        return f'{self.bill_number} - Rs. {self.total_amount}'

    @property
    def bill_number(self):
        """Bill number shown on the receipt, e.g. SM00007."""
        return f'SM{self.id:05d}'


# ---------------------------------------------------------------
# 6. SALE ITEM (one line on a bill)
# ---------------------------------------------------------------
class SaleItem(models.Model):
    # CASCADE: if a sale is deleted, its lines are deleted too.
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    # Price at the moment of sale. Old bills stay correct even if the price changes later.
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        # The subtotal is always calculated here, so it can never be wrong.
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)