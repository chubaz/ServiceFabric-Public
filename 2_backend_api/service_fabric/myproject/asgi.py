# /service-fabric-project/2_backend_api/service_fabric/myproject/asgi.py
"""
ASGI config for myproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/stable/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Imposta la variabile d'ambiente 'DJANGO_SETTINGS_MODULE'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

# Crea l'applicazione ASGI
application = get_asgi_application()

# --- NOTA PER T7/T9 (Chat/WebSockets) ---
# Quando integreremo Django Channels per la chat, questo file diventerà
# più complesso. Dovremo aggiungere il routing WebSocket,
# ad esempio:
#
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# import chat.routing
#
# application = ProtocolTypeRouter({
#   "http": get_asgi_application(),
#   "websocket": AuthMiddlewareStack(
#       URLRouter(
#           chat.routing.websocket_urlpatterns
#       )
#   ),
# })
# ----------------------------------------