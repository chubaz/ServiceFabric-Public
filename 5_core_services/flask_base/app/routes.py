import os
import time
import signal
import threading
from flask import Blueprint, jsonify, g, current_app, request, abort, session
from werkzeug.utils import secure_filename
from app.middleware import token_required
from app.models import ServiceInstance
from app.extensions import db
# Assumiamo che questa funzione esista nel loader (definito in Fase 7)
from app.services_loader import run_script_for_instance, register_all_services 

# Creiamo il Blueprint per le API del Core
core_bp = Blueprint('core', __name__)

# Blueprint per operazioni di sistema (Reload, Health, etc.)
system_bp = Blueprint('system', __name__)

# ==============================================================================
# 0. SYSTEM INTERNAL OPERATIONS (COLD RELOAD)
# ==============================================================================

def _async_surgical_reload(app, target):
    """Esegue il reload chirurgico in un thread separato per non bloccare il worker."""
    import time
    time.sleep(1.0)
    with app.app_context():
        try:
            app.logger.info(f"🔄 Surgical Reload in corso per shard: {target}")
            register_all_services(app, target_shard=target)
            app.logger.info(f"✅ Surgical Reload completato per shard: {target}")
        except Exception as e:
            app.logger.error(f"❌ Errore durante il reload chirurgico di {target}: {e}")

@system_bp.route('/_internal/reload', methods=['POST'])
def internal_reload():
    """
    Meccanismo di Reload:
    1. Se viene fornito un 'target' nel JSON, esegue un reload chirurgico (senza restart worker).
       Ritorna 202 immediatamente e il reload procede in background.
    2. Altrimenti, tenta Cold Reload via SIGHUP al master process (Gunicorn).
    """
    data = request.get_json() or {}
    target = data.get('target')

    if target:
        current_app.logger.info(f"⚡ Surgical Reload richiesto per shard: {target}")
        # Lancio il reload in un thread separato per rispondere subito
        app = current_app._get_current_object()
        t = threading.Thread(target=_async_surgical_reload, args=(app, target), daemon=True)
        t.start()
        return jsonify({
            "status": "accepted",
            "message": f"Surgical reload per shard '{target}' avviato in background.",
            "type": "surgical_async"
        }), 202

    try:
        # Tenta di inviare SIGHUP al processo master
        os.kill(os.getppid(), signal.SIGHUP)
        return jsonify({
            "status": "success",
            "message": "SIGHUP inviato al master process per Cold Reload.",
            "type": "cold"
        }), 200
    except Exception as e:
        # Fallback per ambiente di sviluppo o se os.kill fallisce
        current_app.logger.warning(f"SIGHUP fallito, eseguo register_all_services: {e}")
        try:
            register_all_services(current_app)
            return jsonify({
                "status": "partial_success",
                "message": "SIGHUP fallito. Servizi ricaricati programmaticamente tramite register_all_services.",
                "detail": str(e)
            }), 200
        except Exception as ex:
            return jsonify({
                "status": "error",
                "message": "Errore critico durante il ricaricamento servizi.",
                "detail": str(ex)
            }), 500

# ==============================================================================
# 1. SYSTEM & DEBUG ROUTES
# ==============================================================================

@core_bp.route('/status', methods=['GET'])
def public_status():
    """Route pubblica per Health Check (Docker/K8s)"""
    return jsonify({
        "status": "Flask Core is running", 
        "version": "1.0.0",
        "auth": "not required"
    })

@core_bp.route('/debug/me', methods=['GET'])
@token_required
def debug_me():
    """
    Route protetta per testare il Middleware.
    """
    return jsonify({
        "message": "Autenticazione riuscita!",
        "authenticated_user_id": g.user_id,
        "tenant_scope": f"User {g.user_id}"
    })

@core_bp.route('/_debug_environ')
def debug_environ():
    return jsonify({
        'SCRIPT_NAME': request.environ.get('SCRIPT_NAME'),
        'PATH_INFO': request.environ.get('PATH_INFO'),
        'RAW_URI': request.environ.get('RAW_URI') or request.environ.get('REQUEST_URI'),
        'X-Fwd-Prefix': request.headers.get('X-Forwarded-Prefix'),
    })

# ==============================================================================
# 2. DYNAMIC EXECUTION (FaaS Engine)
# ==============================================================================

@core_bp.route('/execute/<uuid:instance_id>', methods=['POST'])
@token_required
def execute_service(instance_id):
    """
    Esegue uno script Python 'on-the-fly' associato a un'istanza.
    Utile per servizi che non sono Web App complete (Blueprints), 
    ma semplici funzioni di calcolo (stile AWS Lambda).
    """
    # 1. Recupero e Validazione Istanza
    # È CRUCIALE filtrare per owner_id (g.user_id) per evitare che l'Utente A esegua script dell'Utente B
    instance = ServiceInstance.query.filter_by(
        id=instance_id, 
        owner_id=g.user_id
    ).first()

    if not instance:
        return jsonify({"error": "Service Instance not found or access denied"}), 404

    if not instance.is_active:
        return jsonify({"error": "Service is inactive"}), 403

    # 2. Parsing Dati in Input
    # Passiamo i dati JSON inviati dal client allo script
    input_data = request.get_json() or {}

    try:
        # 3. Esecuzione Dinamica (Tramite Loader)
        # Questa funzione caricherà il file 'service.py' dalla cartella dell'istanza
        # e lancerà il metodo .run(context, input_data)
        
        start_time = time.time()
        result = run_script_for_instance(instance, input_data)
        execution_time = time.time() - start_time

        return jsonify({
            "status": "success",
            "execution_time_ms": round(execution_time * 1000, 2),
            "result": result
        })

    except Exception as e:
        current_app.logger.error(f"Execution error for {instance_id}: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "Script execution failed", 
            "details": str(e)
        }), 500

# ==============================================================================
# 3. SHARED UTILITIES (Hybrid Helpers)
# Queste funzioni sono usate da TUTTI i servizi per operazioni comuni
# ==============================================================================

@core_bp.route('/utils/upload', methods=['POST'])
@token_required
def upload_file():
    """
    Gestore Universale Upload.
    Salva i file nella cartella isolata dell'utente: /app/user_media/user_ID/
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        
        # Costruzione path isolato
        user_media_path = os.path.join(current_app.config['USER_MEDIA_ROOT'], str(g.user_id))
        
        # Assicura che la cartella esista
        os.makedirs(user_media_path, exist_ok=True)
        
        save_path = os.path.join(user_media_path, filename)
        file.save(save_path)

        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "internal_path": save_path, # Utile per passarlo a Celery
            "url": f"/media/{g.user_id}/{filename}" # URL pubblico (se servito da Nginx)
        })

@core_bp.route('/utils/storage/list', methods=['GET'])
@token_required
def list_user_files():
    """
    Elenca i file presenti nello storage dell'utente.
    """
    user_media_path = os.path.join(current_app.config['USER_MEDIA_ROOT'], str(g.user_id))
    
    if not os.path.exists(user_media_path):
        return jsonify({"files": []})
        
    try:
        files = os.listdir(user_media_path)
        file_details = []
        for f in files:
            full_path = os.path.join(user_media_path, f)
            if os.path.isfile(full_path):
                file_details.append({
                    "name": f,
                    "size_bytes": os.path.getsize(full_path),
                    "modified": time.ctime(os.path.getmtime(full_path))
                })
        return jsonify({"files": file_details})
    except Exception as e:
        return jsonify({"error": str(e)}), 500