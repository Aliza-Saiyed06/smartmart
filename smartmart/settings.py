"""
Django settings for the SmartMart project.

This file controls how the whole project behaves:
installed apps, database connection, templates, static files, etc.
Secrets (secret key, database password) are NOT written here.
They are read from the .env file using python-dotenv.
"""

import os
from pathlib import Path

from django.contrib.messages import constants as message_constants
from dotenv import load_dotenv

# BASE_DIR = the main project folder (the one that contains manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Read the .env file located in the project folder
load_dotenv(BASE_DIR / '.env')


# ---------------------------------------------------------------
# Security settings (values come from .env)
# ---------------------------------------------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# DEBUG=True shows detailed error pages. Use it only while developing.
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
]


# ---------------------------------------------------------------
# Applications
# ---------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Our own app
    'supermarket',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smartmart.urls'


# ---------------------------------------------------------------
# Templates (HTML files)
# ---------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Django will also look for templates in C:\Projects\smartmart\templates
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartmart.wsgi.application'


# ---------------------------------------------------------------
# Database: MySQL (credentials come from .env)
# ---------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'smartmart_db'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}


# ---------------------------------------------------------------
# Password validation (used when creating users)
# ---------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------
# Language and time
# ---------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True

# USE_TZ = False means dates/times are stored exactly as local (IST) time.
# We keep it False on purpose: with MySQL, USE_TZ=True needs extra timezone
# tables to be loaded, otherwise "sales today" queries return wrong results.
USE_TZ = False


# ---------------------------------------------------------------
# Static files (CSS, JavaScript, images)
# ---------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# ---------------------------------------------------------------
# Messages: map Django's "error" level to Bootstrap's "danger" colour
# ---------------------------------------------------------------
MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------
# Where Django sends people who are not logged in (name of a URL in urls.py)
LOGIN_URL = 'login'

# Where to go after a successful login
LOGIN_REDIRECT_URL = 'dashboard'

# Where to go after logout
LOGOUT_REDIRECT_URL = 'login'