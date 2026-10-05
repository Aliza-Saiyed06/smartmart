"""
Demo data loader.

Run with:  python manage.py seed_demo_data

Right now it creates only the categories and suppliers.
In later phases we will extend it with products and sales history.
It is safe to run more than once (get_or_create avoids duplicates).
"""

from django.core.management.base import BaseCommand

from supermarket.models import Category, Supplier

CATEGORY_NAMES = [
    'Dairy',
    'Grocery',
    'Bakery',
    'Snacks',
    'Beverages',
    'Personal Care',
    'Household',
    'Fruits & Vegetables',
]

# (name, company, phone, email, address)
SUPPLIERS = [
    ('Ramesh Patel', 'Sumul Dairy Distributors', '9876500001', 'ramesh@sumuldist.example.com', 'Ring Road, Surat'),
    ('Anil Shah', 'Shah Wholesale Grocers', '9876500002', 'anil@shahgrocers.example.com', 'Varachha Road, Surat'),
    ('Meena Desai', 'Desai Bakery Supplies', '9876500003', 'meena@desaibakery.example.com', 'Adajan, Surat'),
    ('Kiran Mehta', 'Mehta FMCG Traders', '9876500004', 'kiran@mehtafmcg.example.com', 'Udhna, Surat'),
    ('Suresh Joshi', 'Joshi Fresh Produce', '9876500005', 'suresh@joshifresh.example.com', 'APMC Market, Surat'),
]


class Command(BaseCommand):
    help = 'Loads demo categories and suppliers into the database.'

    def handle(self, *args, **options):
        for name in CATEGORY_NAMES:
            category, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'Created category: {category.name}')

        for name, company, phone, email, address in SUPPLIERS:
            supplier, created = Supplier.objects.get_or_create(
                name=name,
                company=company,
                defaults={'phone': phone, 'email': email, 'address': address},
            )
            if created:
                self.stdout.write(f'Created supplier: {supplier.name}')

        self.stdout.write(self.style.SUCCESS('Demo categories and suppliers are ready.'))