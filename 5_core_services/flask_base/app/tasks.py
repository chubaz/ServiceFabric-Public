# 5_core_services/flask_base/app/tasks.py
import importlib
import logging
import uuid

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