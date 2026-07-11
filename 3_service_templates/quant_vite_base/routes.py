from flask import g, jsonify, request
from app.extensions import db
from app.utils import smart_render
from . import bp
from .models import {{APP_SLUG}}Entity
from _shared.utils.fabric_sdk import fabric
import random # Placeholder for engine logic

@bp.route('/')
def index():
    """Render the Quant Terminal shell."""
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

@bp.route('/api/calculate-pnl')
def calculate_pnl():
    """
    Endpoint: Calculate live PnL and broadcast via Fabric Gateway.
    """
    # Simulated PnL Logic
    pnl_value = round(random.uniform(-500, 1500), 2)
    pnl_data = {
        "value": pnl_value,
        "slug": "{{APP_SLUG}}",
        "currency": "USD",
        "timestamp": g.get('now', 'just now')
    }
    
    # Broadcast to the entire fabric dashboard for real-time monitoring
    fabric.broadcast("pnl_update", pnl_data)
    
    return jsonify(pnl_data)

@bp.route('/api/backtest-results', methods=['GET'])
def get_results():
    """Endpoint: Retrieve historical Alpha-factor performance."""
    return jsonify({"status": "active", "performance": [0.01, 0.02, -0.005]})

@bp.route('/api/rebalance', methods=['POST'])
def run_rebalance():
    """Endpoint: Trigger portfolio rebalancing logic."""
    fabric.broadcast("signal_alert", {"msg": "Portfolio Rebalanced", "slug": "{{APP_SLUG}}"})
    return jsonify({"status": "success", "msg": "Rebalance triggered"})
