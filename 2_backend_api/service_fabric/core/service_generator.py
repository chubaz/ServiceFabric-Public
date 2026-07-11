# 2_backend_api/service_fabric/core/service_generator.py

import os
import shutil
import urllib.request
import logging
from pathlib import Path
from django.conf import settings
from api.models import ServiceTemplate, ServiceApp

logger = logging.getLogger(__name__)

def trigger_reloads(template_key: str):
    """
    Invia segnali di reload ai container core per attivare la nuova app.
    1. Flask Core: ricarica i Blueprint dinamici.
    2. Frontend Builder (React o Vite): lancia la compilazione.
    """
    # --- 1. RELOAD FLASK CORE ---
    try:
        flask_reload_url = "http://core_flask_service:5000/_internal/reload"
        req = urllib.request.Request(flask_reload_url, method='POST')
        with urllib.request.urlopen(req, timeout=5) as response:
            logger.info(f"✅ Flask Reload triggered: {response.read().decode()}")
    except Exception as e:
        logger.error(f"⚠️ Flask Reload failed (continuing anyway): {e}")

    # --- 2. RELOAD FRONTEND BUILDER ---
    # Determiniamo quale builder chiamare in base al template_key
    frontend_service = None
    if 'react' in template_key.lower():
        frontend_service = "core_react_service"
    elif 'vite' in template_key.lower():
        frontend_service = "core_vite_service"
    
    if frontend_service:
        try:
            frontend_reload_url = f"http://{frontend_service}:3000/_internal/reload"
            req = urllib.request.Request(frontend_reload_url, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                logger.info(f"✅ Frontend Builder ({frontend_service}) triggered: {response.read().decode()}")
        except Exception as e:
            logger.error(f"⚠️ Frontend Reload failed for {frontend_service} (continuing anyway): {e}")

def generate_service_app(template_key: str, new_app_name: str, new_app_slug: str, user=None) -> ServiceApp:
    """
    La Fabbrica: Clona fisicamente una cartella da 3_service_templates a 6_service_catalog
    e registra il risultato nel database come nuova ServiceApp.
    """
    
    # 1. Trova il Boilerplate nel DB
    template = ServiceTemplate.objects.get(template_key=template_key)

    # 2. Risoluzione dei Percorsi (Paths)
    # Usiamo i percorsi centralizzati definiti in settings.py
    templates_dir = Path(settings.SERVICE_TEMPLATES_PATH)
    catalog_dir = Path(settings.SERVICE_CATALOG_PATH)

    source_path = templates_dir / template.template_key
    dest_path = catalog_dir / new_app_slug

    # Validazione di sicurezza prima di scrivere su disco
    if not source_path.exists():
        raise FileNotFoundError(f"Errore: Il boilerplate '{template.template_key}' non esiste sul disco ({source_path}).")
    
    if dest_path.exists():
        raise FileExistsError(f"Errore: Esiste già una cartella con lo slug '{new_app_slug}' nel catalogo.")

    # 3. Clonazione Fisica (I/O)
    try:
        shutil.copytree(
            source_path, 
            dest_path, 
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git', 'node_modules')
        )
    except Exception as e:
        raise RuntimeError(f"Errore critico durante la copia dei file: {str(e)}")

    # 4. Personalizzazione Dinamica del Codice Sorgente
    _customize_blueprint_files(dest_path, new_app_name, new_app_slug)

    # 5. Generazione .cursorrules per AI Context
    _create_cursorrules(dest_path, new_app_slug)

    # 6. Registrazione dell'App Generata nel Database
    new_app = ServiceApp.objects.create(
        name=new_app_name,
        app_slug=new_app_slug,
        description=f"Generato automaticamente da {template.name}.",
        template_source=template,
        # Impostiamo un DNA di base generico per chi installerà questa app
        default_state_config={"theme": "light", "title": new_app_name},
        default_app_data={}
    )
    
    # Se l'utente è specificato, diventa l'owner (sviluppatore) di questo Blueprint
    if user:
        new_app.owners.add(user)

    # 6. TRIGGER RELOADS (Integrazione Cold Reload)
    # Eseguiamo i reload affinché la nuova app sia visibile e compilata immediatamente
    trigger_reloads(template_key)

    return new_app


def _customize_blueprint_files(folder_path: Path, app_name: str, app_slug: str):
    """
    Cerca all'interno della nuova cartella clonata e sostituisce le variabili
    placeholder con i nomi reali, gestendo la sanificazione per Python.
    """
    # 1. Preparazione varianti dello slug
    slug_snake = app_slug.replace('-', '_') 
    slug_camel = "".join(x.capitalize() for x in app_slug.replace('-', '_').split('_')) 

    # 2. Ridenominazione Directory (MANTENIAMO IL TRATTINO per Flask Core Mounting)
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for dir_name in dirs:
            if '{{APP_SLUG}}' in dir_name:
                old_dir_path = os.path.join(root, dir_name)
                new_dir_name = dir_name.replace('{{APP_SLUG}}', app_slug)
                new_dir_path = os.path.join(root, new_dir_name)
                os.rename(old_dir_path, new_dir_path)

    # 3. Sostituzione Contenuto File
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            if file_name.endswith(('.py', '.json', '.html', '.js', '.jsx', '.ts', '.tsx', '.md', '.css')):
                file_path = os.path.join(root, file_name)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if any(p in content for p in ['{{APP_NAME}}', '{{APP_SLUG}}']):
                        content = content.replace('{{APP_NAME}}', app_name)
                        
                        if file_name.endswith('.py'):
                            # Sostituzioni per identificatori Python (classi e tabelle)
                            content = content.replace('class {{APP_SLUG}}', f'class {slug_camel}')
                            content = content.replace('{{APP_SLUG}}Item', f'{slug_camel}Item')
                            content = content.replace('{{APP_SLUG}}Entity', f'{slug_camel}Entity')
                            content = content.replace('srv_{{APP_SLUG}}', f'srv_{slug_snake}')
                            # Per stringhe (Blueprint names, template paths): MANTENIAMO IL TRATTINO
                            content = content.replace('{{APP_SLUG}}', app_slug)
                        elif file_name.endswith('.html'):
                            # FIX CRITICO JS: window.SF_CONTEXT_{{APP_SLUG}} -> window["SF_CONTEXT_{{APP_SLUG}}"]
                            # Questo evita SyntaxError dovuti ai trattini interpretati come sottrazioni
                            content = content.replace('window.SF_CONTEXT_{{APP_SLUG}}', f'window["SF_CONTEXT_{app_slug}"]')
                            content = content.replace('{{APP_SLUG}}', app_slug)
                        else:
                            # Altri file (JS, CSS): MANTENIAMO IL TRATTINO
                            content = content.replace('{{APP_SLUG}}', app_slug)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                except UnicodeDecodeError:
                    pass

def _create_cursorrules(dest_path: Path, app_slug: str):
    """
    Crea un file .cursorrules con istruzioni AI specifiche per il progetto Service Fabric.
    """
    cursorrules_content = f"""# Service Fabric AI Context - {app_slug}

## Infrastructure & Stack
- Frontend: Svelte 5 (Runes)
- Backend: Flask (Python)
- Styling: Tailwind CSS

## Architecture & Database
- Database: NEVER create new SQLite DBs.
- Shared Models: Use the shared environment 'models.py' for this shard.
- Registry: This app is automatically mounted by the Fabric Core.

## Security Mandates
- Every backend route MUST filter data by 'owner_id=user_id' (available via flask.g).
- Always use the @token_required decorator for protected routes.

## Development Workflow
- No container restarts required.
- Deployment/Reload: Use the global CLI command at project root:
  `./fabric rebuild {app_slug}`
- Testing:
  `./fabric test {app_slug}`

## Cursor Specifics
- Always respect the directory structure:
  - src/ -> Svelte logic
  - templates/ -> Flask/Jinja2 entry points
  - routes.py -> Flask Blueprint endpoints
"""
    cursorrules_path = dest_path / ".cursorrules"
    try:
        with open(cursorrules_path, 'w', encoding='utf-8') as f:
            f.write(cursorrules_content)
        logger.info(f"✅ .cursorrules generated for {app_slug}")
    except Exception as e:
        logger.error(f"⚠️ Failed to create .cursorrules for {app_slug}: {e}")

def start_service_creation_task(template_key, app_name, app_slug, user):
    """
    Ponte per la creazione asincrona. Per ora esegue la generazione 
    in modo sincrono per permettere il test immediato.
    """
    return generate_service_app(template_key, app_name, app_slug, user)