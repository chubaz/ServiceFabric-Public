"""Durable state for factory approvals, reviews, requirements, and handoffs.

This store intentionally does not persist plans, provider events, usage, or task
results. Those remain owned by their canonical runtimes; this lifecycle records
only the factory decisions and references needed to close a run.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import os
from pathlib import Path
import re
from typing import Any, Iterator, TypeVar

from servicefabric_application_factory_contracts import (
    ApplicationFactoryHandoff,
    CandidateReviewDecision,
    FactoryApprovalDecision,
    UnmetRequirement,
)


_RUN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_Record = TypeVar(
    "_Record",
    FactoryApprovalDecision,
    CandidateReviewDecision,
    UnmetRequirement,
)


@dataclass(frozen=True)
class FactoryLifecycleSnapshot:
    """A typed, deterministic view of state belonging to one factory run."""

    run_id: str
    approvals: tuple[FactoryApprovalDecision, ...]
    reviews: tuple[CandidateReviewDecision, ...]
    unmet_requirements: tuple[UnmetRequirement, ...]
    handoff: ApplicationFactoryHandoff | None


class FileFactoryLifecycleStore:
    """Persist factory-owned lifecycle records as an atomic JSON document per run."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def record_approval(self, decision: FactoryApprovalDecision) -> None:
        """Record an immutable factory approval decision idempotently."""
        self._record(decision.run_id, "approvals", decision.decision_id, decision)

    def record_review(self, decision: CandidateReviewDecision) -> None:
        """Record an immutable candidate review decision idempotently."""
        self._record(decision.run_id, "reviews", decision.decision_id, decision)

    def record_unmet_requirement(self, requirement: UnmetRequirement) -> None:
        """Record an immutable unmet requirement idempotently."""
        self._record(
            requirement.run_id,
            "unmet_requirements",
            requirement.requirement_id,
            requirement,
        )

    def record_handoff(self, handoff: ApplicationFactoryHandoff) -> None:
        """Record one final factory handoff without replacing an existing one."""
        if any(item.run_id != handoff.run_id for item in handoff.unmet_requirements):
            raise ValueError("handoff unmet requirements must belong to its run")

        with self._locked(handoff.run_id):
            state = self._load_or_empty(handoff.run_id)
            serialized = handoff.model_dump(mode="json")
            existing = state["handoff"]
            if existing is not None and existing != serialized:
                raise ValueError(f"run {handoff.run_id!r} already has a different handoff")
            if existing is None:
                state["handoff"] = serialized
                self._write(handoff.run_id, state)

    def load(self, run_id: str) -> FactoryLifecycleSnapshot:
        """Load and validate factory-owned records for a run."""
        state = self._load_state(run_id)
        return FactoryLifecycleSnapshot(
            run_id=run_id,
            approvals=tuple(
                FactoryApprovalDecision.model_validate(value)
                for _, value in sorted(state["approvals"].items())
            ),
            reviews=tuple(
                CandidateReviewDecision.model_validate(value)
                for _, value in sorted(state["reviews"].items())
            ),
            unmet_requirements=tuple(
                UnmetRequirement.model_validate(value)
                for _, value in sorted(state["unmet_requirements"].items())
            ),
            handoff=(
                ApplicationFactoryHandoff.model_validate(state["handoff"])
                if state["handoff"] is not None
                else None
            ),
        )

    def _record(self, run_id: str, section: str, record_id: str, record: _Record) -> None:
        with self._locked(run_id):
            state = self._load_or_empty(run_id)
            serialized = record.model_dump(mode="json")
            existing = state[section].get(record_id)
            if existing is not None and existing != serialized:
                raise ValueError(
                    f"run {run_id!r} already has a different {section} record {record_id!r}"
                )
            if existing is None:
                state[section][record_id] = serialized
                self._write(run_id, state)

    @staticmethod
    def _empty_state() -> dict[str, Any]:
        return {
            "approvals": {},
            "handoff": None,
            "reviews": {},
            "unmet_requirements": {},
        }

    def _path(self, run_id: str) -> Path:
        if not _RUN_ID_PATTERN.fullmatch(run_id):
            raise ValueError(f"invalid run_id: {run_id!r}")
        return self.root / f"{run_id}.json"

    def _load_or_empty(self, run_id: str) -> dict[str, Any]:
        return self._load_state(run_id) if self._path(run_id).exists() else self._empty_state()

    def _load_state(self, run_id: str) -> dict[str, Any]:
        value = json.loads(self._path(run_id).read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != set(self._empty_state()):
            raise ValueError(f"invalid factory lifecycle state for run {run_id!r}")
        for section in ("approvals", "reviews", "unmet_requirements"):
            if not isinstance(value[section], dict):
                raise ValueError(f"invalid {section} for run {run_id!r}")
        if value["handoff"] is not None and not isinstance(value["handoff"], dict):
            raise ValueError(f"invalid handoff for run {run_id!r}")

        self._validate_records(run_id, value)
        return value

    @staticmethod
    def _validate_records(run_id: str, state: dict[str, Any]) -> None:
        for record_id, value in state["approvals"].items():
            record = FactoryApprovalDecision.model_validate(value)
            if record_id != record.decision_id or record.run_id != run_id:
                raise ValueError(f"invalid approval record {record_id!r} for run {run_id!r}")
        for record_id, value in state["reviews"].items():
            record = CandidateReviewDecision.model_validate(value)
            if record_id != record.decision_id or record.run_id != run_id:
                raise ValueError(f"invalid review record {record_id!r} for run {run_id!r}")
        for record_id, value in state["unmet_requirements"].items():
            record = UnmetRequirement.model_validate(value)
            if record_id != record.requirement_id or record.run_id != run_id:
                raise ValueError(f"invalid unmet requirement {record_id!r} for run {run_id!r}")
        if state["handoff"] is not None:
            handoff = ApplicationFactoryHandoff.model_validate(state["handoff"])
            if handoff.run_id != run_id:
                raise ValueError(f"invalid handoff for run {run_id!r}")
            if any(item.run_id != run_id for item in handoff.unmet_requirements):
                raise ValueError(f"invalid handoff unmet requirement for run {run_id!r}")

    @contextmanager
    def _locked(self, run_id: str) -> Iterator[None]:
        target = self._path(run_id)
        self.root.mkdir(parents=True, exist_ok=True)
        with target.with_suffix(".lock").open("a+b") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _write(self, run_id: str, value: dict[str, Any]) -> None:
        target = self._path(run_id)
        temporary = target.with_suffix(".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(value, file, sort_keys=True, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, target)
            directory_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary.unlink(missing_ok=True)
