"""Strict topological, duplicate, self-dependency, and collision validators for module graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from servicefabric_application_model.errors import DependencyError, ValidationError
from servicefabric_application_model.modules import ModuleDefinition


@dataclass(frozen=True)
class ValidatedModuleGraph:
    """Represents a validated, topologically sorted graph of application modules."""

    modules_by_id: Mapping[str, ModuleDefinition]
    interface_providers: Mapping[str, str]
    dependency_order: tuple[str, ...]
    shutdown_order: tuple[str, ...]


def validate_module_graph(modules: list[ModuleDefinition]) -> ValidatedModuleGraph:
    """Strictly validates a list of ModuleDefinitions and builds a ValidatedModuleGraph.

    Performs exhaustive checks including duplicate interface providers, duplicate IDs,

    source collisions, self-dependencies, unknown startup targets, and circular references.

    Raises:
        ValidationError: For structural ID, interface, or source-path collisions.
        DependencyError: For circular or unresolved dependency configurations.
    """
    # 1. Check duplicate module IDs
    seen_ids = set()
    modules_by_id: dict[str, ModuleDefinition] = {}
    for mod in modules:
        if mod.module_id in seen_ids:
            raise ValidationError(
                f"Collision: duplicate module ID '{mod.module_id}' found in the graph."
            )
        seen_ids.add(mod.module_id)
        modules_by_id[mod.module_id] = mod

    # 2. Check source directory collisions
    source_dirs: dict[str, str] = {}
    for mod in modules:
        # Standardise path lookup
        norm_source = str(Path(mod.source).as_posix())
        if norm_source in source_dirs:
            raise ValidationError(
                f"Collision: both module '{mod.module_id}' and module '{source_dirs[norm_source]}' "
                f"attempt to use the identical source directory path '{mod.source}'."
            )
        source_dirs[norm_source] = mod.module_id

    # 3. Check duplicate and colliding interface providers
    interface_providers: dict[str, str] = {}
    for mod in modules:
        # Check module-local duplicate provided interfaces
        local_provides = set()
        for prov in mod.provides_interfaces:
            if prov.id in local_provides:
                raise ValidationError(
                    f"Module '{mod.module_id}' declares duplicate provided interface '{prov.id}'."
                )
            local_provides.add(prov.id)
            
            # Check global duplicate interface providers
            if prov.id in interface_providers:
                raise ValidationError(
                    f"Collision: both module '{mod.module_id}' and module '{interface_providers[prov.id]}' "
                    f"attempt to provide the same interface '{prov.id}'."
                )
            interface_providers[prov.id] = mod.module_id

    # 4. Check duplicate required interfaces and resource requests per module
    for mod in modules:
        local_requires = set()
        for req in mod.requires_interfaces:
            if req.id in local_requires:
                raise ValidationError(
                    f"Module '{mod.module_id}' declares duplicate required interface '{req.id}'."
                )
            local_requires.add(req.id)
            
        local_resources = set()
        for res in mod.resources:
            if res.id in local_resources:
                raise ValidationError(
                    f"Module '{mod.module_id}' declares duplicate resource request '{res.id}'."
                )
            local_resources.add(res.id)

    # 5. Check unresolved dependencies & self-dependencies & unknown startAfters
    seen_resources = {res.id for m in modules for res in m.resources}
    for mod in modules:
        # Unresolved interface dependencies
        for req in mod.requires_interfaces:
            if req.id not in interface_providers:
                raise DependencyError(
                    f"Unresolved dependency: module '{mod.module_id}' requires interface "
                    f"'{req.id}', but no module in the graph provides it."
                )
        
        # Self-dependencies
        for dep in mod.lifecycle.start_after:
            if dep == mod.module_id:
                raise DependencyError(
                    f"Circular violation: module '{mod.module_id}' cannot declare a "
                    f"lifecycle dependency on itself."
                )
            if dep not in seen_ids and dep not in seen_resources:
                raise DependencyError(
                    f"Lifecycle violation: module '{mod.module_id}' declares 'startAfter' dependency "
                    f"on unknown module or resource ID '{dep}'."
                )

    # 6. Topological sorting using Kahn's algorithm (Alphabetically deterministic)
    in_degree = {mod.module_id: 0 for mod in modules}
    adj: dict[str, set[str]] = {mod.module_id: set() for mod in modules}

    for mod in modules:
        dep_id = mod.module_id
        # Interface dependency adds dependency edge: provider_id -> dep_id
        for req in mod.requires_interfaces:
            provider_id = interface_providers.get(req.id)
            if provider_id and provider_id != dep_id:
                if dep_id not in adj[provider_id]:
                    adj[provider_id].add(dep_id)
                    in_degree[dep_id] += 1
                    
        # Explicit lifecycle startup dependencies: start_after -> dep_id
        for start_after in mod.lifecycle.start_after:
            if start_after in seen_ids and start_after != dep_id:
                if dep_id not in adj[start_after]:
                    adj[start_after].add(dep_id)
                    in_degree[dep_id] += 1

    # Select all nodes with 0 in-degree (sorted alphabetically for deterministic output)
    queue = [node for node, deg in in_degree.items() if deg == 0]
    queue.sort()

    dependency_order: list[str] = []
    while queue:
        u = queue.pop(0)
        dependency_order.append(u)
        
        # Decrease in-degrees of all neighbors
        for v in sorted(list(adj[u])):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
        
        queue.sort()  # Maintain alphabetical determinism

    # Check for remaining cycle
    if len(dependency_order) < len(modules):
        # Gather nodes involved in cycle
        cycled_nodes = sorted([node for node, deg in in_degree.items() if deg > 0])
        raise DependencyError(
            f"Dependency cycle detected in the application graph involving modules: {cycled_nodes}"
        )

    shutdown_order = tuple(reversed(dependency_order))

    return ValidatedModuleGraph(
        modules_by_id=modules_by_id,
        interface_providers=interface_providers,
        dependency_order=tuple(dependency_order),
        shutdown_order=shutdown_order,
    )


from pathlib import Path
