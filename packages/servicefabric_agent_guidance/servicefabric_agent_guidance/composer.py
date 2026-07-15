"""Pure, deterministic composition of application and module guidance."""

from __future__ import annotations

import re
from collections.abc import Mapping

from servicefabric_agent_guidance.builtins import KIT_GUIDANCE, MODULE_GUIDANCE, ROOT_GUIDANCE
from servicefabric_agent_guidance.errors import DuplicateGuidancePath, UnknownGuidanceKit
from servicefabric_agent_guidance.models import GuidanceBundle, GuidanceFragment


_MODULE_ID = re.compile(r"^[a-z][a-z0-9-]*$")


def kit_id(reference: str) -> str:
    """Extracts a kit ID from a reviewed framework-kit reference."""
    value = reference.split("@", 1)[0].strip()
    if not value:
        raise UnknownGuidanceKit("Guidance requires a non-empty framework kit reference.")
    return value


class GuidanceComposer:
    """Composes reviewed fragments without filesystem or runtime dependencies."""

    def __init__(self, root_fragment: GuidanceFragment = ROOT_GUIDANCE) -> None:
        self._root_fragment = root_fragment

    def compose(self, module_kits: Mapping[str, str]) -> GuidanceBundle:
        """Creates root and per-module `AGENTS.md` files in lexical module order.

        Every requested kit must have a reviewed guidance fragment. This makes a
        missing fragment explicit instead of silently producing incomplete output.
        """
        files = {self._root_fragment.path: self._root_fragment.rendered_content()}
        for module_id, reference in sorted(module_kits.items()):
            if not _MODULE_ID.fullmatch(module_id):
                raise ValueError(f"Invalid module ID for guidance: {module_id!r}.")
            selected_kit = kit_id(reference)
            try:
                kit_content = KIT_GUIDANCE[selected_kit]
            except KeyError as exc:
                raise UnknownGuidanceKit(
                    f"No reviewed guidance fragment exists for kit {selected_kit!r}."
                ) from exc
            path = f"modules/{module_id}/AGENTS.md"
            if path in files:
                raise DuplicateGuidancePath(f"Multiple fragments target {path!r}.")
            files[path] = MODULE_GUIDANCE.format(module_id=module_id) + "\n" + kit_content
        return GuidanceBundle(files)


def compose_guidance(module_kits: Mapping[str, str]) -> GuidanceBundle:
    """Convenience entry point for standard reviewed guidance composition."""
    return GuidanceComposer().compose(module_kits)
