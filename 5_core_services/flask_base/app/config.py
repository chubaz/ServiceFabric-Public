import os
import sys

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
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    # Percorso dove risiedono i Blueprints (Service Catalog)
    SERVICE_CATALOG_PATH = os.environ.get('SERVICE_CATALOG_PATH', '/app/services_catalog')
    USER_MEDIA_ROOT = os.environ.get('USER_MEDIA_ROOT', '/app/user_media')