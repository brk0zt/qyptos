from pathlib import Path
from datetime import timedelta
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'dev-secret-key-change-in-prod'
DEBUG = True
ALLOWED_HOSTS = ['*']
REACT_BUILD_DIR = os.path.join(BASE_DIR, 'frontend', 'build')

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
    'chat',    
    'memory',
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
    'users.security.middleware.CameraSecurityMiddleware',
]

ROOT_URLCONF = 'cloud_mvp.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'frontend', 'build')],
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
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'build', 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # JWT'yi (Simple JWT) kullanıyorsanız, ana kimlik doğrulama sınıfı budur.
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Ekle
        # Eğer hem JWT hem de standart TokenAuthentication (DRF'in kendi token'ı) kullanıyorsanız
        # bu satırı da ekleyin. Kullanmıyorsanız silin.
        # 'rest_framework.authentication.TokenAuthentication',
        
        # Django session'larını da kullanmak isterseniz (tarayıcıdan erişim için):
        # 'rest_framework.authentication.SessionAuthentication', 
    ],
    
    'DEFAULT_PERMISSION_CLASSES': [
        # Varsayılan olarak tüm endpoint'leri korur.
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',  # Geçici: Tüm endpoint'lere erişime izin ver

    ],
    
    'DEFAULT_RENDERER_CLASSES': [
        # Tüm yanıtların varsayılan olarak JSON formatında gönderilmesini sağlar (API için standarttır).
        'rest_framework.renderers.JSONRenderer',
    ],
    
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'SIGNING_KEY': 'dev-secret-key-change-in-prod',  # BU SATIR ÇOK ÖNEMLİ!
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React'in varsayılan adresi
    "http://127.0.0.1:3000",
    # Eğer React başka bir adreste çalışıyorsa onu da ekle
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
CSRF_COOKIE_DOMAIN = None # Varsayılan olarak None bırakmak genellikle en iyisidir.
CSRF_COOKIE_SAMESITE = 'None' # Modern tarayıcılar için önerilir.
SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = False
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
SECURITY_CONFIG = {
    'ENABLE_CAMERA_MONITORING': True,
    'MAX_NO_FACE_SECONDS': 3,
    'ALLOW_SCREENSHOTS': False,
}

SECURE_VIEWER_CONFIG = {
    'ENABLE_CANVAS_PROTECTION': True,
    'ENABLE_CSS_DISTORTION': True,
    'MAX_VIOLATIONS': 2,
    'BLOCK_DURATION': 3600,  # 1 saat
    'DETECT_SCREENSHOT_APIS': True,
}