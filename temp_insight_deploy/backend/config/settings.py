from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-key-for-dev")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# [Fix] Prevent POST redirect issues (Body loss -> 400 Bad Request)
APPEND_SLASH = False

# [Security] HTTPS & Proxy Settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
CSRF_TRUSTED_ORIGINS = [
    "https://*.nip.io",
    "https://mind-diary.kro.kr",
]
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = True
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = [
    "https://217.142.253.35.nip.io", # Standard HTTPS
    "http://217.142.253.35.nip.io",  # Verify
    "https://217.142.253.35.nip.io:8000", # Just in case
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
# [Fix] Reverted to default names for Frontend compatibility
# CSRF_COOKIE_NAME = "csrftoken"
# SESSION_COOKIE_NAME = "sessionid"


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_yasg",
    # Local apps
    "accounts",
    "centers",
    "haru_on",
    "b2g_sync",
    "share",
]

MIDDLEWARE = [
    'config.middleware_dump.DumpRequestMiddleware',  # [Debug] Dump Raw Request
    "corsheaders.middleware.CorsMiddleware",  # CORS
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.csrf.CsrfViewMiddleware', # [Debug] Disable CSRF to check 400 error
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# 기본적으로 MySQL을 사용하되 설정을 .env에서 제어
# 연결 실패 시 SQLite로 fallback하는 로직은 없으나, 초기 개발을 위해
# DB_MODE 환경변수로 제어하거나 일단 MySQL로 강제.
# Database
# [Hard Transition] PostgreSQL
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "reboot_db"), # [Found] Local DB
        "USER": os.getenv("DB_USER", "slyeee"),    # [Found] Local User
        "PASSWORD": os.getenv("DB_PASSWORD", ""),  # No Password for local socket
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static_root"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF Setting
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# JWT Setting
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}

# CORS Setting
# CORS Setting
# CORS_ALLOW_ALL_ORIGINS = True  # withCredentials: true와 충돌하여 비활성화
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://217.142.253.35.nip.io",
    "https://150.230.7.76.nip.io",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5174",
]
CSRF_TRUSTED_ORIGINS = [
    "https://217.142.253.35.nip.io",
    "https://150.230.7.76.nip.io",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
]

# [Emergency Fix] Regex-based Origin Allow (Port-Agnostic)
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https?://localhost(:[0-9]+)?$",
    r"^https?://127\.0\.0\.1(:[0-9]+)?$",
    r"^https?://.*\.nip\.io$",
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/ubuntu/project/temp_insight_deploy/backend/django_root.log',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'DEBUG',
    },
}
