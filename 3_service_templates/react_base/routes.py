from flask import g, jsonify, request, render_template
from app.extensions import db
from app.utils import smart_render
from . import bp
from .models import {{APP_SLUG}}Item

@bp.route('/', methods=['GET'])
def serve_main():
    """
    Renderizza lo Shard.
    Passa state_config e app_data dal Gateway per la Double Hydration.
    """
    # Assicura che le tabelle esistano
    db.create_all()

    state_config = g.get('state_config', {})
    app_data = g.get('app_data', {})

    return smart_render(
        '{{APP_SLUG}}/index.html',
        app_name="{{APP_NAME}}",
        app_slug="{{APP_SLUG}}",
        state_config=state_config,
        app_data=app_data
    )

@bp.route('/api/items', methods=['GET'])
def list_items():
    user_id = getattr(g, 'user_id', 1)
    items = {{APP_SLUG}}Item.query.filter_by(owner_id=user_id).all()
    return jsonify([i.to_dict() for i in items])

@bp.route('/api/sync', methods=['POST'])
def sync_data():
    """Riceve aggiornamenti dallo Shard React."""
    payload = request.json
    return jsonify({"status": "success", "msg": "Handshake completato"})
