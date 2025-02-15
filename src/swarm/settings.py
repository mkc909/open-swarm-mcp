import os
import sys
from django.db.backends.signals import connection_created
from django.dispatch import receiver
import logging
from pathlib import Path
from dotenv import load_dotenv

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

logging.basicConfig(level=(logging.DEBUG if DEBUG else logging.INFO), format='%(levelname)s:%(message)s')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
logger.debug(f"BASE_DIR resolved to: {BASE_DIR}")

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')

# Define a logs directory within the base directory
LOGS_DIR = BASE_DIR / 'logs'

# Ensure the logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Add the project root and the app directory to the system path
sys.path.append(str(BASE_DIR))  # Add the project root
sys.path.append(str(BASE_DIR / 'src/swarm/'))
logger.debug(f"System path updated: {sys.path}")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key'  # Replace with a strong secret key

# Blueprint discovery and configuration
BLUEPRINTS_DIR = BASE_DIR / 'blueprints'
swarm_blueprints_env = os.getenv('SWARM_BLUEPRINTS', '').strip()
SWARM_BLUEPRINTS = [name.strip() for name in swarm_blueprints_env.split(',') if name.strip()] if swarm_blueprints_env else []
logger.info(f"Discovered SWARM_BLUEPRINTS env: {SWARM_BLUEPRINTS}")

# Discover and load blueprint settings only when not in CLI mode
import os
if not os.getenv("SWARM_CLI"):
    for blueprint_name in os.listdir(BLUEPRINTS_DIR):
        blueprint_path = BLUEPRINTS_DIR / blueprint_name
        settings_path = blueprint_path / 'settings.py'
        if settings_path.exists() and (not SWARM_BLUEPRINTS or blueprint_name in SWARM_BLUEPRINTS):
            logger.info(f"Loading settings for blueprint: {blueprint_name}")
            with open(settings_path) as f:
                code = compile(f.read(), str(settings_path), 'exec')
                exec(code, globals(), locals())
else:
    logger.info("CLI mode detected; skipping blueprint settings loading")

ALLOWED_HOSTS = ['*']  # Adjust as needed in production

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'channels',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'swarm',
    'swarm.extensions.blueprint.modes.rest_mode',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Enables static file serving
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'swarm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'src/swarm/templates'],  # Updated to use pathlib for consistency
        'APP_DIRS': False,
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

WSGI_APPLICATION = 'swarm.wsgi.application'
ASGI_APPLICATION = 'swarm.asgi.application'


# Database
# Determine database selection from environment variable (default: sqlite)
DJANGO_DATABASE = os.getenv("DJANGO_DATABASE", "sqlite").lower()

if DJANGO_DATABASE == "postgres":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv("POSTGRES_DB", "swarm"),
            'USER': os.getenv("POSTGRES_USER", "postgres"),
            'PASSWORD': os.getenv("POSTGRES_PASSWORD", ""),
            'HOST': os.getenv("POSTGRES_HOST", "localhost"),
            'PORT': os.getenv("POSTGRES_PORT", "5432"),
        }
    }
elif DJANGO_DATABASE == "sqlite":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }
else:
    raise ValueError(f"Invalid value for DJANGO_DATABASE: {DJANGO_DATABASE}. Must be 'sqlite' or 'postgres'.")

# Warn if stateful mode is enabled but using SQLite
if os.getenv("STATEFUL_CHAT_ID_PATH") and DJANGO_DATABASE != "postgres":
    logger.warning("⚠️  WARNING: Stateful chat is enabled, but DJANGO_DATABASE is set to 'sqlite'. "
                   "Consider switching to 'postgres' for scalability and persistence.")

@receiver(connection_created)
def set_sqlite_optimizations(sender, connection, **kwargs):
    """Apply SQLite PRAGMA settings when a new database connection is created."""
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA journal_mode=WAL;')  # Enable Write-Ahead Logging
        cursor.execute('PRAGMA synchronous=NORMAL;')  # Reduce disk sync overhead
        cursor.execute('PRAGMA temp_store=MEMORY;')  # Use memory for temp tables
        cursor.execute('PRAGMA mmap_size=30000000000;')  # Use memory-mapped I/O
        cursor.execute('PRAGMA cache_size=-5000;')  # Limit cache to 5MB
        cursor.execute('PRAGMA busy_timeout=5000;')  # Prevent "database is locked" errors
        cursor.close()

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
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
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Define a root directory for collectstatic
STATICFILES_DIRS = [
    BASE_DIR / "src/swarm/static"
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file_rest_mode': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'rest_mode.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'file_default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'open_swarm.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {  # Add this logger
            'handlers': ['console', 'file_default'],
            'level': 'INFO',
            'propagate': True,
        },
        'rest_mode': {
            'handlers': ['console', 'file_rest_mode'],
            'level': 'DEBUG',
            'propagate': False,
        },
        '': {  # Root logger
            'handlers': ['console', 'file_default'],
            'level': 'INFO',
        },
    },
}

ACCOUNT_EMAIL_VERIFICATION = "none"  # Skip email verification
ACCOUNT_SIGNUP_REDIRECT_URL = "/django_chat/"  # Redirect to homepage after signup
ACCOUNT_AUTHENTICATION_METHOD = "username_email"  # Allow both username and email login
ACCOUNT_USERNAME_REQUIRED = True  # Require usernames
ACCOUNT_EMAIL_REQUIRED = False  # Emails optional for dev POC

# Caching Configuration
USE_DJANGO_CACHE = True  # Set to False to disable caching
# swarm/settings.py

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

INSTALLED_APPS += [
    'rest_framework.authtoken',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'swarm.auth.EnvOrTokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Disable CSRF for DRF authentication
# SESSION_COOKIE_HTTPONLY = True
# CSRF_COOKIE_HTTPONLY = True
# CSRF_TRUSTED_ORIGINS = ['http://localhost:8000']

