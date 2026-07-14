"""Strictly parses and loads ApplicationModule manifests from files or dictionaries."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from servicefabric_application_model.errors import InvalidModuleDefinition
from servicefabric_application_model.interfaces import ProvidedInterface, RequiredInterface
from servicefabric_application_model.lifecycle import LifecycleConfig, ReadinessProbe, ShutdownConfig
from servicefabric_application_model.modules import ModuleDefinition, ResourceExpectations
from servicefabric_application_model.primitives import validate_primitive
from servicefabric_application_model.resources import ResourceRequest

# Pre-compiled strict validation regular expressions
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-\w+)?$")


def validate_id(val: Any, field_name: str) -> str:
    if not isinstance(val, str):
        raise InvalidModuleDefinition(f"{field_name} must be a string, got '{type(val).__name__}'.")
    if not ID_PATTERN.match(val):
        raise InvalidModuleDefinition(
            f"{field_name} '{val}' is invalid. Must consist only of lowercase letters, "
            f"numbers, and single hyphens, start with a letter, and end with a letter or number."
        )
    length = len(val)
    if length < 3 or length > 63:
        raise InvalidModuleDefinition(
            f"{field_name} '{val}' length must be between 3 and 63 characters (got {length})."
        )
    return val


def validate_version(val: Any, field_name: str) -> str:
    if not isinstance(val, str):
        raise InvalidModuleDefinition(f"{field_name} must be a string, got '{type(val).__name__}'.")
    if not VERSION_PATTERN.match(val):
        raise InvalidModuleDefinition(
            f"{field_name} '{val}' is invalid. Must match semantic-versioning format (e.g. 1.0.0)."
        )
    return val


def validate_kit_reference(val: Any, field_name: str) -> str:
    if not isinstance(val, str):
        raise InvalidModuleDefinition(f"{field_name} must be a string, got '{type(val).__name__}'.")
    if " @ServiceFabric/" not in val:
        raise InvalidModuleDefinition(
            f"{field_name} '{val}' must be a valid reference formatted as 'kit_id @ServiceFabric/path'."
        )
    parts = val.split(" @ServiceFabric/", 1)
    kit_id = parts[0].strip()
    validate_id(kit_id, f"{field_name} kit ID")
    return val


def validate_source_path(val: Any, field_name: str) -> str:
    if not isinstance(val, str):
        raise InvalidModuleDefinition(f"{field_name} must be a string, got '{type(val).__name__}'.")
    if not val:
        raise InvalidModuleDefinition(f"{field_name} cannot be empty.")
    path = Path(val)
    if path.is_absolute():
        raise InvalidModuleDefinition(f"{field_name} '{val}' cannot be an absolute path.")
    
    # Path safety traversal check using resolved dummy parent
    dummy_root = Path("/tmp/dummy-root").resolve()
    try:
        resolved = (dummy_root / path).resolve()
        if not resolved.is_relative_to(dummy_root):
            raise InvalidModuleDefinition(
                f"{field_name} '{val}' violates path safety: escapes parent directory boundary."
            )
    except Exception as exc:
        raise InvalidModuleDefinition(f"{field_name} '{val}' is invalid: {exc}") from exc
    return val


def _assert_keys_supported(keys: set[str], supported: set[str], context_name: str) -> None:
    unsupported = keys - supported
    if unsupported:
        raise InvalidModuleDefinition(
            f"Unsupported field(s) {sorted(list(unsupported))} found in '{context_name}'. "
            f"Allowed fields: {sorted(list(supported))}"
        )


def load_module_definition_from_dict(data: dict[str, Any]) -> ModuleDefinition:
    """Strictly parses a dictionary representing an ApplicationModule manifest.

    Raises:
        InvalidModuleDefinition: If fields are unsupported, missing, malformed, or invalid.
    """
    if not isinstance(data, dict):
        raise InvalidModuleDefinition("Module manifest is not a valid dictionary structure.")

    # Validate outer keys
    _assert_keys_supported(
        set(data.keys()),
        {"apiVersion", "kind", "metadata", "spec"},
        "root",
    )

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
    
    _assert_keys_supported(set(metadata.keys()), {"id", "version"}, "metadata")

    module_id = validate_id(metadata.get("id"), "metadata.id")
    version = validate_version(metadata.get("version", "0.1.0"), "metadata.version")

    # 3. Spec parsing
    spec = data.get("spec", {})
    if not isinstance(spec, dict):
        raise InvalidModuleDefinition("Section 'spec' must be a valid dictionary.")

    _assert_keys_supported(
        set(spec.keys()),
        {"primitive", "kit", "source", "provides", "requires", "lifecycle", "resourceExpectations"},
        "spec",
    )

    primitive = spec.get("primitive")
    if not primitive:
        raise InvalidModuleDefinition("Required field 'spec.primitive' is missing.")
    
    primitive_kind = validate_primitive(primitive)

    kit = validate_kit_reference(spec.get("kit"), "spec.kit")
    source = validate_source_path(spec.get("source"), "spec.source")

    # 4. Provided interfaces parsing (strictly structured)
    provides_data = spec.get("provides")
    provides_interfaces: list[ProvidedInterface] = []
    
    if provides_data is not None:
        if not isinstance(provides_data, list):
            raise InvalidModuleDefinition("Section 'spec.provides' must be a list of interface objects.")
            
        for idx, item in enumerate(provides_data):
            if not isinstance(item, dict):
                raise InvalidModuleDefinition(
                    f"Provides interface at index {idx} must be an object."
                )
            _assert_keys_supported(
                set(item.keys()),
                {"id", "type", "protocol", "contract"},
                f"provides[{idx}]",
            )
            
            prov_id = validate_id(item.get("id"), f"provides[{idx}].id")
            prov_type = item.get("type")
            if not prov_type:
                raise InvalidModuleDefinition(f"Required field 'type' is missing in provides[{idx}].")
            if not isinstance(prov_type, str):
                raise InvalidModuleDefinition(f"Provides type in provides[{idx}] must be a string.")
            
            prov_proto = item.get("protocol")
            if prov_proto is not None and not isinstance(prov_proto, str):
                raise InvalidModuleDefinition(f"Protocol in provides[{idx}] must be a string.")
                
            prov_contract = item.get("contract")
            if prov_contract is not None and not isinstance(prov_contract, str):
                raise InvalidModuleDefinition(f"Contract in provides[{idx}] must be a string.")
                
            provides_interfaces.append(
                ProvidedInterface(
                    id=prov_id, type=prov_type, protocol=prov_proto, contract=prov_contract
                )
            )

    # 5. Required interfaces & Resource requests parsing
    requires_data = spec.get("requires") or {}
    requires_interfaces_list: list[RequiredInterface] = []
    resources_list: list[ResourceRequest] = []
    
    if "requires" in spec:
        if not isinstance(requires_data, dict):
            raise InvalidModuleDefinition("Section 'spec.requires' must be a dictionary.")
            
        _assert_keys_supported(
            set(requires_data.keys()),
            {"interfaces", "resources"},
            "spec.requires",
        )

        req_interfaces = requires_data.get("interfaces")
        if req_interfaces is not None:
            if not isinstance(req_interfaces, list):
                raise InvalidModuleDefinition("Section 'spec.requires.interfaces' must be a list.")
            for idx, item in enumerate(req_interfaces):
                if not isinstance(item, dict):
                    raise InvalidModuleDefinition(f"Interface requirement at index {idx} must be an object.")
                _assert_keys_supported(set(item.keys()), {"id"}, f"requires.interfaces[{idx}]")
                req_id = validate_id(item.get("id"), f"requires.interfaces[{idx}].id")
                requires_interfaces_list.append(RequiredInterface(id=req_id))
        
        req_resources = requires_data.get("resources")
        if req_resources is not None:
            if not isinstance(req_resources, list):
                raise InvalidModuleDefinition("Section 'spec.requires.resources' must be a list.")
            for idx, item in enumerate(req_resources):
                if not isinstance(item, dict):
                    raise InvalidModuleDefinition(f"Resource requirement at index {idx} must be an object.")
                _assert_keys_supported(
                    set(item.keys()),
                    {"id", "type", "scope"},
                    f"requires.resources[{idx}]",
                )
                res_id = validate_id(item.get("id"), f"requires.resources[{idx}].id")
                
                res_type = item.get("type")
                if not res_type:
                    raise InvalidModuleDefinition(f"Required field 'type' is missing in requires.resources[{idx}].")
                if not isinstance(res_type, str):
                    raise InvalidModuleDefinition(f"Resource type in requires.resources[{idx}] must be a string.")
                
                res_scope = item.get("scope", "application")
                if not isinstance(res_scope, str):
                    raise InvalidModuleDefinition(f"Resource scope in requires.resources[{idx}] must be a string.")
                    
                resources_list.append(
                    ResourceRequest(id=res_id, type=res_type, scope=res_scope)
                )

    # 6. Lifecycle configuration parsing
    lifecycle_config = LifecycleConfig()
    if "lifecycle" in spec:
        lifecycle_data = spec.get("lifecycle")
        if not isinstance(lifecycle_data, dict):
            raise InvalidModuleDefinition("Section 'spec.lifecycle' must be a dictionary.")
            
        _assert_keys_supported(
            set(lifecycle_data.keys()),
            {"startAfter", "start_after", "readiness", "shutdown"},
            "spec.lifecycle",
        )
        
        start_after_key = "startAfter" if "startAfter" in lifecycle_data else "start_after"
        start_after_val = lifecycle_data.get(start_after_key, [])
        if not isinstance(start_after_val, list):
            raise InvalidModuleDefinition(f"Lifecycle '{start_after_key}' must be a list of IDs.")
        start_after = [validate_id(x, f"lifecycle.{start_after_key} ID") for x in start_after_val]
        
        readiness = None
        readiness_val = lifecycle_data.get("readiness")
        if readiness_val is not None:
            if not isinstance(readiness_val, dict):
                raise InvalidModuleDefinition("Lifecycle 'readiness' must be a dictionary.")
            _assert_keys_supported(
                set(readiness_val.keys()),
                {"type", "path", "port"},
                "lifecycle.readiness",
            )
            r_type = readiness_val.get("type")
            if not r_type:
                raise InvalidModuleDefinition("Required field 'type' is missing in lifecycle.readiness.")
            if r_type not in {"http", "tcp", "command", "process"}:
                raise InvalidModuleDefinition(f"Unsupported readiness probe type '{r_type}'.")
                
            r_path = readiness_val.get("path")
            if r_path is not None and not isinstance(r_path, str):
                raise InvalidModuleDefinition("Readiness probe 'path' must be a string.")
                
            r_port = readiness_val.get("port")
            if r_port is not None:
                if not isinstance(r_port, int) or r_port < 1 or r_port > 65535:
                    raise InvalidModuleDefinition(f"Readiness probe 'port' '{r_port}' must be a valid port number.")
            readiness = ReadinessProbe(type=r_type, path=r_path, port=r_port)
            
        shutdown = ShutdownConfig()
        shutdown_val = lifecycle_data.get("shutdown")
        if shutdown_val is not None:
            if not isinstance(shutdown_val, dict):
                raise InvalidModuleDefinition("Lifecycle 'shutdown' must be a dictionary.")
            _assert_keys_supported(
                set(shutdown_val.keys()),
                {"timeoutSeconds", "timeout_seconds"},
                "lifecycle.shutdown",
            )
            timeout_key = "timeoutSeconds" if "timeoutSeconds" in shutdown_val else "timeout_seconds"
            s_timeout = shutdown_val.get(timeout_key, 10)
            if not isinstance(s_timeout, int) or s_timeout <= 0:
                raise InvalidModuleDefinition("Shutdown timeout must be a positive integer.")
            shutdown = ShutdownConfig(timeout_seconds=s_timeout)

        lifecycle_config = LifecycleConfig(
            start_after=tuple(start_after),
            readiness=readiness,
            shutdown=shutdown,
        )

    # 7. ResourceExpectations parsing
    resource_expectations = None
    if "resourceExpectations" in spec:
        exp_data = spec.get("resourceExpectations")
        if not isinstance(exp_data, dict):
            raise InvalidModuleDefinition("Section 'spec.resourceExpectations' must be a dictionary.")
        _assert_keys_supported(
            set(exp_data.keys()),
            {"memoryMiB", "cpuCores"},
            "spec.resourceExpectations",
        )
        mem_mib = exp_data.get("memoryMiB")
        if mem_mib is not None:
            if not isinstance(mem_mib, int) or mem_mib <= 0:
                raise InvalidModuleDefinition("resourceExpectations.memoryMiB must be a positive integer.")
                
        cpu_cores = exp_data.get("cpuCores")
        if cpu_cores is not None:
            if not isinstance(cpu_cores, (int, float)) or cpu_cores <= 0.0:
                raise InvalidModuleDefinition("resourceExpectations.cpuCores must be a positive number.")
                
        resource_expectations = ResourceExpectations(
            memory_mib=mem_mib,
            cpu_cores=float(cpu_cores) if cpu_cores is not None else None,
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
        resource_expectations=resource_expectations,
        raw_data=data,
    )


def load_module_definition_from_file(path: Path) -> ModuleDefinition:
    """Reads and strictly parses an ApplicationModule manifest file.

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
        if isinstance(exc, InvalidModuleDefinition):
            raise
        raise InvalidModuleDefinition(
            f"Failed to read/parse module manifest at '{path}': {exc}"
        ) from exc
