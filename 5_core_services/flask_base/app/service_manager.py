import os
from flask import current_app
from app.service_security import validate_identifier

class ServiceAssetsManager:
    """
    Helper to align Flask Blueprints with the Docker Volume structure
    created by the Central Vite Builder.
    """
    
    @staticmethod
    def configure_blueprint(app, blueprint, service_name):
        """
        Overrides the blueprint's static folder configuration to point 
        to the shared volume mount.
        """
        service_name = validate_identifier(service_name)
        # 1. Get the global mount point from Flask Config (set by Env Var)
        # Defaults to /app/static_assets if not set
        assets_root = app.config.get('STATIC_ASSETS_PATH', '/app/flask_static')
        
        # 2. Construct the specific path for this service
        # builder.js outputs to: /app/dist/{service_name}
        # Flask sees it at:      /app/static_assets/{service_name}
        service_assets_path = os.path.join(assets_root, service_name)
        
        # 3. Configure the Blueprint
        # We enforce this path regardless of what's in the service's __init__.py
        blueprint.static_folder = service_assets_path
        
        # 4. Set the URL prefix for the browser
        # Browser requests: /static/assets/index.js (prefixed by blueprint url_prefix)
        blueprint.static_url_path = "/static"
        
        app.logger.info(f"🔧 [Assets] Linked {service_name} -> {service_assets_path}")
        return blueprint
