"""Immutable inputs and outputs for deterministic guidance composition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Mapping

from servicefabric_agent_guidance.errors import InvalidGuidancePath


def _relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or str(path) == ".":
        raise InvalidGuidancePath(
            f"Guidance path must be a non-empty relative path: {value!r}."
        )
    return path.as_posix()


@dataclass(frozen=True)
class GuidanceFragment:
    """Reviewed text to be rendered into one relative workspace path."""

    fragment_id: str
    path: str
    content: str

    def __post_init__(self) -> None:
        if not self.fragment_id:
            raise ValueError("Guidance fragment IDs must not be empty.")
        object.__setattr__(self, "path", _relative_path(self.path))
        if not self.content:
            raise ValueError("Guidance fragment content must not be empty.")

    def rendered_content(self) -> str:
        """Returns canonical UTF-8 text with exactly one trailing newline."""
        return self.content.rstrip("\n") + "\n"


@dataclass(frozen=True)
class GuidanceBundle:
    """A deterministic set of generated guidance files."""

    files: Mapping[str, str]

    def __post_init__(self) -> None:
        ordered = {
            _relative_path(path): content.rstrip("\n") + "\n"
            for path, content in sorted(self.files.items())
        }
        object.__setattr__(self, "files", MappingProxyType(ordered))

    def paths(self) -> tuple[str, ...]:
        """Returns generated paths in stable lexical order."""
        return tuple(self.files)
