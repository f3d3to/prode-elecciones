import os
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'prode',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'prode_backend.urls'

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

WSGI_APPLICATION = 'prode_backend.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Si hay DATABASE_URL, usar Postgres (prod/Render)
if os.getenv("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=60,            # pooling liviano
        ssl_require=True            # Render usa SSL
    )


AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

# CORS: enumerar orígenes permitidos para que funcione con credenciales
_origins_env = os.environ.get('ALLOWED_ORIGINS')
if _origins_env:
    CORS_ALLOWED_ORIGINS = [s for s in _origins_env.split(',') if s]
else:
    # Defaults para dev
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'https://localhost:5173', 'https://127.0.0.1:5173',
        "https://prode-2025-jade.vercel.app",
    ]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins (cuando front y back están en dominios distintos)
_csrf_env = os.environ.get('CSRF_TRUSTED_ORIGINS')
if _csrf_env:
    CSRF_TRUSTED_ORIGINS = [s for s in _csrf_env.split(',') if s]
else:
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'https://localhost:5173', 'https://127.0.0.1:5173',
    ]

# Deadline
DEADLINE = os.environ.get('DEADLINE')  # ISO-UTC string

def is_after_deadline() -> bool:
    dl = os.environ.get('DEADLINE')
    if not dl:
        return False
    try:
        dt = datetime.fromisoformat(dl.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) >= dt
    except Exception:
        return False

# Cookies cross-site para producción (Vercel -> Render):
# Habilitar con CROSS_SITE_COOKIES=true en el entorno de producción (HTTPS requerido)
_cross = os.environ.get('CROSS_SITE_COOKIES', 'false').strip().lower() in ('1','true','yes')
if _cross:
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SECURE = True

# Admin token TTL (segundos) para autenticación alternativa sin cookies
ADMIN_TOKEN_TTL = int(os.environ.get('ADMIN_TOKEN_TTL', '86400'))  # 24h
