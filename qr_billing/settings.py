from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- SECURITY ----------------
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------------- UPI / STORE SETTINGS ----------------
UPI_ID = os.environ.get('UPI_ID', 'yourname@upi')
STORE_NAME = os.environ.get('STORE_NAME', 'My Store')



# ---------------- INSTALLED APPS ----------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # project apps
    
    'billing',
    'staffpanel',
    'customers',
    'products',
    'pos',
    'reports',
    'payments',
    'account',
  
]


# ---------------- MIDDLEWARE ----------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'qr_billing.urls'


# ---------------- TEMPLATES ----------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # global templates folder
        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'qr_billing.wsgi.application'

# ---------------- DATABASE ----------------

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# ---------------- PASSWORD VALIDATION ----------------

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


# ---------------- INTERNATIONALIZATION ----------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'   # better for India

USE_I18N = True
USE_TZ = True


# ---------------- STATIC FILES ----------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ---------------- MEDIA FILES (QR CODES) ----------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------- AUTH REDIRECTS ----------------

LOGIN_URL = "/account/login/"

LOGIN_REDIRECT_URL = "/account/redirect/"

LOGOUT_REDIRECT_URL = "/accounts/login/"


# ---------------- DEFAULT PRIMARY KEY ----------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'account.User'

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "https://billing-assistant.onrender.com"
]
LOGIN_REDIRECT_URL = '/account/redirect/'

# ---------------- PRODUCTION SECURITY ----------------
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = False  # Render handles SSL itself
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')