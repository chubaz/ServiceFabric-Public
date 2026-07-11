# /service-fabric-project/2_backend_api/service_fabric/myproject/wsgi.py
"""
WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Imposta la variabile d'ambiente 'DJANGO_SETTINGS_MODULE' in modo che
# il server sappia quale file di impostazioni utilizzare.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

application = get_wsgi_application()