# SmartMart: Supermarket Management & Sales Analytics System

A web-based system for a small or medium supermarket. It joins products, stock, billing, customers, suppliers and sales into one application. When a bill is generated, stock drops automatically. When stock is low, an alert appears. A simple rule suggests how much to reorder.

*College project for **Open Source Technologies** (B.Tech CSE, Semester V).*

---

## 1. Problem statement

Small and medium supermarkets often rely on manual or disconnected methods for managing products, inventory, billing, customers and sales. This leads to stock inconsistencies, difficulty tracking sales, and late discovery of low-stock products. SmartMart provides one centralized web system that connects these operations, with automatic stock updates, low-stock alerts and restock recommendations.

## 2. Objectives

1. Build a centralized supermarket management system.
2. Manage products and inventory efficiently.
3. Automate billing and stock updates.
4. Keep customer and supplier records.
5. Identify best-selling products and categories.
6. Detect low-stock products automatically.
7. Give simple, explainable restock recommendations.
8. Demonstrate practical use of open-source technologies.

## 3. Features

| Module | What it does |
|---|---|
| **Login** | Django's built-in authentication. Every page requires login |
| **Dashboard** | Products, customers, suppliers, today's sales and orders, low and out-of-stock counts, items sold, best-selling product and category, 7-day sales trend, low-stock list |
| **Products** | Add, view, edit, delete. Search, category filter, stock-status filter |
| **Inventory** | Green / Yellow / Red status, low-stock and out-of-stock lists, restock form, expiry warnings |
| **Billing** | Product search, cart, quantity controls, live total, payment (Cash / UPI / Card), optional customer, printable receipt |
| **Customers** | Add, view, edit, delete, search, purchase history and total spent |
| **Suppliers** | Add, view, edit, delete, search, products supplied |
| **Sales** | List of all bills, search, date-range and payment filters, bill details |
| **Restock** | Rule-based recommendation with the calculation shown |

### Innovative features

- **Billing and inventory are connected.** A bill reduces stock in the same database transaction, so a bill is never half-saved.
- **Stock status is calculated, never stored,** so it cannot go out of date.
- **Explainable restock rule** (no machine learning):
  ```
  Average daily sales = units sold in last N days / N
  Recommended stock   = average daily sales x planning days   (rounded up)
  Restock quantity    = recommended stock - current stock     (never below 0)
  ```
- **The browser never decides prices.** It sends product IDs and quantities, and the server reads real prices from MySQL.
- **Works offline.** Bootstrap, jQuery and icons are stored in `static/vendor/`.

## 4. Technology stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, jQuery |
| Backend | Python, Django 5.2 |
| Database | MySQL (via `mysqlclient`) |
| Configuration | `python-dotenv` (`.env` file) |
| Tools | Git / GitHub, VS Code |

**Where each technology is used**

| Technology | Used for |
|---|---|
| HTML / CSS | All pages, `static/css/style.css` (theme, receipt, print styles) |
| Bootstrap | Responsive grid, sidebar (offcanvas), cards, tables, badges, modals, alerts |
| JavaScript | `billing.js` (cart and totals), `validation.js` (form validation) |
| jQuery | `filters.js` (live search and filters), restock modal, login page |
| Django | Models, views, forms, URLs, authentication, templates, admin |
| MySQL | All data |

## 5. System architecture

```
Browser (HTML, CSS, Bootstrap, JavaScript, jQuery)
        |  HTTP
        v
Django:  urls.py -> views.py -> forms.py -> models.py
        |   billing_logic.py   inventory.py   restock.py
        |  Django ORM
        v
MySQL: smartmart_db
```

## 6. Database design

Six tables, plus Django's own user tables.

```
Category 1---* Product *---1 Supplier
                  1
                  |
                  *
Customer 1---* Sale 1---* SaleItem *---1 Product
   (optional)
```

| Table | Main fields |
|---|---|
| `Category` | name |
| `Supplier` | name, company, phone, email, address |
| `Product` | name, category, supplier, price, quantity, minimum_stock, expiry_date |
| `Customer` | name, phone (unique), email |
| `Sale` | customer (optional), date, total_amount, payment_method |
| `SaleItem` | sale, product, quantity, price, subtotal |

**Design decisions**

- `Sale.customer` is optional, because walk-in customers are not registered.
- `SaleItem.price` copies the product price at sale time, so old bills stay correct if the price changes.
- `on_delete=PROTECT` stops deleting a product, customer, supplier or category that other records depend on. This protects sales history.
- Stock status is a `@property`, calculated from `quantity` and `minimum_stock`:

| Condition | Status |
|---|---|
| quantity = 0 | Out of stock (red) |
| 0 < quantity <= minimum stock | Low stock (yellow) |
| quantity > minimum stock | In stock (green) |

## 7. Project structure

```
smartmart/
├── manage.py
├── requirements.txt
├── .env.example            # placeholders only (committed)
├── .env                    # real secrets (NEVER committed)
├── smartmart/              # project settings and root URLs
├── supermarket/            # the application
│   ├── models.py           # six models, stock rules
│   ├── forms.py            # forms and server-side validation
│   ├── views.py            # all pages
│   ├── urls.py
│   ├── billing_logic.py    # saves a bill in one transaction
│   ├── inventory.py        # low-stock queries
│   ├── restock.py          # restock rule
│   ├── admin.py
│   ├── migrations/
│   └── management/commands/seed_demo_data.py
├── templates/              # base.html, 404.html, 500.html, one folder per module
└── static/
    ├── css/style.css
    ├── js/                 # billing.js, validation.js, filters.js
    └── vendor/             # Bootstrap, jQuery, Bootstrap Icons (local copies)
```

