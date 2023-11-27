"""
Django settings for chatgptwebapp project.

Based on 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

if os.getenv("AUTH_ENABLED") == 'False':
    LOGIN_REQUIRED = False
else:
    LOGIN_REQUIRED = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

allowed_hosts_temp = os.getenv("ALLOWED_HOSTS")
allowed_hosts_temp = str(allowed_hosts_temp).split(',')
ALLOWED_HOSTS = allowed_hosts_temp

cors_csrf_trusted_host_temp = os.getenv("CORS_AND_CSRF_TRUSTED_HOST")
cors_csrf_trusted_host_temp = str(cors_csrf_trusted_host_temp).split(',')
CSRF_TRUSTED_ORIGINS = cors_csrf_trusted_host_temp
CORS_ORIGIN_WHITELIST = cors_csrf_trusted_host_temp

# Application references
# https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-INSTALLED_APPS
INSTALLED_APPS = [
    'app',
    # Add your apps here to enable them
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_swagger',
    'sequences.apps.SequencesConfig',
]


# Middleware framework
# https://docs.djangoproject.com/en/2.1/topics/http/middleware/
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'opencensus.ext.django.middleware.OpencensusMiddleware',
]

ROOT_URLCONF = 'chatgptwebapp.urls'

# Template configuration
# https://docs.djangoproject.com/en/2.1/topics/templates/
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

WSGI_APPLICATION = 'chatgptwebapp.wsgi.application'
# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

if os.getenv("DATABASE_TYPE") == 'SQLITE3':
    DATABASES = {
        ### Sqlite
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }    
elif os.getenv("DATABASE_TYPE") == 'POSTGRESQL':
    DATABASES = {       
        ### Postgresql
        'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': os.getenv("POSTGRES_CONNECTION_USERID"),
        'PASSWORD': os.getenv("POSTGRES_CONNECTION_PASSWORD"),
        'HOST': os.getenv("POSTGRES_CONNECTION_HOST"),
        'PORT': '5432',
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            'sslmode': 'require',
            'keepalives_idle': 100,
            'keepalives_interval': 5,
            'keepalives_count': 5,
        },
        }
    }

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators
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

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema'
}

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  
STATIC_ROOT = os.path.join(BASE_DIR, 'app\\static')

APPEND_SLASH = False

### Application Insight ###
if os.getenv("DJANGO_SECRET_KEY") == 'True':
    OPENCENSUS_Exporter = f'opencensus.ext.azure.trace_exporter.AzureExporter(connection_string="{os.getenv("APPINSIGHT_KEY")}")'
    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': OPENCENSUS_Exporter,
            'EXCLUDELIST_PATHS': [], 
        }
    }

LOGIN_URL = 'login/'
LOGIN_REDIRECT_URL = ''
LOGOUT_REDIRECT_URL = 'login/'
LOGOUT_URL = '/logout/'