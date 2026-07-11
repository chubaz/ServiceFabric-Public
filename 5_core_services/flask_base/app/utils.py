from flask import request, render_template, current_app
import json


def get_theme_context():
    """
    Loads the theme manifest for use in Jinja templates.
    NOTE: In a production environment, this file should be compiled/cached 
    to avoid reading the file system on every request.
    """
    try:
        # Assuming the manifest is accessible via a path (or loaded into app config)
        manifest_path = current_app.config.get('THEME_MANIFEST_PATH', 
                                              '/app/component_repo/themes/theme_manifest.json')
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        current_app.logger.error(f"Error loading theme manifest: {e}")
        # Fallback dictionary if file is missing
        return {"color_palette": {"primary": "#f59e0b"}, "typography": {"font_family": "sans-serif"}, "layout": {"header_height_px": 64}}


def smart_render(partial_name, **context):
    """
    Intelligent Renderer for Micro-Frontend Integration.
    
    1. If request is from HTMX (Core wrapper): Renders ONLY the partial template.
    2. If request is direct (Browser): Renders the 'fallback' wrapper which extends 
       the Shared Base and injects the partial.
    """
    
    theme_context = get_theme_context()
    context['theme'] = theme_context
    
    # Ensure 'service' exists in context for service_wrapper.html
    if 'service' not in context:
        # Try to guess the service name from the blueprint
        service_name = "Unknown Service"
        if request.blueprint:
            service_name = request.blueprint.replace('_', ' ').title()
        
        context['service'] = {
            'name': service_name,
            'slug': request.blueprint or 'unknown'
        }
    
    # Check for HTMX header
    is_htmx = request.headers.get('HX-Request') == 'true'

    if is_htmx:
        # Just return the content. The 'Core' already has the <head> and <body>
        current_app.logger.debug(f"HTMX request detected. Rendering partial: {partial_name}")

        return render_template(partial_name, **context)
    
    else:
        # FALLBACK: The user opened the link in a new tab.
        # We render a special 'wrapper.html' that extends the SHARED base.html
        # and places the specific template inside the content block.
        current_app.logger.info(f"Full browser request. Rendering wrapped page for: {partial_name}")

        context['partial_template'] = partial_name
        return render_template('core/fallback_wrapper.html', **context)