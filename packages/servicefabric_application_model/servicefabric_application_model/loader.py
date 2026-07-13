"""Parses and loads ApplicationModule manifests from files or dictionaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from servicefabric_application_model.errors import InvalidModuleDefinition
from servicefabric_application_model.interfaces import ProvidedInterface, RequiredInterface
from servicefabric_application_model.lifecycle import LifecycleConfig, ReadinessProbe, ShutdownConfig
from servicefabric_application_model.modules import ModuleDefinition
from servicefabric_application_model.primitives import validate_primitive
from servicefabric_application_model.resources import ResourceRequest


def load_module_definition_from_dict(data: dict[str, Any]) -> ModuleDefinition:
    """Parses a dictionary representing an ApplicationModule manifest.

    Args:
        data: Parsed dictionary from a YAML manifest.

    Returns:
        A validated ModuleDefinition model.

    Raises:
        InvalidModuleDefinition: If fields are missing, malformed, or fail headers checks.
    """
    if not isinstance(data, dict):
        raise InvalidModuleDefinition("Module manifest is not a valid dictionary structure.")

    # 1. API version and kind checks
    api_version = data.get("apiVersion")
    kind = data.get("kind")
    if api_version != "servicefabric.local/v1":
        raise InvalidModuleDefinition(
            f"Unsupported apiVersion '{api_version}'. Expected 'servicefabric.local/v1'."
        )
    if kind != "ApplicationModule":
        raise InvalidModuleDefinition(
            f"Unsupported kind '{kind}'. Expected 'ApplicationModule'."
        )

    # 2. Metadata parsing
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise InvalidModuleDefinition("Section 'metadata' must be a valid dictionary.")
    
    module_id = metadata.get("id")
    if not module_id:
        raise InvalidModuleDefinition("Required field 'metadata.id' is missing.")
    
    version = metadata.get("version", "0.1.0")

    # 3. Spec parsing
    spec = data.get("spec", {})
    if not isinstance(spec, dict):
        raise InvalidModuleDefinition("Section 'spec' must be a valid dictionary.")

    primitive = spec.get("primitive")
    if not primitive:
        raise InvalidModuleDefinition("Required field 'spec.primitive' is missing.")
    
    primitive_kind = validate_primitive(primitive)

    kit = spec.get("kit")
    if not kit:
        raise InvalidModuleDefinition("Required field 'spec.kit' is missing.")
    
    source = spec.get("source", "")

    # 4. Provided interfaces parsing (flexible list or dict formats)
    provides_data = spec.get("provides")
    provides_list: list[Any] = []
    if isinstance(provides_data, list):
        provides_list = provides_data
    elif isinstance(provides_data, dict):
        provides_list = (
            provides_data.get("interfaces")
            or provides_data.get("provided_interfaces")
            or []
        )
        if not isinstance(provides_list, list):
            provides_list = []

    provides_interfaces: list[ProvidedInterface] = []
    for item in provides_list:
        if isinstance(item, dict):
            prov_id = item.get("id") or item.get("interface_id")
            if not prov_id:
                continue
            prov_type = item.get("type", "http")
            prov_proto = item.get("protocol")
            prov_contract = item.get("contract")
            provides_interfaces.append(
                ProvidedInterface(
                    id=prov_id, type=prov_type, protocol=prov_proto, contract=prov_contract
                )
            )

    # 5. Required interfaces & Resource requests parsing
    requires_data = spec.get("requires") or {}
    requires_interfaces_list: list[RequiredInterface] = []
    resources_list: list[ResourceRequest] = []
    
    if isinstance(requires_data, dict):
        req_interfaces = requires_data.get("interfaces") or []
        if isinstance(req_interfaces, list):
            for item in req_interfaces:
                if isinstance(item, dict):
                    req_id = item.get("id")
                    if req_id:
                        requires_interfaces_list.append(RequiredInterface(id=req_id))
                elif isinstance(item, str):
                    requires_interfaces_list.append(RequiredInterface(id=item))
        
        req_resources = requires_data.get("resources") or []
        if isinstance(req_resources, list):
            for item in req_resources:
                if isinstance(item, dict):
                    res_id = item.get("id")
                    if not res_id:
                        continue
                    res_type = item.get("type", "relational-database")
                    res_scope = item.get("scope", "application")
                    resources_list.append(
                        ResourceRequest(id=res_id, type=res_type, scope=res_scope)
                    )
                elif isinstance(item, str):
                    resources_list.append(
                        ResourceRequest(id=item, type="relational-database")
                    )

    # 6. Lifecycle configuration parsing
    lifecycle_data = spec.get("lifecycle") or {}
    start_after: list[str] = []
    readiness: ReadinessProbe | None = None
    shutdown = ShutdownConfig()

    if isinstance(lifecycle_data, dict):
        start_after_val = (
            lifecycle_data.get("startAfter") or lifecycle_data.get("start_after") or []
        )
        if isinstance(start_after_val, list):
            start_after = [str(x) for x in start_after_val]
        
        readiness_val = lifecycle_data.get("readiness")
        if isinstance(readiness_val, dict):
            r_type = readiness_val.get("type", "http")
            r_path = readiness_val.get("path")
            r_port = readiness_val.get("port")
            readiness = ReadinessProbe(type=r_type, path=r_path, port=r_port)
        
        shutdown_val = lifecycle_data.get("shutdown")
        if isinstance(shutdown_val, dict):
            s_timeout = (
                shutdown_val.get("timeoutSeconds")
                or shutdown_val.get("timeout_seconds")
                or 10
            )
            shutdown = ShutdownConfig(timeout_seconds=int(s_timeout))
        elif "shutdownTimeoutSeconds" in lifecycle_data:
            shutdown = ShutdownConfig(
                timeout_seconds=int(lifecycle_data["shutdownTimeoutSeconds"])
            )

    lifecycle_config = LifecycleConfig(
        start_after=tuple(start_after),
        readiness=readiness,
        shutdown=shutdown,
    )

    return ModuleDefinition(
        module_id=module_id,
        version=version,
        primitive=primitive_kind,
        kit=kit,
        source=source,
        provides_interfaces=tuple(provides_interfaces),
        requires_interfaces=tuple(requires_interfaces_list),
        resources=tuple(resources_list),
        lifecycle=lifecycle_config,
        raw_data=data,
    )


def load_module_definition_from_file(path: Path) -> ModuleDefinition:
    """Reads and parses an ApplicationModule manifest file.

    Raises:
        InvalidModuleDefinition: If the file does not exist or has invalid content.
    """
    import yaml
    
    if not path.is_file():
        raise InvalidModuleDefinition(f"Module manifest file not found: '{path}'")
    
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
            return load_module_definition_from_dict(data)
    except Exception as exc:
        raise InvalidModuleDefinition(
            f"Failed to read/parse module manifest at '{path}': {exc}"
        ) from exc
