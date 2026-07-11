from flask import g, request, render_template, jsonify
from app.extensions import db
from app.utils import smart_render
from . import bp
from .models import {{APP_SLUG}}Item
from _shared.utils.fabric_sdk import fabric

@bp.route('/')
def index():
    """
    Carica la Shell Locale dello Shard. 
    Questa è la pagina principale caricata dalla Shell Globale.
    """
    state_config = g.get('state_config', {})
    theme_color = state_config.get('theme_color', 'indigo')
    
    # Notify Gateway that a user has accessed this shard
    fabric.broadcast("shard_accessed", {"slug": "{{APP_SLUG}}", "user_id": g.get('user_id')})
    
    return smart_render(
        '{{APP_SLUG}}/index.html',
        app_name="{{APP_NAME}}",
        app_slug="{{APP_SLUG}}",
        theme_color=theme_color,
        initial_view='dashboard'
    )

@bp.route('/health')
def health():
    """Standard health check for Gateway Orchestration."""
    return jsonify({
        "status": "online",
        "service": "{{APP_SLUG}}",
        "type": "flask_shard"
    })

@bp.route('/views/dashboard')
def view_dashboard():
    """Restituisce solo il frammento HTML della Dashboard via HTMX."""
    user_id = getattr(g, 'user_id', 1)
    items = {{APP_SLUG}}Item.query.filter_by(owner_id=user_id).all()
    return render_template(
        '{{APP_SLUG}}/views/dashboard.html',
        app_slug="{{APP_SLUG}}",
        items=items
    )

@bp.route('/api/sync', methods=['POST'])
@fabric.notify_on_change("{{APP_SLUG}}_sync_completed")
def api_sync():
    """
    Example API endpoint that notifies the Gateway on success.
    The @fabric.notify_on_change decorator automatically broadcasts an event.
    """
    data = request.json
    return jsonify({
        "status": "success",
        "msg": f"Shard {{APP_SLUG}} synced successfully",
        "received": data
    })

@bp.route('/api/ping', methods=['POST'])
def api_ping():
    """
    Manual broadcast example for custom real-time messaging.
    """
    fabric.broadcast("{{APP_SLUG}}_ping", {"msg": "Ping from backend", "user_id": g.get('user_id')})
    return jsonify({"status": "broadcasted"})

@bp.route('/views/settings')
def view_settings():
    """Restituisce solo il frammento HTML delle Impostazioni via HTMX."""
    state_config = g.get('state_config', {})
    return render_template(
        '{{APP_SLUG}}/views/settings.html',
        app_slug="{{APP_SLUG}}",
        config=state_config
    )
