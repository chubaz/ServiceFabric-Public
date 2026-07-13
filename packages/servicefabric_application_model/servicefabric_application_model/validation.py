"""Validates modules, interfaces, bindings, and dependency graphs."""

from __future__ import annotations

from servicefabric_application_model.errors import DependencyError, ValidationError
from servicefabric_application_model.modules import ModuleDefinition


def validate_module_graph(modules: list[ModuleDefinition]) -> None:
    """Performs topological validation of the module graph.

    Verifies absence of duplicate IDs, unresolved dependencies, and dependency cycles.

    Raises:
        ValidationError: If duplicate module IDs exist.
        DependencyError: If there are unresolved required interfaces or circular dependencies.
    """
    # 1. Verify duplicate module IDs
    seen_ids = set()
    for mod in modules:
        if mod.module_id in seen_ids:
            raise ValidationError(f"Duplicate module ID '{mod.module_id}' found in the graph.")
        seen_ids.add(mod.module_id)

    # Map interface ID -> module ID providing it
    providers: dict[str, str] = {}
    for mod in modules:
        for prov in mod.provides_interfaces:
            providers[prov.id] = mod.module_id

    # 2. Check for unresolved interface requirements
    for mod in modules:
        for req in mod.requires_interfaces:
            if req.id not in providers:
                raise DependencyError(
                    f"Unresolved dependency: module '{mod.module_id}' requires interface "
                    f"'{req.id}', but no module in the workspace provides it."
                )

    # 3. Detect dependency cycles using Depth First Search (DFS)
    # Build adjacency list: node -> set of modules it depends on
    adj: dict[str, set[str]] = {mod.module_id: set() for mod in modules}
    for mod in modules:
        # Interface dependency
        for req in mod.requires_interfaces:
            provider_mod = providers.get(req.id)
            if provider_mod:
                adj[mod.module_id].add(provider_mod)
        # Explicit lifecycle startup dependencies (start_after)
        for dep in mod.lifecycle.start_after:
            if dep in seen_ids:
                adj[mod.module_id].add(dep)

    # Visited state tracker: 0 = unvisited, 1 = visiting, 2 = visited
    visited: dict[str, int] = {node: 0 for node in adj}

    def dfs(node: str) -> None:
        visited[node] = 1  # Mark as visiting
        for neighbor in adj[node]:
            if visited[neighbor] == 1:
                raise DependencyError(
                    f"Dependency cycle detected: circular relationship found involving "
                    f"module '{node}' and module '{neighbor}'."
                )
            elif visited[neighbor] == 0:
                dfs(neighbor)
        visited[node] = 2  # Mark as fully visited

    for node in adj:
        if visited[node] == 0:
            dfs(node)
