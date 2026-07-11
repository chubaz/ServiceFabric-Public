import os
import sys


def _flag(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _csv(name):
    return frozenset(item.strip() for item in os.environ.get(name, "").split(",") if item.strip())

class Config:
    # Sicurezza
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Chiave segreta condivisa con Django per validare i JWT
    DJANGO_SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')

    if not SECRET_KEY or not DJANGO_SECRET_KEY:
        error_msg = "\n" + "!"*60 + "\n"
        error_msg += "CRITICAL SECURITY ERROR: SECRET_KEY or DJANGO_SECRET_KEY missing!\n"
        error_msg += "These environment variables are required for secure operations.\n"
        error_msg += "!"*60 + "\n"
        sys.stderr.write(error_msg)
        # Note: We don't raise RuntimeError here to allow the process to start
        # and report the error through logs/stderr, similar to DATABASE_URL logic.

    # Database (Stesso di Django)
    db_url = os.environ.get('DATABASE_URL')
    # 2. Se manca, AVVISA ma NON CRASHARE
    if not db_url:
        error_msg = "\n\n" + "="*60 + "\n"
        error_msg += "CRITICAL WARNING: 'DATABASE_URL' non trovata!\n"
        error_msg += "L'app userà SQLite temporaneo per avviarsi e mostrarti questo errore.\n"
        error_msg += "VERIFICA IL TUO FILE .env E DOCKER-COMPOSE.\n"
        error_msg += "="*60 + "\n\n"
        sys.stderr.write(error_msg)
        
        # Fallback a SQLite in memoria per permettere il boot di Gunicorn
        # Questo database è vuoto e volatile, ma evita il RuntimeError immediato
        db_url = 'sqlite:///:memory:' 
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASK_ENVIRONMENT = os.environ.get('FLASK_ENVIRONMENT', os.environ.get('FABRIC_ENVIRONMENT', 'production')).lower()
    IS_PRODUCTION = FLASK_ENVIRONMENT == 'production'

    # Legacy dynamic behaviour is opt-in. Production also requires an explicit catalogue allowlist.
    ENABLE_DYNAMIC_SERVICE_IMPORTS = _flag('ENABLE_DYNAMIC_SERVICE_IMPORTS')
    ENABLE_GENERATED_SERVICE_IMPORTS = _flag('ENABLE_GENERATED_SERVICE_IMPORTS') and not IS_PRODUCTION
    ENABLE_LEGACY_FAAS_EXECUTION = _flag('ENABLE_LEGACY_FAAS_EXECUTION') and not IS_PRODUCTION
    ENABLE_INTERNAL_RELOAD = _flag('ENABLE_INTERNAL_RELOAD') and not IS_PRODUCTION
    ENABLE_DEBUG_ROUTES = _flag('ENABLE_DEBUG_ROUTES') and not IS_PRODUCTION
    LEGACY_CATALOG_ALLOWLIST = _csv('LEGACY_CATALOG_ALLOWLIST')
    INTERNAL_RELOAD_ALLOWED_SERVICES = _csv('INTERNAL_RELOAD_ALLOWED_SERVICES')
    INTERNAL_RELOAD_ALLOWED_TARGETS = _csv('INTERNAL_RELOAD_ALLOWED_TARGETS')
    INTERNAL_RELOAD_TOKEN = os.environ.get('INTERNAL_RELOAD_TOKEN')

    MAX_UPLOAD_BYTES = int(os.environ.get('MAX_UPLOAD_BYTES', 10 * 1024 * 1024))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_BYTES
    UPLOAD_ALLOWED_EXTENSIONS = _csv('UPLOAD_ALLOWED_EXTENSIONS') or frozenset({
        'csv', 'json', 'jpeg', 'jpg', 'pdf', 'png', 'txt'
    })

    # Percorso dove risiedono i Blueprints (Service Catalog)
    SERVICE_CATALOG_PATH = os.environ.get('SERVICE_CATALOG_PATH', '/app/services_catalog')
    SERVICE_GENERATED_PATH = os.environ.get('SERVICE_GENERATED_PATH', '/app/4_generated_services')
    USER_MEDIA_ROOT = os.environ.get('USER_MEDIA_ROOT', '/app/user_media')
