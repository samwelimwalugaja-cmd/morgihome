import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here':
    sys.exit('ERROR: SECRET_KEY is not set in .env. Generate one with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if os.getenv('CSRF_TRUSTED_ORIGINS') else []
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if os.getenv('CORS_ALLOWED_ORIGINS') else []

if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver', '10.0.2.2', '192.168.*']
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    'django.forms',
    'csp',
    'axes',
    'accounts',
    'properties',
    'mortgages',
    'transactions',
    'api',
    'bank',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',
        'user': '60/minute',
        'register': '5/minute',
        'login': '10/minute',
        'otp': '5/minute',
        'verification': '5/minute',
        'mortgage': '10/minute',
        'contract': '10/minute',
        'transaction': '10/minute',
        'property': '30/minute',
        'search': '20/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

AUTH_USER_MODEL = 'accounts.User'

ROOT_URLCONF = 'morgihome_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'bank.context_processors.bank_badges',
            ],
            'loaders': [
                ['django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]],
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'morgihome_backend.wsgi.application'

if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'), conn_max_age=600, conn_health_checks=True)
    }
elif not os.getenv('DB_PASSWORD'):
    # PythonAnywhere / local without Postgres password -> SQLite
    # On PA this resolves to /home/samweli20/morgihome/db.sqlite3 after clone
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'morgihome_db'),
            'USER': os.getenv('DB_USER', 'morgihome_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
            'CONN_HEALTH_CHECKS': True,
            'OPTIONS': {
                'sslmode': os.getenv('DB_SSLMODE', 'require'),
            },
            'TEST': {
                'NAME': 'test_morgihome_db',
                'CHARSET': 'utf8mb4',
                'COLLATION': 'utf8mb4_general_ci',
            },
        }
    }

if DEBUG:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {'max_similarity': 0.7},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailBackend',
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFiles'

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_STRICT_IGNORE = []
WHITENOISE_AUTOREFRESH = DEBUG

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@morgihome.co.tz')
EMAIL_TIMEOUT = 30
EMAIL_SSL_KEYFILE = os.getenv('EMAIL_SSL_KEYFILE', None)
EMAIL_SSL_CERTFILE = os.getenv('EMAIL_SSL_CERTFILE', None)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
STRICT_TRANSPORT_SECURITY = 'max-age=31536000; includeSubDomains; preload' if not DEBUG else ''
HSTS_SECONDS = 31536000 if not DEBUG else 0
HSTS_INCLUDE_SUBDOMAINS = True if not DEBUG else False
HSTS_PRELOAD = True if not DEBUG else False
SECURE_REDIRECT_EXEMPT = []

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# In DEBUG allow all for Flutter (emulator, web)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    if CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS = [o for o in CORS_ALLOWED_ORIGINS if o.strip()]
        CORS_ALLOW_CREDENTIALS = True
    else:
        CORS_ALLOWED_ORIGINS = []
        CORS_ALLOW_CREDENTIALS = False

# Flutter Web (Chrome) inapakia picha kupitia Image.network - bila hii, CORS inakataa /media/* na picha hazionekani
CORS_URLS_REGEX = r'^/(api|media)/.*$'
CORS_ALLOW_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['Authorization', 'Content-Type']
CORS_PREFLIGHT_MAX_AGE = 86400

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'base-uri': ("'self'",),
        'connect-src': ("'self'", 'https://unpkg.com', 'https://cdn.jsdelivr.net', 'https://cdn.tailwindcss.com'),
        'default-src': ("'self'",),
        'font-src': ("'self'", 'data:', 'https:', 'https://cdn.jsdelivr.net', 'https://unpkg.com'),
        'form-action': ("'self'",),
        'frame-src': ("'none'",),
        'img-src': ("'self'", 'data:', 'blob:', 'https:', 'http:', 'https://i.pravatar.cc', 'https://cdn.jsdelivr.net', 'https://unpkg.com'),
        'object-src': ("'none'",),
        'script-src': ("'self'", "'unsafe-inline'", 'https:', 'https://cdn.tailwindcss.com', 'https://cdn.jsdelivr.net', 'https://unpkg.com'),
        'style-src': ("'self'", "'unsafe-inline'", 'https:', 'https://cdn.jsdelivr.net', 'https://cdn.tailwindcss.com', 'https://cdn.jsdelivr.net/npm/remixicon@4.6.0/fonts/remixicon.css', 'https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/light/style.css', 'https://cdn.jsdelivr.net/npm/remixicon@4.2.0/fonts/remixicon.css', 'https://unpkg.com'),
        'style-src-elem': ("'self'", "'unsafe-inline'", 'https:', 'https://cdn.jsdelivr.net', 'https://cdn.tailwindcss.com', 'https://unpkg.com'),
    },
    'EXCLUDE_URLS': ['/admin/', '/admin-secure/', '/swagger/', '/redoc/'],
}

CSP_EXCLUDE_URLS = ['/admin/', '/admin-secure/', '/swagger/', '/redoc/']

SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

RATELIMIT_ENABLE = True
RATELIMIT_VIEW = 'accounts.views.rate_limit_exceeded'

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_LOCKOUT_URL = '/accounts/lockout/'
AXES_META_PROXY_COUNT = 1
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_ENABLED = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'morgihome-axes',
    }
}

CSRF_FAILURE_VIEW = 'accounts.views.rate_limit_exceeded'

LOGIN_ATTEMPTS_LIMIT = 5
LOGIN_ATTEMPTS_TIMEOUT = 300

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}:{lineno} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'security': {
            'format': '[{asctime}] SECURITY {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'security.log',
            'formatter': 'security',
            'level': 'WARNING',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'axes': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

DRF_YASG_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
        }
    },
    'SECURITY_REQUIRED': ['Bearer'],
    'VALIDATOR_URL': None,
}