import os
import random
import string
import environ

env = environ.Env()

DEBUG = False

ANONYMOUS_USER_NAME = "AnonymousUser"

AUTH_USER_MODEL = "testapp.CustomUser"
GUARDIAN_MONKEY_PATCH = False

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.messages',
    'guardian',
    'guardian.testapp',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

ROOT_URLCONF = 'guardian.testapp.tests.urls'
SITE_ID = 1

SECRET_KEY = ''.join([random.choice(string.ascii_letters) for x in range(40)])

# Database specific

DATABASES = {'default': env.db(default="sqlite:///")}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (
            os.path.join(os.path.dirname(__file__), 'tests', 'templates'),
        ),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
