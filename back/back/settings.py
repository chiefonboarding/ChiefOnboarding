"""
Django settings for back project.

Generated by 'django-admin startproject' using Django 3.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import environ

env = environ.Env()
environ.Env.read_env(env.str('ENV_PATH', 'back/.env'))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', default=False)

ALLOWED_HOSTS = [env('ALLOWED_HOST', default="0.0.0.0"),]

INSTALLED_APPS = [
    'users',
    'organization',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_auth',
    'axes',
    'user_auth',
    'notes',
    'to_do',
    'resources',
    'introductions',
    'admin_tasks',
    'badges',
    'slack_bot',
    'integrations',
    'preboarding',
    'appointments',
    'sequences',
    'new_hire',
    'misc',
    'anymail',
    'django_q',
    'back'
]

if env('API_ACCESS', default=False):
    INSTALLED_APPS += [
        'rest_framework.authtoken'
    ]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.language_middleware',
    'axes.middleware.AxesMiddleware'
]

ROOT_URLCONF = 'back.urls'

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
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'templates'),
)

WSGI_APPLICATION = 'back.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': env.db()
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]


AUTH_USER_MODEL = 'users.User'

CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_ALLOW_ALL = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication'
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'users.permissions.AdminPermission',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day'
    }
}


if env('API_ACCESS', default=False):
    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append('rest_framework.authentication.TokenAuthentication')


REST_AUTH_SERIALIZERS = {
    'PASSWORD_RESET_SERIALIZER': 'user_auth.serializers.PasswordResetSerializer',
}

APPEND_SLASH = False
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if env('ANYMAIL', default=False):
    if env('MAILGUN', default=False):
        ANYMAIL = {
            "MAILGUN_API_KEY": env('MAILGUN_KEY', default=""),
            "MAILGUN_SENDER_DOMAIN": env('MAILGUN_DOMAIN', default="")
        }
        EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

    if env('MAILJET', default=False):
        ANYMAIL = {
            "MAILJET_API_KEY": env('MAILJET_API_KEY', default=""),
            "MAILJET_SECRET_KEY": env('MAILJET_SECRET_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.mailjet.EmailBackend"

    if env('MANDRILL', default=False):
        ANYMAIL = {
            "MANDRILL_API_KEY": env('MANDRILL_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.mandrill.EmailBackend"

    if env('POSTMARK', default=False):
        ANYMAIL = {
            "POSTMARK_SERVER_TOKEN": env('POSTMARK_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"

    if env('SENDGRID', default=False):
        ANYMAIL = {
            "SENDGRID_API_KEY": env('SENDGRID_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"

    if env('SENDINBLUE', default=False):
        ANYMAIL = {
            "SENDINBLUE_API_KEY": env('SENDINBLUE_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.sendinblue.EmailBackend"

    if env('SPARKPOST', default=False):
        ANYMAIL = {
            "SPARKPOST_API_KEY": env('SPARKPOST_KEY', default="")
        }
        EMAIL_BACKEND = "anymail.backends.sparkpost.EmailBackend"

if env('SMTP', default=False):
    EMAIL_HOST = env('EMAIL_HOST', default="localhost")
    EMAIL_PORT = env('EMAIL_PORT', default="25")
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default="")
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default="")
    EMAIL_USE_TLS = env('EMAIL_USE_TLS', default="")
    EMAIL_USE_SSL = env('EMAIL_USE_SSL', default="")
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'


DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
OLD_PASSWORD_FIELD_ENABLED = True
REST_SESSION_LOGIN = True

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cached_items',
    }
}

Q_CLUSTER = {
    'name': 'DjangORM',
    'workers': 2,
    'timeout': 90,
    'retry': 1800,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default'
}

# AWS
AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', default="https://s3.eu-west-1.amazonaws.com")
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default="")
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default="")
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default="")
AWS_REGION = env('AWS_REGION', default="us-east-1")

BASE_URL = env('BASE_URL')

# Twilio
TWILIO_FROM_NUMBER = env('TWILIO_FROM_NUMBER', default="")
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default="")
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default="")

# Django-Axes
AUTHENTICATION_BACKENDS = [
    # AxesBackend should be the first backend in the AUTHENTICATION_BACKENDS list.
    'axes.backends.AxesBackend',

    # Django ModelBackend is the default authentication backend.
    'django.contrib.auth.backends.ModelBackend',
]
AXES_ENABLED = True
AXES_PROXY_ORDER = []
AXES_PROXY_TRUSTED_IPS = []
AXES_PROXY_COUNT = 0
AXES_META_PRECEDENCE_ORDER = [
   'HTTP_X_FORWARDED_FOR',
   'REMOTE_ADDR',
]
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_FAILURE_LIMIT = 20
AXES_LOCK_OUT_AT_FAILURE = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = False
AXES_ONLY_USER_FAILURES = False
AXES_ONLY_ADMIN_SITE = False
AXES_ENABLE_ADMIN = True
AXES_USE_USER_AGENT = False
AXES_USERNAME_FORM_FIELD = "email"
AXES_PASSWORD_FORM_FIELD = "password"  # noqa
AXES_USERNAME_CALLABLE = None
AXES_WHITELIST_CALLABLE = None
AXES_LOCKOUT_CALLABLE = None
AXES_RESET_ON_SUCCESS = False
AXES_DISABLE_ACCESS_LOG = False
AXES_LOCKOUT_TEMPLATE = None
AXES_LOCKOUT_URL = None
AXES_COOLOFF_TIME = None
AXES_VERBOSE = True
AXES_NEVER_LOCKOUT_WHITELIST = False
AXES_NEVER_LOCKOUT_GET = False
AXES_ONLY_WHITELIST = False
AXES_IP_WHITELIST = None
AXES_IP_BLACKLIST = None
AXES_LOCK_OUT_BY_USER_OR_IP = False
# message to show when locked out and have cooloff enabled
AXES_COOLOFF_MESSAGE = "Account locked: too many login attempts. Please try again later"
AXES_PERMALOCK_MESSAGE = "Account locked: too many login attempts. Contact an admin to unlock your account."
PROXY_TRUSTED_IPS = None
REST_FRAMEWORK_ACTIVE = True

# Error tracking
if env('SENTRY', default=False):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=env('SENTRY_URL', default=""),
        integrations=[DjangoIntegration(),],

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=False
    )

if not env('DEBUG', default=False) and not env('HTTP_INSECURE', default=False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

FIXTURE_DIRS = ['fixtures']

if env('SSL_REDIRECT', default=False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

ACCOUNT_EMAIL = env('ACCOUNT_EMAIL', default='')
ACCOUNT_PASSWORD = env('ACCOUNT_PASSWORD', default='')
