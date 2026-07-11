import importlib.machinery
import importlib.util
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from flask import current_app, g

from app.service_manager import ServiceAssetsManager
from app.service_security import ServiceAccessDenied, resolve_service_directory, validate_identifier

import_lock = threading.RLock()


class LegacyExecutionDisabled(RuntimeError):
    pass


def _catalogue_allowed(app, service_name: str) -> bool:
    if not app.config['ENABLE_DYNAMIC_SERVICE_IMPORTS']:
        return False
    if app.config['IS_PRODUCTION']:
        return service_name in app.config['LEGACY_CATALOG_ALLOWLIST']
    return True


def _generated_allowed(app) -> bool:
    return bool(app.config['ENABLE_GENERATED_SERVICE_IMPORTS']) and not app.config['IS_PRODUCTION']


def _ensure_parent_package(parent_package: str, root: Path) -> None:
    if parent_package in sys.modules:
        return
    spec = importlib.machinery.ModuleSpec(parent_package, None, is_package=True)
    module = importlib.util.module_from_spec(spec)
    module.__path__ = [str(root.resolve())]
    sys.modules[parent_package] = module


def _safe_module_name(parent_package: str, service_name: str) -> str:
    return f"{parent_package}.{service_name.replace('-', '_')}"


def register_all_services(app, target_shard=None):
    """Mount only explicitly enabled legacy catalogue packages."""
    if target_shard is not None:
        target_shard = validate_identifier(target_shard)

    catalog_path = Path(app.config['SERVICE_CATALOG_PATH'])
    generated_path = Path(app.config['SERVICE_GENERATED_PATH'])

    if app.config['ENABLE_DYNAMIC_SERVICE_IMPORTS']:
        _mount_from_directory(app, catalog_path, 'dynamic_catalog', '', target_shard, generated=False)
    if _generated_allowed(app):
        _mount_from_directory(app, generated_path, 'dynamic_sandbox', '/sandbox', target_shard, generated=True)


def load_active_services(app):
    register_all_services(app)


def _mount_from_directory(app, directory, parent_package, prefix_base, target_shard=None, generated=False):
    if not directory.exists() or not directory.is_dir():
        return
    _ensure_parent_package(parent_package, directory)

    for item in directory.iterdir():
        if not item.is_dir() or item.name.startswith(('.', '_')):
            continue
        try:
            service_name = validate_identifier(item.name)
            if target_shard and service_name != target_shard:
                continue
            if generated and not _generated_allowed(app):
                continue
            if not generated and not _catalogue_allowed(app, service_name):
                continue
            service_dir = resolve_service_directory(directory, service_name)
            init_file = service_dir / '__init__.py'
            if not init_file.is_file():
                continue
            _mount_service(app, service_dir, service_name, parent_package, prefix_base)
        except ServiceAccessDenied:
            app.logger.warning('Skipped an invalid legacy service identifier')
        except Exception:
            app.logger.exception('Failed to mount legacy service %s', item.name)


def _mount_service(app, service_dir, service_name, parent_package, prefix_base):
    module_name = _safe_module_name(parent_package, service_name)
    with import_lock:
        if module_name in sys.modules:
            return
        spec = importlib.util.spec_from_file_location(
            module_name,
            service_dir / '__init__.py',
            submodule_search_locations=[str(service_dir)],
        )
        if not spec or not spec.loader:
            raise RuntimeError('Legacy service could not be loaded')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(module_name, None)
            raise

    blueprint = getattr(module, 'bp', getattr(module, 'service_bp', None))
    if not blueprint or blueprint.name in app.blueprints:
        return
    ServiceAssetsManager.configure_blueprint(app, blueprint, service_name)
    app.register_blueprint(blueprint, url_prefix=f'{prefix_base}/{service_name}'.replace('//', '/'))
    app.logger.info("Mounted approved legacy service '%s'", service_name)


@contextmanager
def _temporary_service_path(path: Path):
    path_string = str(path)
    sys.path.insert(0, path_string)
    try:
        yield
    finally:
        if path_string in sys.path:
            sys.path.remove(path_string)


def run_script_for_instance(instance, input_data):
    """Execute the temporary legacy FaaS path only when explicitly enabled outside production."""
    if current_app.config['IS_PRODUCTION'] or not current_app.config['ENABLE_LEGACY_FAAS_EXECUTION']:
        raise LegacyExecutionDisabled('Legacy service execution is disabled')

    service_name = validate_identifier(instance.service_type)
    roots = [Path(current_app.config['SERVICE_CATALOG_PATH'])]
    if _generated_allowed(current_app):
        roots.append(Path(current_app.config['SERVICE_GENERATED_PATH']))

    script_path = None
    target_dir = None
    for root in roots:
        candidate_dir = resolve_service_directory(root, service_name)
        candidate_script = candidate_dir / 'service.py'
        if candidate_script.is_file():
            script_path = candidate_script
            target_dir = candidate_dir
            break
    if not script_path or not target_dir:
        raise FileNotFoundError('Legacy service script is unavailable')

    module_name = f"dynamic_script.{service_name.replace('-', '_')}_{instance.id}"
    with import_lock:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if not spec or not spec.loader:
            raise RuntimeError('Legacy service script could not be loaded')
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
    try:
        with _temporary_service_path(target_dir):
            spec.loader.exec_module(module)
            runner_class = getattr(module, 'ServiceRunner', None)
            if runner_class is None:
                raise RuntimeError('Legacy service script is invalid')
            context = {
                'user_id': g.user_id,
                'instance_id': str(instance.id),
                'config': instance.state_config,
                'logger': current_app.logger,
            }
            return runner_class(context).run(input_data)
    finally:
        sys.modules.pop(module_name, None)
