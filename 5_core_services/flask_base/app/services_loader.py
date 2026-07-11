# 5_core_services/flask_base/app/services_loader.py
import os
import sys
import importlib.util
import threading # Aggiunto per gestire i lock
from pathlib import Path
from flask import current_app, g
from app.extensions import db
from app.service_manager import ServiceAssetsManager
import traceback

# Lock globale per evitare che più thread carichino moduli contemporaneamente
import_lock = threading.RLock()

def register_all_services(app, target_shard=None):
    """Dual-Mount System: Scansiona il catalogo ufficiale e la sandbox AI."""
    base_path = Path("/app")
    catalog_path = Path(app.config.get('SERVICE_CATALOG_PATH', base_path / 'services_catalog'))
    sandbox_path = Path(app.config.get('SERVICE_GENERATED_PATH', base_path / '4_generated_services'))

    for path in [catalog_path, sandbox_path]:
        if path.exists() and str(path) not in sys.path:
            sys.path.append(str(path))

    # Inizializza i pacchetti contenitore se non esistono
    for pkg in ["dynamic_catalog", "dynamic_sandbox"]:
        if pkg not in sys.modules:
            spec = importlib.machinery.ModuleSpec(pkg, None)
            module = importlib.util.module_from_spec(spec)
            sys.modules[pkg] = module

    # Montaggio dei servizi
    _mount_from_directory(app, catalog_path, "dynamic_catalog", prefix_base="", target_shard=target_shard)
    _mount_from_directory(app, sandbox_path, "dynamic_sandbox", prefix_base="/sandbox", target_shard=target_shard)

    # RIMOSSO db.create_all() da qui per evitare deadlock durante l'importazione

def load_active_services(app):
    """
    Inizializza e monta tutti i servizi attivi.
    """
    register_all_services(app)

def _mount_from_directory(app, directory, parent_pkg, prefix_base, target_shard=None):
    """Scansiona una directory e registra fisicamente i Blueprint trovati."""
    if not directory.exists(): return

    for item in directory.iterdir():
        if not item.is_dir() or item.name.startswith(('.', '_')): continue
        
        service_name = item.name
        if target_shard and service_name != target_shard: continue

        init_file = item / "__init__.py"
        if not init_file.exists(): continue

        module_name = f"{parent_pkg}.{service_name}"
        
        # Proteggiamo l'importazione dinamica con un lock
        with import_lock:
            try:
                # Pulizia selettiva: eliminiamo solo se necessario e con cautela
                if module_name in sys.modules:
                    # Invece di 'del', potremmo saltare se non è richiesto un reload forzato
                    if not app.config.get('FORCE_RELOAD_SERVICES', False):
                        app.logger.debug(f"Modulo {module_name} già caricato, skipping.")
                        # Procediamo comunque a controllare il Blueprint
                    else:
                        del sys.modules[module_name]
                        for m in list(sys.modules.keys()):
                            if m.startswith(module_name + "."): del sys.modules[m]

                spec = importlib.util.spec_from_file_location(module_name, str(init_file))
                if not spec or not spec.loader: continue
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                blueprint = getattr(module, 'bp', getattr(module, 'service_bp', None))
                if not blueprint: continue

                if blueprint.name in app.blueprints:
                    continue

                ServiceAssetsManager.configure_blueprint(app, blueprint, service_name)
                url_prefix = f"{prefix_base}/{service_name}".replace("//", "/")
                app.register_blueprint(blueprint, url_prefix=url_prefix)
                app.logger.info(f"[*] Fabric Node Mounted: '{service_name}'")

            except Exception as e:
                app.logger.error(f"Errore nel montaggio del servizio {service_name}: {e}")
                # Aggiungi questa riga per stampare lo stack trace completo:
                app.logger.error(traceback.format_exc())


def run_script_for_instance(instance, input_data):
    """
    Esegue lo script service.py associato all'istanza di un servizio dinamico.
    """
    service_name = instance.service_type
    base_path = Path("/app")
    search_paths = [
        Path(current_app.config.get('SERVICE_CATALOG_PATH', base_path / 'services_catalog')),
        Path(current_app.config.get('SERVICE_GENERATED_PATH', base_path / '4_generated_services'))
    ]
    
    script_path = None
    target_dir = None
    
    for p in search_paths:
        potential_dir = p / service_name
        potential_script = potential_dir / 'service.py'
        if potential_script.exists():
            script_path = potential_script
            target_dir = potential_dir
            break
            
    if not script_path: 
        raise FileNotFoundError(f"Script service.py non trovato per {service_name}")
        
    module_name = f"dynamic_script.{service_name}_{instance.id}"
    
    # Protezione del lock per sys.modules (opzionale qui, ma buona pratica visto il refactor)
    with import_lock:
        if module_name in sys.modules: 
            del sys.modules[module_name]
            
        spec = importlib.util.spec_from_file_location(module_name, str(script_path))
        module = importlib.util.module_from_spec(spec)
        
    if str(target_dir) not in sys.path: 
        sys.path.insert(0, str(target_dir))
        
    try:
        spec.loader.exec_module(module)
        if not hasattr(module, 'ServiceRunner'): 
            raise AttributeError(f"Classe ServiceRunner non trovata in {script_path}")
            
        context = {
            'user_id': g.user_id, 
            'instance_id': str(instance.id), 
            'config': instance.state_config, 
            'logger': current_app.logger
        }
        runner = module.ServiceRunner(context)
        return runner.run(input_data)
        
    finally:
        if str(target_dir) in sys.path: 
            sys.path.remove(str(target_dir))