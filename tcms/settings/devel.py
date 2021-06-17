# pylint: disable=wildcard-import, unused-wildcard-import
"""
    Django settings for devel env.
"""
import pymysql
pymysql.install_as_MySQLdb()
import os
from .product import *  # noqa: F403


# Debug settings
DEBUG = True

# Database settings
DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': '/home/nvme/weili/10KIWI_QA/db/test-kiwi.devel.sqlite',  # nosec:B108:hardcoded_tmp_directory
        # 'USER': 'root',
        # 'PASSWORD': '',
        # 'HOST': '',
        # 'PORT': '',
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kiwi_tcms',  # nosec:B108:hardcoded_tmp_directory
        'USER': 'tester',
        'PASSWORD': 'Cnex!321',
        'HOST': '172.29.129.8',
        'PORT': '3306',
        'CONN_MAX_AGE': 5*60,
        'OPTIONS':{'charset': 'utf8mb4'}
    },
}

# django-debug-toolbar settings

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa: F405

INSTALLED_APPS += ['debug_toolbar', 'django_extensions']  # noqa: F405

MEDIA_ROOT = os.path.join(TCMS_ROOT_PATH, '..', 'uploads')  # noqa: F405

# Needed by django.template.context_processors.debug:
# See:
# http://docs.djangoproject.com/en/dev/ref/templates/api/#django-template-context-processors-debug
INTERNAL_IPS = ('127.0.0.1', )

STATICFILES_STORAGE = 'tcms.tests.storage.RaiseWhenFileNotFound'
