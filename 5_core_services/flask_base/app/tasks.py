# 5_core_services/flask_base/app/tasks.py
import importlib
import logging
import uuid
from flask import current_app
from app.service_security import ServiceAccessDenied, validate_identifier

logger = logging.getLogger("service_fabric.tasks")
logger.setLevel(logging.INFO)

def run_catalog_job(catalog_app_name, module_name, function_name, kwargs, room_id=None):
    """
    Synchronous version of the catalog job runner without Celery/SocketIO.
    """
    # Generate a random ID since we no longer have self.request.id from Celery
    audit_id = uuid.uuid4().hex[:8] 
    
    logger.info(f"[{audit_id}] 📥 Task ricevuto per {catalog_app_name}.{function_name}")

    try:
        catalog_app_name = validate_identifier(catalog_app_name)
        if not current_app.config['ENABLE_DYNAMIC_SERVICE_IMPORTS']:
            raise ServiceAccessDenied('Legacy catalogue jobs are disabled')
        if current_app.config['IS_PRODUCTION'] and catalog_app_name not in current_app.config['LEGACY_CATALOG_ALLOWLIST']:
            raise ServiceAccessDenied('Legacy catalogue job is not allowed')
        module_parts = module_name.split('.') if isinstance(module_name, str) else []
        if not module_parts or any(not part.isidentifier() for part in module_parts):
            raise ServiceAccessDenied('Invalid legacy module target')
        if not isinstance(function_name, str) or not function_name.isidentifier():
            raise ServiceAccessDenied('Invalid legacy function target')
        # STEP 1: Audit del caricamento modulo
        logger.info(f"[{audit_id}] 🔍 Tentativo di importazione: {catalog_app_name}.{module_name}")
        module_path = f"{catalog_app_name}.{module_name}"
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        
        # STEP 2: Audit pre-esecuzione
        logger.info(f"[{audit_id}] 🚀 Chiamata alla funzione {function_name}...")

        # STEP 3: Esecuzione
        result = func(**kwargs)

        # STEP 4: Audit successo
        logger.info(f"[{audit_id}] ✅ Funzione completata con successo.")
            
        return result

    except Exception as e:
        # STEP 5: Audit fallimento
        logger.error(f"[{audit_id}] ❌ ERRORE CRITICO: {str(e)}", exc_info=True)
        raise e
