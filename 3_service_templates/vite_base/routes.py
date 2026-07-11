from flask import g, jsonify, request
from app.extensions import db
from app.utils import smart_render
from . import bp
from .models import {{APP_SLUG}}Entity

@bp.route('/')
def index():
    """Renderizza lo Shard con Double Hydration."""
    db.create_all()

    # Estrazione contesto Service Fabric
    state_config = g.get('state_config', {})
    app_data = g.get('app_data', {})

    return smart_render(
        '{{APP_SLUG}}/index.html',
        app_name="{{APP_NAME}}",
        app_slug="{{APP_SLUG}}",
        state_config=state_config,
        app_data=app_data
    )

@bp.route('/api/entities', methods=['GET', 'POST'])
def handle_entities():
    user_id = getattr(g, 'user_id', 1)

    if request.method == 'POST':
        data = request.json
        new_entity = {{APP_SLUG}}Entity(
            owner_id=user_id,
            label=data.get('label', 'Untitled'),
            payload=data.get('data', {})
        )
        db.session.add(new_entity)
        db.session.commit()
        return jsonify(new_entity.to_dict()), 201

    entities = {{APP_SLUG}}Entity.query.filter_by(owner_id=user_id).all()
    return jsonify([e.to_dict() for e in entities])
