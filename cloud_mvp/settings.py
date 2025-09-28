from pathlib import Path
from datetime import timedelta
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'dev-secret-key-change-in-prod'
DEBUG = False
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',
    "rest_framework_simplejwt.token_blacklist",
    'files',
    'users',
    'ads',
    'corsheaders',
    "channels",
    "notifications",
    "groups",
        
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cloud_mvp.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]},
    },
]
WSGI_APPLICATION = 'cloud_mvp.wsgi.application'
ASGI_APPLICATION = "cloud_mvp.asgi.application"
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3',}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # JWT'yi (Simple JWT) kullanýyorsanýz, ana kimlik doðrulama sýnýfý budur.
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Ekle
        # Eðer hem JWT hem de standart TokenAuthentication (DRF'in kendi token'ý) kullanýyorsanýz
        # bu satýrý da ekleyin. Kullanmýyorsanýz silin.
        # 'rest_framework.authentication.TokenAuthentication',
        
        # Django session'larýný da kullanmak isterseniz (tarayýcýdan eriþim için):
        # 'rest_framework.authentication.SessionAuthentication', 
    ],
    
    'DEFAULT_PERMISSION_CLASSES': [
        # Varsayýlan olarak tüm endpoint'leri korur.
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',  # Geçici: Tüm endpoint'lere eriþime izin ver

    ],
    
    'DEFAULT_RENDERER_CLASSES': [
        # Tüm yanýtlarýn varsayýlan olarak JSON formatýnda gönderilmesini saðlar (API için standarttýr).
        'rest_framework.renderers.JSONRenderer',
    ],
    
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React'in varsayýlan adresi
    "http://127.0.0.1:3000",
    # Eðer React baþka bir adreste çalýþýyorsa onu da ekle
]
CORS_ALLOW_CREDENTIALS = True
CSRF_COOKIE_HTTPONLY = False 
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
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
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8001",
]
CSRF_COOKIE_DOMAIN = None # Varsayýlan olarak None býrakmak genellikle en iyisidir.
CSRF_COOKIE_SAMESITE = 'None' # Modern tarayýcýlar için önerilir.
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = False
