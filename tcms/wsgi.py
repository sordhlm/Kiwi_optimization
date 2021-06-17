# -*- coding: utf-8 -*-

"""
WSGI config for Kiwi TCMS project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.

"""

import os
import sys
import tempfile
from django.core.wsgi import get_wsgi_application

import tcms


# We defer to a DJANGO_SETTINGS_MODULE already in the environment. This breaks
# if running multiple sites in the same mod_wsgi process. To fix this, use
# mod_wsgi daemon mode with each site in its own daemon process, or use
# os.environ["DJANGO_SETTINGS_MODULE"] = "tcms.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tcms.settings.product")
os.environ['PYTHON_EGG_CACHE'] = tempfile.mkdtemp(prefix='.python-eggs-')

# add tcms's core lib path
sys.path.append(os.path.join(tcms.__path__[0], 'core', 'lib'))

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
_APPLICATION = get_wsgi_application()


def application(environ, start_response):
    if ('PATH_INFO' in environ) and ('SCRIPT_NAME' in environ):
        environ['PATH_INFO'] = environ['SCRIPT_NAME'] + environ['PATH_INFO']
    if environ['wsgi.url_scheme'] == 'https':
        environ['HTTPS'] = 'on'

    return _APPLICATION(environ, start_response)

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
