"""Atomic publication of approved, evidence-backed technique policies."""
from __future__ import annotations

from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

from servicefabric_application_factory_contracts import TechnologyProfile
from servicefabric_distillation_contracts import (
    ApplicationEvidenceBundle,
    DistillationDecision,
    TechniquePolicyCandidate,
    TechniquePolicyDefinition,
)


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
_STATE_FILE = "technique-policy-catalog.json"
_STATE_VERSION = 1


class TechniquePolicyPublicationError(RuntimeError):
    """Base error for reviewed policy candidate and publication failures."""


class TechniquePolicyStorageError(TechniquePolicyPublicationError):
    """Raised for unsafe or malformed catalog storage."""


class TechniquePolicyConflictError(TechniquePolicyPublicationError):
    """Raised when an exact policy version has different content."""


class TechniquePolicyNotFoundError(TechniquePolicyPublicationError):
    """Raised when a requested exact policy version is absent."""


@dataclass(frozen=True)
class TechniquePolicyRecord:
    definition: TechniquePolicyDefinition
    digest: str
    profile_ids: tuple[str, ...]
    evidence_refs: tuple[str, ...]


def technique_policy_content_digest(definition: TechniquePolicyDefinition) -> str:
    """Return the canonical static declaration digest."""
    encoded = json.dumps(
        definition.model_dump(mode="json", by_alias=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def candidate_from_profile_and_evidence(
    definition: TechniquePolicyDefinition,
    profile: TechnologyProfile,
    evidence: ApplicationEvidenceBundle,
) -> TechniquePolicyCandidate:
    """Make one deterministic proposed candidate from approved, successful inputs."""
    _validate_provenance(definition, profile, evidence)
    evidence_refs = tuple(sorted(set(evidence.verification_evidence_refs + evidence.review_decision_refs)))
    seed = "|".join((technique_policy_content_digest(definition), profile.profile_id, evidence.bundle_id))
    candidate_id = f"technique-policy-candidate-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:24]}"
    return TechniquePolicyCandidate(
        candidate_id=candidate_id,
        proposed_definition=definition,
        evidence_refs=evidence_refs,
        rationale=(
            f"Approved technology profile '{profile.profile_id}' references exact policy "
            f"'{definition.policy_id}@{definition.version}' and the evidence bundle has successful verification."
        ),
        confidence=1.0,
        status="proposed",
    )


class TechniquePolicyCatalog:
    """Path-safe local catalog keyed by immutable ``policy_id@version`` values."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    def publish(
        self,
        candidate: TechniquePolicyCandidate,
        decision: DistillationDecision,
        profile: TechnologyProfile,
        evidence: ApplicationEvidenceBundle,
    ) -> TechniquePolicyRecord:
        """Atomically publish a human-approved candidate, or return its identical record."""
        if not isinstance(candidate, TechniquePolicyCandidate):
            raise TypeError("candidate must be a TechniquePolicyCandidate")
        if not isinstance(decision, DistillationDecision):
            raise TypeError("decision must be a DistillationDecision")
        if decision.decision != "approve" or decision.candidate_ref != candidate.candidate_id:
            raise TechniquePolicyPublicationError("publication requires an approval for this candidate")
        if candidate.status != "proposed":
            raise TechniquePolicyPublicationError("only proposed technique-policy candidates may be published")
        _validate_provenance(candidate.proposed_definition, profile, evidence)
        expected = candidate_from_profile_and_evidence(candidate.proposed_definition, profile, evidence)
        if candidate != expected:
            raise TechniquePolicyPublicationError("candidate does not match deterministic profile and evidence inputs")

        definition = candidate.proposed_definition
        key = self._key(definition.policy_id, definition.version)
        digest = technique_policy_content_digest(definition)
        with _CatalogLock(self) as state:
            entry = state["policies"].get(key)
            if entry is not None and entry["digest"] != digest:
                raise TechniquePolicyConflictError(
                    f"policy '{key}' is already published with different content"
                )
            if entry is None:
                entry = {
                    "definition": definition.model_dump(mode="json", by_alias=True),
                    "digest": digest,
                    "profiles": [],
                    "evidence": [],
                }
                state["policies"][key] = entry
            for profile_id in (profile.profile_id,):
                if profile_id not in entry["profiles"]:
                    entry["profiles"].append(profile_id)
            for evidence_ref in candidate.evidence_refs:
                if evidence_ref not in entry["evidence"]:
                    entry["evidence"].append(evidence_ref)
            entry["profiles"].sort()
            entry["evidence"].sort()
            self._write_state(state)
            return self._record(entry)

    def describe(self, policy_id: str, version: str) -> TechniquePolicyRecord:
        state = self._read_state()
        try:
            return self._record(state["policies"][self._key(policy_id, version)])
        except KeyError as exc:
            raise TechniquePolicyNotFoundError(f"policy '{policy_id}@{version}' is not published") from exc

    def list(self, policy_id: str | None = None) -> tuple[TechniquePolicyRecord, ...]:
        if policy_id is not None:
            self._validate_identifier(policy_id, "policy_id")
        state = self._read_state()
        entries = (
            (entry for key, entry in state["policies"].items() if key.startswith(f"{policy_id}@"))
            if policy_id is not None else (state["policies"][key] for key in sorted(state["policies"]))
        )
        return tuple(self._record(entry) for entry in entries)

    @staticmethod
    def _key(policy_id: str, version: str) -> str:
        TechniquePolicyCatalog._validate_identifier(policy_id, "policy_id")
        if not isinstance(version, str) or not version:
            raise TechniquePolicyStorageError("version must be a non-empty string")
        return f"{policy_id}@{version}"

    @staticmethod
    def _validate_identifier(value: str, name: str) -> None:
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise TechniquePolicyStorageError(f"{name} must be a safe ServiceFabric identifier")

    def _prepare_root(self) -> Path:
        if self._root.is_symlink():
            raise TechniquePolicyStorageError("catalog root must not be a symlink")
        try:
            self._root.mkdir(mode=0o700, parents=True, exist_ok=True)
            status = self._root.lstat()
        except OSError as exc:
            raise TechniquePolicyStorageError("catalog root is not accessible") from exc
        if not self._root.is_dir() or os.path.islink(self._root) or not stat.S_ISDIR(status.st_mode):
            raise TechniquePolicyStorageError("catalog root must be a real directory")
        return self._root

    def _read_state(self) -> dict[str, Any]:
        path = self._prepare_root() / _STATE_FILE
        if path.is_symlink():
            raise TechniquePolicyStorageError("catalog state file must not be a symlink")
        if not path.exists():
            return {"version": _STATE_VERSION, "policies": {}}
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TechniquePolicyStorageError("catalog state file is unreadable") from exc
        self._validate_state(state)
        return state

    def _write_state(self, state: dict[str, Any]) -> None:
        self._validate_state(state)
        root = self._prepare_root()
        path = root / _STATE_FILE
        if path.is_symlink():
            raise TechniquePolicyStorageError("catalog state file must not be a symlink")
        descriptor, temporary = tempfile.mkstemp(prefix=".technique-policy-", suffix=".tmp", dir=root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(state, handle, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except OSError as exc:
            raise TechniquePolicyStorageError("catalog state could not be written atomically") from exc
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _validate_state(state: object) -> None:
        if not isinstance(state, dict) or set(state) != {"version", "policies"} or state["version"] != _STATE_VERSION or not isinstance(state["policies"], dict):
            raise TechniquePolicyStorageError("catalog state has an unsupported shape")
        for key, entry in state["policies"].items():
            if not isinstance(key, str) or "@" not in key or not isinstance(entry, dict) or set(entry) != {"definition", "digest", "profiles", "evidence"}:
                raise TechniquePolicyStorageError("catalog policy entry has an unsupported shape")
            try:
                definition = TechniquePolicyDefinition.model_validate(entry["definition"])
            except Exception as exc:
                raise TechniquePolicyStorageError("catalog policy definition is invalid") from exc
            if key != TechniquePolicyCatalog._key(definition.policy_id, definition.version) or entry["digest"] != technique_policy_content_digest(definition):
                raise TechniquePolicyStorageError("catalog policy key or digest is invalid")
            for name in ("profiles", "evidence"):
                if not isinstance(entry[name], list) or entry[name] != sorted(set(entry[name])) or not all(isinstance(value, str) and value for value in entry[name]):
                    raise TechniquePolicyStorageError(f"catalog {name} must be sorted, unique, non-empty strings")

    @staticmethod
    def _record(entry: dict[str, Any]) -> TechniquePolicyRecord:
        return TechniquePolicyRecord(
            definition=TechniquePolicyDefinition.model_validate(entry["definition"]),
            digest=entry["digest"],
            profile_ids=tuple(entry["profiles"]),
            evidence_refs=tuple(entry["evidence"]),
        )


class _CatalogLock:
    def __init__(self, catalog: TechniquePolicyCatalog) -> None:
        self._catalog = catalog
        self._handle: Any = None

    def __enter__(self) -> dict[str, Any]:
        root = self._catalog._prepare_root()
        lock_path = root / ".technique-policy.lock"
        if lock_path.is_symlink():
            raise TechniquePolicyStorageError("catalog lock file must not be a symlink")
        try:
            self._handle = lock_path.open("a+", encoding="utf-8")
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
            return self._catalog._read_state()
        except OSError as exc:
            raise TechniquePolicyStorageError("catalog lock could not be acquired") from exc

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._handle is not None:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
            self._handle.close()


def _validate_provenance(
    definition: TechniquePolicyDefinition, profile: TechnologyProfile, evidence: ApplicationEvidenceBundle
) -> None:
    if not isinstance(definition, TechniquePolicyDefinition):
        raise TypeError("definition must be a TechniquePolicyDefinition")
    if not isinstance(profile, TechnologyProfile) or not profile.approved:
        raise TechniquePolicyPublicationError("technique policies require an approved technology profile")
    if not isinstance(evidence, ApplicationEvidenceBundle):
        raise TypeError("evidence must be an ApplicationEvidenceBundle")
    if evidence.technology_profile_id != profile.profile_id:
        raise TechniquePolicyPublicationError("evidence bundle must reference the approved technology profile")
    if evidence.application_blueprint_id != profile.application_blueprint_id:
        raise TechniquePolicyPublicationError("evidence and profile must reference the same application blueprint")
    if not evidence.verification_evidence_refs or evidence.unmet_requirement_refs:
        raise TechniquePolicyPublicationError("technique policies require successful verification evidence")
    if definition.policy_id not in {policy_id for module in profile.module_selections for policy_id in module.technique_policy_ids}:
        raise TechniquePolicyPublicationError("approved profile does not reference the technique policy")
