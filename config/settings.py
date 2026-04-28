"""
Cấu hình Django cho dự án QHUN22
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if exists
load_dotenv()

# Đường dẫn gốc của dự án
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Bảo mật
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-qhun22-mobile-shop-2024')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'qhun22.com,www.qhun22.com,127.0.0.1,localhost').split(',')

# Ứng dụng đã cài đặt
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Apps tùy chỉnh
    'store',
]

# Site ID cho django-allauth
SITE_ID = 1

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Cấu hình URL
ROOT_URLCONF = 'config.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.qhun22_context',
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Xác thực
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Ngôn ngữ và múi giờ
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Upload)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs - Sử dụng URL tùy chỉnh của store
LOGIN_URL = 'store:login'
LOGIN_REDIRECT_URL = 'store:home'
LOGOUT_REDIRECT_URL = 'store:home'
ACCOUNT_LOGOUT_ON_GET = True  # Skip logout confirmation

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'store.backends.EmailBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Django-allauth settings
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Auto signup khi Google OAuth
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True  # Query email từ provider
SOCIALACCOUNT_LOGIN_ON_GET = True  # Skip intermediate confirmation page
ACCOUNT_LOGIN_ON_SUCCESS = True  # Redirect to LOGIN_REDIRECT_URL after successful login

# Cloudflare Turnstile Settings
CLOUDFLARE_TURNSTILE_SITE_KEY = os.getenv('CLOUDFLARE_TURNSTILE_SITE_KEY', '')
CLOUDFLARE_TURNSTILE_SECRET_KEY = os.getenv('CLOUDFLARE_TURNSTILE_SECRET_KEY', '')

# Google OAuth2 Settings
GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID', '')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET', '')

# Custom User Model
AUTH_USER_MODEL = 'store.CustomUser'

# Allauth Adapters
ACCOUNT_ADAPTER = 'store.allauth_adapter.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'store.allauth_adapter.SocialAccountAdapter'

# Messages Framework
MESSAGE_TAGS = {
    'success': 'success',
    'error': 'error',
}

# ==================== VNPAY PAYMENT GATEWAY CONFIG ====================
VNPAY_CONFIG = {
    'vnp_TmnCode': os.getenv('VNPAY_TMN_CODE', ''),
    'vnp_HashSecret': os.getenv('VNPAY_HASH_SECRET', ''),
    'vnp_Url': os.getenv('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'),
    'vnp_ReturnUrl': os.getenv('VNPAY_RETURN_URL', 'https://qhun22.com/vnpay/return/'),
    'vnp_IpnUrl': os.getenv('VNPAY_IPN_URL', 'https://qhun22.com/vnpay/ipn/'),
    'vnp_OrderType': 'billpayment',
    'vnp_Version': '2.1.0',
    'vnp_Command': 'pay',
}

# ==================== MOMO PAYMENT GATEWAY CONFIG ====================
MOMO_PARTNER_CODE = os.getenv('MOMO_PARTNER_CODE', 'MOMO')
MOMO_ACCESS_KEY = os.getenv('MOMO_ACCESS_KEY', 'F8BBA842ECF85')
MOMO_SECRET_KEY = os.getenv('MOMO_SECRET_KEY', 'K951B6PE1waDMi640xX08PD3vg6EkVlz')
MOMO_ENDPOINT = os.getenv('MOMO_ENDPOINT', 'https://test-payment.momo.vn/v2/gateway/api/create')
MOMO_RETURN_URL = os.getenv('MOMO_RETURN_URL', 'https://qhun22.com/momo/return/')
MOMO_IPN_URL = os.getenv('MOMO_IPN_URL', 'https://qhun22.com/momo/ipn/')

# ==================== BANK ACCOUNT CONFIG (VietQR) ====================
BANK_ID = os.getenv('BANK_ID', 'TCB')
BANK_ACCOUNT_NO = os.getenv('BANK_ACCOUNT_NO', '')
BANK_ACCOUNT_NAME = os.getenv('BANK_ACCOUNT_NAME', '')
VIETQR_CALLBACK_TOKEN = os.getenv('VIETQR_CALLBACK_TOKEN', 'dev-secret')

# ==================== EMAIL (SMTP) CONFIG ====================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL') or EMAIL_HOST_USER

# ==================== CONTACT CHANNELS ====================
ZALO_CHAT_URL = os.getenv('ZALO_CHAT_URL', 'https://zalo.me/0327221005')

# ==================== LOGGING ====================
LOG_LEVEL = os.getenv('DJANGO_LOG_LEVEL', 'INFO').upper()
CHATBOT_LOG_LEVEL = os.getenv('QH_CHATBOT_LOG_LEVEL', 'INFO').upper()

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': LOG_LEVEL,
        },

        'chatbot_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOG_DIR / 'chatbot.log'),
            'formatter': 'standard',
            'level': CHATBOT_LOG_LEVEL,
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'store.chatbot.api': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
        'store.chatbot_orchestrator': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
        'store.chatbot_service': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
        'ai.rag_pipeline': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
        'ai.trainer': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
        'ai.vector_store': {
            'handlers': ['console', 'chatbot_file'],
            'level': CHATBOT_LOG_LEVEL,
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

