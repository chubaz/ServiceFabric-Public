"""Build deterministic assembly graphs from canonical application modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from servicefabric_application_model import (
    ModuleDefinition,
    ResourceRequest,
    ValidationError,
    load_module_definition_from_file,
    validate_module_graph,
)


@dataclass(frozen=True)
class AssemblyEdge:
    """Directed dependency edge in an assembled application graph."""

    source: str
    target: str
    kind: str
    via: str


@dataclass(frozen=True)
class ApplicationResource:
    """Resource binding requested by one or more modules."""

    id: str
    type: str
    scope: str
    requested_by: tuple[str, ...]


@dataclass(frozen=True)
class ModuleAssemblyNode:
    """Assembly metadata for one module."""

    module_id: str
    module: ModuleDefinition
    provides_interfaces: tuple[str, ...]
    requires_interfaces: tuple[str, ...]
    requires_resources: tuple[str, ...]
    depends_on_modules: tuple[str, ...]
    depends_on_resources: tuple[str, ...]


@dataclass(frozen=True)
class ApplicationAssembly:
    """Resolved application assembly without process or kit side effects."""

    modules_by_id: Mapping[str, ModuleAssemblyNode]
    interface_providers: Mapping[str, str]
    resources_by_id: Mapping[str, ApplicationResource]
    edges: tuple[AssemblyEdge, ...]
    build_order: tuple[str, ...]
    startup_order: tuple[str, ...]
    shutdown_order: tuple[str, ...]


def assemble_application(modules: Iterable[ModuleDefinition]) -> ApplicationAssembly:
    """Validate modules and assemble their interface, resource, and lifecycle graph."""

    module_list = tuple(modules)
    validated = validate_module_graph(list(module_list))
    resources_by_id = _collect_resources(module_list)
    module_ids = set(validated.modules_by_id)

    collisions = sorted(set(resources_by_id).intersection(module_ids))
    if collisions:
        raise ValidationError(
            "Resource ID(s) collide with module ID(s), making lifecycle dependencies ambiguous: "
            f"{collisions}"
        )

    nodes: dict[str, ModuleAssemblyNode] = {}
    edges: list[AssemblyEdge] = []

    for module_id in validated.dependency_order:
        module = validated.modules_by_id[module_id]
        module_deps: set[str] = set()
        resource_deps: set[str] = set()

        for requirement in module.requires_interfaces:
            provider_id = validated.interface_providers[requirement.id]
            module_deps.add(provider_id)
            edges.append(
                AssemblyEdge(
                    source=provider_id,
                    target=module_id,
                    kind="interface",
                    via=requirement.id,
                )
            )

        for resource in module.resources:
            resource_deps.add(resource.id)
            edges.append(
                AssemblyEdge(
                    source=resource.id,
                    target=module_id,
                    kind="resource",
                    via=resource.id,
                )
            )

        for dependency_id in module.lifecycle.start_after:
            if dependency_id in module_ids:
                module_deps.add(dependency_id)
            elif dependency_id in resources_by_id:
                resource_deps.add(dependency_id)
            edges.append(
                AssemblyEdge(
                    source=dependency_id,
                    target=module_id,
                    kind="lifecycle",
                    via=dependency_id,
                )
            )

        nodes[module_id] = ModuleAssemblyNode(
            module_id=module_id,
            module=module,
            provides_interfaces=tuple(interface.id for interface in module.provides_interfaces),
            requires_interfaces=tuple(interface.id for interface in module.requires_interfaces),
            requires_resources=tuple(resource.id for resource in module.resources),
            depends_on_modules=tuple(sorted(module_deps)),
            depends_on_resources=tuple(sorted(resource_deps)),
        )

    return ApplicationAssembly(
        modules_by_id=nodes,
        interface_providers=dict(validated.interface_providers),
        resources_by_id=resources_by_id,
        edges=tuple(sorted(edges, key=lambda edge: (edge.target, edge.kind, edge.source, edge.via))),
        build_order=validated.dependency_order,
        startup_order=validated.dependency_order,
        shutdown_order=validated.shutdown_order,
    )


def load_application_assembly_from_files(paths: Iterable[Path]) -> ApplicationAssembly:
    """Load module manifests from files and assemble them."""

    return assemble_application(load_module_definition_from_file(Path(path)) for path in paths)


def _collect_resources(modules: Iterable[ModuleDefinition]) -> dict[str, ApplicationResource]:
    resources: dict[str, ResourceRequest] = {}
    requested_by: dict[str, list[str]] = {}

    for module in modules:
        for resource in module.resources:
            existing = resources.get(resource.id)
            if existing is not None and (
                existing.type != resource.type or existing.scope != resource.scope
            ):
                raise ValidationError(
                    f"Resource '{resource.id}' is requested with conflicting definitions."
                )
            resources[resource.id] = resource
            requested_by.setdefault(resource.id, []).append(module.module_id)

    return {
        resource_id: ApplicationResource(
            id=resource.id,
            type=resource.type,
            scope=resource.scope,
            requested_by=tuple(sorted(requested_by[resource_id])),
        )
        for resource_id, resource in sorted(resources.items())
    }
