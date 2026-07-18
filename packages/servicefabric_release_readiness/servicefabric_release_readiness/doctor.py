"""Read-only local checks for the ServiceFabric foundation release."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
import tomllib
from typing import Any


@dataclass(frozen=True)
class Check:
    """One deterministic doctor check."""

    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    """The complete result of a local doctor invocation."""

    release: str
    repository_root: str
    checks: tuple[Check, ...]

    @property
    def ok(self) -> bool:
        return all(check.status == "pass" for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "release": self.release,
            "repository_root": self.repository_root,
            "ok": self.ok,
            "checks": [asdict(check) for check in self.checks],
        }


def load_manifest() -> dict[str, Any]:
    """Load the release manifest shipped with this package."""

    manifest_path = Path(__file__).with_name("foundation_release.json")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def run_doctor(repository_root: Path | str) -> DoctorReport:
    """Validate local prerequisites and declared package metadata without mutation."""

    root = Path(repository_root).resolve()
    manifest = load_manifest()
    minimum_python = tuple(int(part) for part in manifest["minimum_python"].split("."))
    checks: list[Check] = [
        Check(
            name="python",
            status="pass" if sys.version_info[:2] >= minimum_python else "fail",
            detail=(
                f"Python {sys.version_info.major}.{sys.version_info.minor} "
                f"(minimum {manifest['minimum_python']})"
            ),
        )
    ]

    for package in manifest["declared_packages"]:
        pyproject_path = root / package["path"] / "pyproject.toml"
        if not pyproject_path.is_file():
            checks.append(Check(package["project_name"], "fail", f"missing {pyproject_path.relative_to(root)}"))
            continue
        try:
            project_name = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["name"]
        except (KeyError, tomllib.TOMLDecodeError) as error:
            checks.append(Check(package["project_name"], "fail", f"invalid project metadata: {error}"))
            continue
        if project_name == package["project_name"]:
            checks.append(Check(project_name, "pass", "declared package metadata matches manifest"))
        else:
            checks.append(
                Check(
                    package["project_name"],
                    "fail",
                    f"manifest declares {package['project_name']}; metadata declares {project_name}",
                )
            )
    return DoctorReport(manifest["release"], str(root), tuple(checks))
