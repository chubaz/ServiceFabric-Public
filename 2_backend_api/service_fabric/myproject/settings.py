AUTH_USER_MODEL = 'api.User' #nome_app.NomeModello

"""
Impostazioni Django per il progetto Service Fabric (myproject).

Basato su /service-fabric-project/2_backend_api/service_fabric/myproject/settings.py
e ispirato da.
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR punta a /service-fabric-project/2_backend_api/service_fabric/
BASE_DIR = Path(__file__).resolve().parent.parent

# PROJECT_ROOT: Risale alla radice del progetto se siamo in sviluppo locale,
# altrimenti usa BASE_DIR se siamo nel container (/app)
if os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER'):
    PROJECT_ROOT = BASE_DIR
else:
    # In locale, risaliamo da /2_backend_api/service_fabric a /
    PROJECT_ROOT = BASE_DIR.parent.parent

# --- Percorsi Service Fabric ---
SERVICE_TEMPLATES_PATH = PROJECT_ROOT / '3_service_templates'
SERVICE_CATALOG_PATH = PROJECT_ROOT / '6_service_catalog'
SERVICE_GENERATED_PATH = PROJECT_ROOT / '4_generated_services'


# --- Impostazioni di Sicurezza Fondamentali ---

# Carichiamo le variabili d'ambiente dal file .env.prod (T1)
# NON scrivere mai la chiave segreta qui.
SECRET_KEY = os.environ.get('SECRET_KEY')

# NON eseguire in produzione con DEBUG=True!
# 'DEBUG' sarà 'True' (stringa) se impostato a '1' o 'True' nel .env
DEBUG = os.environ.get('DEBUG', '0') == '1'

# ALLOWED_HOSTS deve essere configurato per la produzione.
# Per lo sviluppo Docker, '*' è accettabile, ma per la produzione
# dovremmo impostare i domini (es. 'tuodominio.com', 'localhost')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
ALLOWED_HOSTS.extend(
    ["localhost:443",
    "https://dryfus.one",
     "dryfus.one",
    "127.0.0.1",
    "192.168.178.140"]
)

# --- Definizione delle Applicazioni ---

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Applicazioni di terze parti
    'rest_framework',
    'rest_framework_simplejwt',
    'django.contrib.postgres',
    'pgcrypto',
    
    # Le nostre applicazioni (T3, T4, T5)
    'api.apps.Api1Config',     # App per API e Modelli
    'core',   # App per la logica (Generatore T5)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
    
]

WSGI_APPLICATION = 'myproject.wsgi.application'


# --- Database (T1, T3) ---
# Configurato per PostgreSQL usando variabili d'ambiente.
# Ispirato da

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': 'db',  # Questo è il nome del servizio nel docker-compose.yml (T1)
        'PORT': 5432,
    }
}


# --- Autenticazione (T3) ---

# Sostituiamo il modello User standard con il nostro Custom User Model (T3)
AUTH_USER_MODEL = 'api.User'


# --- Password validation ---
# (Standard Django)
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internazionalizzazione ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- File Statici (T1) ---

# URL per riferirsi ai file statici (es. /static/main.html)
STATIC_URL = '/static/'

# Dove 'collectstatic' (T1, entrypoint.sh) copierà i file.
# Questo percorso è condiviso con Nginx tramite 'static_volume'.
STATIC_ROOT = BASE_DIR / 'static'


# --- Tipi di Campo ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configurazione Django REST Framework (T4) ---
# Come da

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Usiamo JWT per l'autenticazione delle API
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Richiediamo l'autenticazione di default per tutti gli endpoint
        'rest_framework.permissions.IsAuthenticated', 
    ],
}


# --- Configurazione Simple JWT (T2, T4) ---

SIMPLE_JWT = {
    # Durata del token di accesso (breve)
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    # Durata del token di refresh (lunga)
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ISSUER': os.environ.get('DJANGO_JWT_ISSUER', 'servicefabric-development'),
    'AUDIENCE': os.environ.get('DJANGO_JWT_AUDIENCE', 'servicefabric-development'),
}
    # TBD (T10 - Sicurezza): Per una sicurezza avanzata,
    # potremmo impostare il refresh token per essere inviato
    # solo tramite cookie HttpOnly.

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080', 
    'http://127.0.0.1:8080',
    'http://dryfus.one',
    'https://dryfus.one',
    'https://proxy.dryfus.one',
]

# Aggiunge dinamicamente la porta del proxy configurata nel .env
_proxy_port = os.environ.get('PROXY_PORT')
if _proxy_port:
    CSRF_TRUSTED_ORIGINS.append(f'http://localhost:{_proxy_port}')
    CSRF_TRUSTED_ORIGINS.append(f'http://127.0.0.1:{_proxy_port}')
    # Se il proxy gestisce SSL o siamo in produzione, aggiungiamo anche https
    CSRF_TRUSTED_ORIGINS.append(f'https://localhost:{_proxy_port}')
    CSRF_TRUSTED_ORIGINS.append(f'https://127.0.0.1:{_proxy_port}')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTH_COOKIE_SECURE = os.environ.get('AUTH_COOKIE_SECURE', str(not DEBUG)).lower() in {'1', 'true', 'yes', 'on'}
AUTH_COOKIE_SAMESITE = os.environ.get('AUTH_COOKIE_SAMESITE', 'Lax')
AUTH_COOKIE_PATH = os.environ.get('AUTH_COOKIE_PATH', '/')
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = AUTH_COOKIE_SECURE
SESSION_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
CSRF_COOKIE_SECURE = AUTH_COOKIE_SECURE
CSRF_COOKIE_SAMESITE = AUTH_COOKIE_SAMESITE
