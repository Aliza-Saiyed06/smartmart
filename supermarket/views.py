"""
Views for the supermarket app.

A view receives a web request, does some work, and returns a web page.
"""

import django
from django.db import connection
from django.shortcuts import render


def dashboard(request):
    """
    Temporary dashboard (Phase 3).

    It only checks that Django can talk to MySQL.
    The real dashboard with sales cards and low-stock alerts is built in Phase 12.
    """
    try:
        # Ask MySQL for its version number. If this works, the connection is OK.
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