## 8. Installation (Windows, PowerShell)

### Requirements

- Python 3.12 recommended (3.10 or newer works)
- MySQL Server 8.x
- Git

### Steps

**1. Clone and enter the project folder** (the one containing `manage.py`)

```powershell
git clone <repository-url>
cd <folder-with-manage.py>
```

**2. Create the virtual environment and install packages**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the script, run once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

**3. Create the MySQL database and user** (in the MySQL client, as root)

```sql
CREATE DATABASE smartmart_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'smartmart_user'@'localhost' IDENTIFIED BY 'choose-your-password';
GRANT ALL PRIVILEGES ON smartmart_db.* TO 'smartmart_user'@'localhost';
FLUSH PRIVILEGES;
```

**4. Create your `.env` file**

```powershell
Copy-Item .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Open `.env` and fill in `DJANGO_SECRET_KEY` (the key printed above) and `DB_PASSWORD`. Never commit `.env`.

**5. Create the tables, an admin user and starter data**

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
```

`seed_demo_data` creates the 8 categories and 5 suppliers. Products and customers are then added through the website.

**6. Run**

```powershell
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in.

> Each computer has its own MySQL database. Code is shared through GitHub, but data is not.

## 9. Demo workflow (5 to 10 minutes)

1. **Log in** and open the **Dashboard**.
2. **Products -> Add Product:** Amul Milk, Dairy, price 32, quantity 20, minimum 10.
3. **Inventory:** show the stock and the Green / Yellow / Red statuses.
4. **Billing:** add Milk x 2, Bread x 1, Biscuits x 3, choose UPI, click **Generate Bill**.
5. The **receipt** appears. Open **Inventory** again: stock decreased automatically.
6. Make a product fall to or below its minimum. The **LOW STOCK** alert appears on the Inventory page and the Dashboard.
7. **Restock:** see the recommendation and its calculation, then restock a product.
8. **Sales:** filter by date and payment method, open a bill.
9. **Customers:** open a customer to see the purchase history and total spent.
10. **Dashboard:** best-selling product and category, and the 7-day trend.

The Restock page averages past sales, so it shows more once there are several days of bills.

## 10. Validation and error handling

| | Client-side | Server-side |
|---|---|---|
| Where | Browser (`validation.js`) | Django forms (`forms.py`), `billing_logic.py` |
| Purpose | Instant feedback | The check that cannot be bypassed |
| Examples | Required fields, phone and email format, price, quantity, dates | Duplicate product / customer / supplier, insufficient stock, empty cart, invalid payment |

Client-side checks can be switched off by a user, so the server repeats every important check. Friendly messages are shown for: product or customer not found, insufficient stock, empty cart, invalid data, duplicates, protected deletes and database errors. Users see custom 404 and 500 pages, never raw Django errors (when `DJANGO_DEBUG=False`).

## 11. Security

- Django CSRF protection on every form.
- Django authentication, with passwords stored as hashes.
- Secrets in `.env` (ignored by Git). `.env.example` has placeholders only.
- Server-side validation of every input, and prices always read from the database.
- Billing runs in a database transaction with row locking.
- Set `DJANGO_DEBUG=False` outside development.

## 12. Testing checklist (manual)

- [ ] `python manage.py check` shows no issues
- [ ] Login works, wrong password shows a message, logout works
- [ ] Add, edit and delete a product
- [ ] Duplicate product name is rejected
- [ ] Search and filters work without reloading
- [ ] Low and out-of-stock status shows correctly
- [ ] Restock increases stock
- [ ] Bill total is correct (Milk x 2 + Bread x 1 + Biscuits x 3 = Rs. 194 at the demo prices)
- [ ] Bill saves the sale and its items, and stock decreases
- [ ] More than the available stock is rejected, and nothing is saved
- [ ] Empty cart is rejected
- [ ] Customer history and total spent are correct
- [ ] Customer or supplier with records cannot be deleted
- [ ] Sales date and payment filters work
- [ ] Restock page matches a hand calculation
- [ ] Layout works at phone width
- [ ] Site works with Wi-Fi off
- [ ] `git status` does not show `.env`

## 13. Limitations

- No automated test suite yet. Testing is manual (section 12).
- All logged-in users have the same access (no roles).
- The restock rule uses a simple average, so it ignores weekends and seasons.
- No real payment processing (the payment method is only recorded).
- Single store only.

## 14. Future scope

Barcode scanner, online payments, mobile app, multi-branch support, demand forecasting, cloud deployment, loyalty program, email/SMS alerts, role-based access, sales analytics with charts, automated tests.

## 15. Team

| Member | Responsibilities |
|---|---|
| *Name 1* | Frontend (HTML, CSS, Bootstrap, JavaScript, jQuery), billing interface, validation |
| *Name 2* | Backend (Django, MySQL, models, sales and inventory logic) |

Both members: integration, testing, documentation, Git / GitHub and the final presentation.

## 16. Conclusion

SmartMart connects products, stock, billing, customers, suppliers and sales in one system. A sale updates stock automatically, low stock is detected without manual checking, and past sales drive a clear restock suggestion. It is built with open-source tools: Django, MySQL, Bootstrap, JavaScript and jQuery.
