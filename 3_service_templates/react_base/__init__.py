from flask import Blueprint
import os

# Definizione del Blueprint standard per Service Fabric.
bp = Blueprint(
    '{{APP_SLUG}}',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/flask_static/assets'
)

from . import routes
