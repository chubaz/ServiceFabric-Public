#!/usr/bin/env
"""
Utilità da riga di comando di Django per le attività amministrative.
"""
import os
import sys

def main():
    """Esegue le attività amministrative."""
    
    # Imposta il percorso del file di impostazioni (settings.py)
    # in modo che manage.py sappia quale progetto sta gestendo.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
        
    # Passa gli argomenti della riga di comando (es. "migrate")
    # a Django per l'esecuzione.
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()