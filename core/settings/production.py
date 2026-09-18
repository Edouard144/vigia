from .base import *

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from decouple import config

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.2,
    send_default_pii=False,
)

DEBUG = False
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files (whitenoise)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_FRAME_OPTIONS = 'DENY'
X_FRAME_OPTIONS = 'DENY'

# CORS — allow the frontend origin
FRONTEND_URL = config('FRONTEND_URL', default='')
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://localhost:3000",
]
if FRONTEND_URL:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL)