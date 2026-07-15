"""Safe errors exposed by the reviewed HTTP operation transport."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HttpOperationAdapterError(RuntimeError):
    """A stable transport failure that deliberately excludes endpoint details."""

    code: str
    message: str

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.message)

    def to_dict(self) -> dict[str, str]:
        """Return the structured error payload suitable for canonical callers."""
        return {"code": self.code, "message": self.message}
