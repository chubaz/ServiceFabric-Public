import threading
import time
import uuid
from pathlib import Path

from flask import Blueprint, abort, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.middleware import debug_routes_enabled, reload_service_required, token_required
from app.models import ServiceInstance
from app.service_security import ServiceAccessDenied, resolve_tenant_directory, validate_identifier
from app.services_loader import LegacyExecutionDisabled, register_all_services, run_script_for_instance

core_bp = Blueprint('core', __name__)
system_bp = Blueprint('system', __name__)


def _async_surgical_reload(app, target):
    with app.app_context():
        try:
            register_all_services(app, target_shard=target)
            app.logger.info("Approved legacy service reload completed for %s", target)
        except Exception:
            app.logger.exception("Approved legacy service reload failed")


@system_bp.post('/_internal/reload')
@reload_service_required
def internal_reload():
    data = request.get_json(silent=True) or {}
    try:
        target = validate_identifier(data.get('target'))
    except ServiceAccessDenied:
        return jsonify({'error': 'Invalid reload target'}), 400

    if target not in current_app.config['INTERNAL_RELOAD_ALLOWED_TARGETS']:
        return jsonify({'error': 'Reload target is not allowed'}), 403

    app = current_app._get_current_object()
    thread = threading.Thread(target=_async_surgical_reload, args=(app, target), daemon=True)
    thread.start()
    return jsonify({'status': 'accepted', 'type': 'surgical_async'}), 202


@core_bp.route('/status', methods=['GET'])
def public_status():
    return jsonify({'status': 'Flask Core is running', 'version': '1.0.0', 'auth': 'not required'})


@core_bp.route('/debug/me', methods=['GET'])
@debug_routes_enabled
@token_required
def debug_me():
    return jsonify({'message': 'Authentication succeeded', 'authenticated_user_id': g.user_id})


@core_bp.route('/_debug_environ')
@debug_routes_enabled
def debug_environ():
    return jsonify({
        'SCRIPT_NAME': request.environ.get('SCRIPT_NAME'),
        'PATH_INFO': request.environ.get('PATH_INFO'),
        'X-Fwd-Prefix': request.headers.get('X-Forwarded-Prefix'),
    })


@core_bp.route('/execute/<uuid:instance_id>', methods=['POST'])
@token_required
def execute_service(instance_id):
    if current_app.config['IS_PRODUCTION'] or not current_app.config['ENABLE_LEGACY_FAAS_EXECUTION']:
        return jsonify({'status': 'disabled', 'message': 'Legacy service execution is disabled'}), 503

    instance = ServiceInstance.query.filter_by(id=instance_id, owner_id=g.user_id).first()
    if not instance:
        return jsonify({'error': 'Service Instance not found or access denied'}), 404
    if not instance.is_active:
        return jsonify({'error': 'Service is inactive'}), 403

    try:
        result = run_script_for_instance(instance, request.get_json(silent=True) or {})
        return jsonify({'status': 'success', 'result': result})
    except LegacyExecutionDisabled:
        return jsonify({'status': 'disabled', 'message': 'Legacy service execution is disabled'}), 503
    except (ServiceAccessDenied, FileNotFoundError, RuntimeError):
        current_app.logger.warning('Legacy execution failed for instance %s', instance_id)
        return jsonify({'status': 'error', 'message': 'Script execution failed'}), 500
    except Exception:
        current_app.logger.exception('Legacy execution failed for instance %s', instance_id)
        return jsonify({'status': 'error', 'message': 'Script execution failed'}), 500


def _upload_destination(filename: str) -> tuple[Path, str]:
    safe_filename = secure_filename(filename)
    if not safe_filename or '.' not in safe_filename:
        raise ServiceAccessDenied('Invalid upload filename')
    extension = safe_filename.rsplit('.', 1)[1].lower()
    if extension not in current_app.config['UPLOAD_ALLOWED_EXTENSIONS']:
        raise ServiceAccessDenied('Upload type is not allowed')

    tenant_directory = resolve_tenant_directory(Path(current_app.config['USER_MEDIA_ROOT']), g.user_id)
    tenant_directory.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{Path(safe_filename).stem}-{uuid.uuid4().hex}{Path(safe_filename).suffix.lower()}"
    return tenant_directory / stored_filename, stored_filename


@core_bp.route('/utils/upload', methods=['POST'])
@token_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    uploaded_file = request.files['file']
    if not uploaded_file.filename:
        return jsonify({'error': 'No selected file'}), 400

    try:
        destination, stored_filename = _upload_destination(uploaded_file.filename)
        uploaded_file.save(destination)
    except ServiceAccessDenied as exc:
        return jsonify({'error': str(exc)}), 400
    except Exception:
        current_app.logger.exception('Upload failed')
        return jsonify({'error': 'File upload failed'}), 500

    return jsonify({
        'message': 'File uploaded successfully',
        'filename': secure_filename(uploaded_file.filename),
        'file_id': stored_filename,
        'url': f"/media/{g.user_id}/{stored_filename}",
    })


@core_bp.route('/utils/storage/list', methods=['GET'])
@token_required
def list_user_files():
    try:
        user_media_path = resolve_tenant_directory(Path(current_app.config['USER_MEDIA_ROOT']), g.user_id)
    except ServiceAccessDenied:
        return jsonify({'error': 'Storage is unavailable'}), 400
    if not user_media_path.exists():
        return jsonify({'files': []})

    try:
        files = [
            {'name': item.name, 'size_bytes': item.stat().st_size, 'modified': time.ctime(item.stat().st_mtime)}
            for item in user_media_path.iterdir()
            if item.is_file()
        ]
        return jsonify({'files': files})
    except Exception:
        current_app.logger.exception('Storage listing failed')
        return jsonify({'error': 'Storage listing failed'}), 500
