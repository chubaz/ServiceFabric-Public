# 5_core_services/flask_base/app/__init__.py
import os
from flask import Flask
from flask_cors import CORS  # <-- 1. Importa CORS
from app.config import Config
from app.extensions import db
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix
from jinja2 import ChoiceLoader, FileSystemLoader
from app.services_loader import register_all_services

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 2. Inizializza CORS qui, subito dopo aver creato 'app'
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}}, allow_headers=["Authorization", "Content-Type"])

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Fix: Theme manifest path should point to the correct location in the container
    app.config['THEME_MANIFEST_PATH'] = os.path.join('/app', 'services_catalog', 'component_repo', 'themes', 'theme_manifest.json')
    
    local_templates = "/app/app/templates"
    shared_templates = "/app/shared"

    # Preserve original loader to support Blueprints discovery
    original_loader = app.jinja_loader
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(local_templates),
        FileSystemLoader(shared_templates),
        original_loader
    ])
    
    app.config.update(
        TEMPLATES_AUTO_RELOAD=False,
        DEBUG=False 
    )
    app.jinja_env.auto_reload = False
    app.jinja_env.cache = {} 
    
    db.init_app(app)
    migrate = Migrate(app, db)

    from app.routes import core_bp, system_bp
    app.register_blueprint(core_bp)
    app.register_blueprint(system_bp)
    
    # ---------------------------------------------------------
    # ROUTE PER UTILITY CONDIVISE (_shared)
    # ---------------------------------------------------------
    @app.route('/_shared/<path:filename>')
    def serve_shared(filename):
        """Serve files from the _shared utility directory in the catalog."""
        from flask import send_from_directory
        # BASE_DIR è la root /app all'interno del container
        shared_dir = "/app/services_catalog/_shared"
        return send_from_directory(shared_dir, filename)
    
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    
    if db_uri and ('postgresql' in db_uri or 'postgres' in db_uri):
        try:
            # Legacy service imports are explicit and fail closed when disabled.
            if app.config['ENABLE_DYNAMIC_SERVICE_IMPORTS']:
                register_all_services(app)
            
            # THEN create tables within app context
            with app.app_context():
                db.create_all()
                app.logger.info("Database schema sincronizzato con modelli dinamici.")
                
        except Exception as e:
            app.logger.error(f"Errore durante l'inizializzazione dei servizi o del DB: {e}")

    return app
