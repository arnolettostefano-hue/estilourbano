import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'replace-me-for-production')

# Read DEBUG from environment so production can set it to False
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.sessions',
    'catalog',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'clothstore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                    'django.template.context_processors.request',
                ],
        },
    },
]

WSGI_APPLICATION = 'clothstore.wsgi.application'

# Use sqlite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Where `collectstatic` will gather static files for production (e.g. Render)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Use Whitenoise compressed manifest storage in production for efficient static serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Use signed-cookie session backend to avoid requiring the database table
# during local development. For production, prefer the database-backed session
# engine and run migrations to create `django_session` table.
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
