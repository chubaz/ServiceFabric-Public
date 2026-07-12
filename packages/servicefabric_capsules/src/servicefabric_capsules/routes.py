"""Deterministic capsule route and binding resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from servicefabric_contracts import CapsuleArtifactBinding, CapsuleRevision, CapsuleRoute
from servicefabric_contracts.capsules import _normalize_route_path


@dataclass(frozen=True)
class CapsuleRouteTable:
    routes: tuple[CapsuleRoute, ...]
    bindings: tuple[CapsuleArtifactBinding, ...]
    entry_route: str

    @classmethod
    def from_revision(cls, revision: CapsuleRevision) -> "CapsuleRouteTable":
        routes = tuple(revision.spec.routes)
        bindings = tuple(revision.spec.artifact_bindings)
        if not routes:
            raise ValueError("capsule revision must declare routes")
        if not bindings:
            raise ValueError("capsule revision must declare artifact bindings")
        route_paths = {route.path for route in routes}
        if len(route_paths) != len(routes):
            raise ValueError("route paths must be unique")
        binding_ids = {binding.binding_id for binding in bindings}
        if len(binding_ids) != len(bindings):
            raise ValueError("artifact binding IDs must be unique")
        if revision.spec.entry_route not in route_paths:
            raise ValueError("entry route must be declared")
        mount_paths = [binding.mount_path for binding in bindings]
        for left_index, left in enumerate(mount_paths):
            for right in mount_paths[left_index + 1 :]:
                if left == right or left.startswith(right.rstrip("/") + "/") or right.startswith(left.rstrip("/") + "/"):
                    raise ValueError("artifact binding mount paths must not overlap")
        return cls(
            routes=tuple(sorted(routes, key=lambda item: item.path)),
            bindings=tuple(sorted(bindings, key=lambda item: item.binding_id)),
            entry_route=revision.spec.entry_route,
        )

    def resolve(self, path: str) -> CapsuleRoute:
        normalized = _normalize_route_path(path)
        if normalized != path:
            raise ValueError("route path traversal is forbidden")
        for route in self.routes:
            if route.path == normalized:
                return route
        raise KeyError(normalized)

    def binding(self, binding_id: str) -> CapsuleArtifactBinding:
        for binding in self.bindings:
            if binding.binding_id == binding_id:
                return binding
        raise KeyError(binding_id)

    def declared_paths(self) -> tuple[str, ...]:
        return tuple(route.path for route in self.routes)
