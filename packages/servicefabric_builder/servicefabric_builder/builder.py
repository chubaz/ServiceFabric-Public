"""Native static-web assembly without command execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic

from servicefabric_contracts import ApplicationRevision

from .source import ValidatedSourceBundle


class BuildError(ValueError):
    pass


@dataclass(frozen=True)
class BuildPolicy:
    maximum_files: int = 4096
    maximum_output_bytes: int = 134_217_728
    maximum_elapsed_seconds: float = 30.0


@dataclass(frozen=True)
class BuildOutput:
    output_root: Path
    files: tuple[tuple[str, str, str, int], ...]
    entry_document: str
    total_size: int


class StaticWebBuilder:
    builder_id = "static-web-builder"
    builder_revision = "1.0.0"

    def build(self, revision: ApplicationRevision, source: ValidatedSourceBundle, output_root: Path, policy: BuildPolicy = BuildPolicy()) -> BuildOutput:
        started = monotonic()
        if revision.spec.application_type != "static_web":
            raise BuildError("unsupported application type")
        if len(source.files) > min(policy.maximum_files, revision.spec.build_spec.maximum_file_count):
            raise BuildError("output file count exceeds policy")
        if source.total_size > min(policy.maximum_output_bytes, revision.spec.build_spec.maximum_output_bytes):
            raise BuildError("output size exceeds policy")
        output_root.mkdir(parents=True, exist_ok=False)
        records: list[tuple[str, str, str, int]] = []
        for item in source.files:
            if monotonic() - started > policy.maximum_elapsed_seconds:
                raise BuildError("build exceeded elapsed-time policy")
            destination = output_root / item.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(item.content)
            records.append((item.path, item.digest, item.media_type, len(item.content)))
        entry = revision.spec.build_spec.entry_document
        if entry not in {record[0] for record in records}:
            raise BuildError("entry document is missing")
        return BuildOutput(output_root, tuple(sorted(records)), entry, sum(record[3] for record in records))
