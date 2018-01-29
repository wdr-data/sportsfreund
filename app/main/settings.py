"""
Django settings for wahltraud project.

Generated by 'django-admin startproject' using Django 1.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
import dj_database_url
from urllib.parse import urlparse


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY')
if SECRET_KEY is None:
    raise EnvironmentError("Please specify a SECRET_KEY in your environment")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if os.environ.get("DEBUG") == "True":
    DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'storages',
    'backend.apps.BackendConfig',
    'bot.apps.BotConfig',
    'sortedm2m',
    'sortedm2m_filter_horizontal_widget',
    'tz_detect',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tz_detect.middleware.TimezoneMiddleware',
]

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'main.wsgi.application'

SECURE_SSL_REDIRECT = True

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if os.environ.get('DATABASE_URL') is not None:
    DATABASES = {
        'default': dj_database_url.config()
    }


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
URL_PREFIX = '/'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, STATIC_URL[1:])
STATIC_URL = os.path.join(URL_PREFIX, STATIC_URL[1:])

DEFAULT_FILE_STORAGE = 'main.custom_storages.S3BotoRandomNameStorage'
AWS_ACCESS_KEY_ID = os.environ.get('S3_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('S3_ACCESS_SECRET')
AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_BUCKET')
AWS_AUTO_CREATE_BUCKET = False
AWS_QUERYSTRING_AUTH = False
try:
    AWS_S3_ENDPOINT_URL = os.environ['S3_ENDPOINT']
except KeyError:
    pass
try:
    aws_url = urlparse(os.environ['S3_DOMAIN'])
    AWS_S3_SECURE_URLS = False
    AWS_S3_URL_PROTOCOL = aws_url.scheme + ':'
    AWS_S3_CUSTOM_DOMAIN = aws_url.netloc + aws_url.path
except KeyError:
    pass
S3_USE_SIGV4 = True

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Error reporting on Sentry.io
if os.environ.get('SENTRY_URL') is not None:
#    INSTALLED_APPS.append('raven.contrib.django.raven_compat')
    RAVEN_CONFIG = {
        'dsn': os.environ.get('SENTRY_URL'),
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }
}

TZ_DETECT_COUNTRIES = ('DE', 'FR', 'GB', 'US', 'CN', 'IN', 'JP', 'BR', 'RU')
