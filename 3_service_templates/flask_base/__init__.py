from flask import Blueprint

# Blueprint standard per Service Fabric - Dynamic Shard Architecture
bp = Blueprint(
    '{{APP_SLUG}}', 
    __name__, 
    template_folder='templates',
    static_folder='static'
)

from . import routes
