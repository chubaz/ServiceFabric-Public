import hmac
import uuid
from functools import wraps

import jwt
from flask import abort, current_app, g, jsonify, request


def _authentication_error():
    return jsonify({'message': 'Invalid or missing credentials'}), 401


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('sf_access_token')
        authorization = request.headers.get('Authorization', '')
        if not token and authorization:
            scheme, _, bearer_token = authorization.partition(' ')
            if scheme.lower() == 'bearer' and bearer_token:
                token = bearer_token
        if not token:
            return _authentication_error()

        secret_key = current_app.config.get('DJANGO_SECRET_KEY')
        if not secret_key:
            current_app.logger.error('Flask JWT verification is not configured')
            return jsonify({'message': 'Authentication is unavailable'}), 503

        try:
            payload = jwt.decode(
                token,
                secret_key,
                algorithms=current_app.config['DJANGO_JWT_ALGORITHMS'],
                issuer=current_app.config['DJANGO_JWT_ISSUER'],
                audience=current_app.config['DJANGO_JWT_AUDIENCE'],
                options={'require': ['exp', 'user_id', 'token_type']},
            )
            if payload.get('token_type') != current_app.config['DJANGO_JWT_TOKEN_TYPE']:
                return _authentication_error()
            g.user_id = uuid.UUID(str(payload['user_id']))
        except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
            return _authentication_error()

        return f(*args, **kwargs)

    return decorated


def reload_service_required(f):
    """Authorize development reloads using a configured service identity and secret."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config['ENABLE_INTERNAL_RELOAD']:
            abort(404)

        service_id = request.headers.get('X-Service-Identity', '')
        token = request.headers.get('X-Internal-Reload-Token', '')
        expected_token = current_app.config.get('INTERNAL_RELOAD_TOKEN')
        allowed_services = current_app.config.get('INTERNAL_RELOAD_ALLOWED_SERVICES', frozenset())
        if (
            not expected_token
            or service_id not in allowed_services
            or not hmac.compare_digest(token, expected_token)
        ):
            return jsonify({'error': 'Reload authorization denied'}), 403
        return f(*args, **kwargs)

    return decorated


def debug_routes_enabled(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config['ENABLE_DEBUG_ROUTES']:
            abort(404)
        return f(*args, **kwargs)

    return decorated
