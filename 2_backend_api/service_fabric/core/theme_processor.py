import json
import os
from django.conf import settings

def theme_context(request):
    """
    Loads the theme manifest and makes it available to all templates.
    """
    # Define path relative to the Django project root
    # Adjust '..' based on your actual structure relative to manage.py
    manifest_path = os.path.join(settings.BASE_DIR, '..', '..', 'component-repository', 'themes', 'theme_manifest.json')
    
    default_theme = {
        "color_palette": {"primary": "#f59e0b", "background_dark": "#0f172a"},
        "typography": {"font_family": "sans-serif"}
    }

    try:
        with open(manifest_path, 'r') as f:
            theme_data = json.load(f)
        return {'theme': theme_data}
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback if file is missing/corrupt
        return {'theme': default_theme}