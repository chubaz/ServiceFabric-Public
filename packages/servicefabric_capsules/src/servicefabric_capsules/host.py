"""Bounded loopback capsule host sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Callable
from urllib.parse import unquote, urlsplit

from servicefabric_artifacts import FileArtifactStore
from servicefabric_builder import ApplicationPortfolio
from servicefabric_contracts import CapsuleHostRequest, CapsuleHostResult, CapsuleHostSession, EvidenceRecord

from .authoring import CapsuleAuthoringDiagnostic
from .portfolio import CapsulePortfolio, CapsuleResolution
from .routes import CapsuleRouteTable
from .sessions import CapsuleSessionManager


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _HostState:
    resolution: CapsuleResolution
    session: CapsuleHostSession
    artifact_store: FileArtifactStore
    session_manager: CapsuleSessionManager
    route_table: CapsuleRouteTable
    evidence: list[EvidenceRecord] = field(default_factory=list)


@dataclass(frozen=True)
class HostResponse:
    status: int
    headers: dict[str, str]
    body: bytes


class LoopbackCapsuleHost:
    def __init__(
        self,
        portfolio: CapsulePortfolio,
        application_portfolio: ApplicationPortfolio,
        artifact_store: FileArtifactStore,
        request: CapsuleHostRequest,
        clock: Callable[[], datetime] = _utcnow,
    ):
        self.portfolio = portfolio
        self.application_portfolio = application_portfolio
        self.artifact_store = artifact_store
        self.request = request
        self.clock = clock
        self.resolution = portfolio.resolve(request.spec.capsule_id, request.spec.capsule_revision, application_portfolio, artifact_store)
        opened_at = clock()
        expires_at = opened_at + timedelta(seconds=self.resolution.host_policy.spec.maximum_session_seconds)
        self.route_table = CapsuleRouteTable.from_revision(self.resolution.revision)
        self.session_manager = CapsuleSessionManager(
            opened_at=opened_at,
            expires_at=expires_at,
            idle_timeout_seconds=self.resolution.host_policy.spec.idle_timeout_seconds,
            maximum_requests=self.resolution.host_policy.spec.maximum_requests,
        )
        self.session = CapsuleHostSession.model_validate(
            {
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "CapsuleHostSession",
                "metadata": {
                    "id": f"session.{request.spec.capsule_id}.{request.spec.capsule_revision}.{request.spec.request_id}",
                    "name": f"{request.spec.capsule_id} host session",
                    "description": "Bounded loopback capsule host session.",
                    "labels": {},
                    "annotations": {},
                    "owner_ref": request.metadata.owner_ref.model_dump(mode="json"),
                },
                "spec": {
                    "session_id": f"session.{request.spec.capsule_id}.{request.spec.capsule_revision}.{request.spec.request_id}",
                    "capsule_id": request.spec.capsule_id,
                    "capsule_revision": request.spec.capsule_revision,
                    "capsule_digest": self.resolution.revision.spec.revision_digest,
                    "host": "127.0.0.1",
                    "port": 0,
                    "base_url": "http://127.0.0.1:0/",
                    "status": "opening",
                    "opened_at": opened_at,
                    "expires_at": expires_at,
                    "request_budget": {
                        "maximum_wall_clock_ms": self.resolution.host_policy.spec.maximum_session_seconds * 1000,
                    },
                    "requests_served": 0,
                    "artifact_digests": [binding.artifact_digest for binding in self.resolution.revision.spec.artifact_bindings],
                },
            }
        )
        self.session_manager.activate()
        self.session.spec.status = self.session_manager.status
        self._state = _HostState(
            resolution=self.resolution,
            session=self.session,
            artifact_store=artifact_store,
            session_manager=self.session_manager,
            route_table=self.route_table,
        )
        self._server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None
        self._closed = False

    @property
    def address(self) -> tuple[str, int]:
        if self._server is None:
            return ("127.0.0.1", 0)
        return self._server.server_address

    @property
    def result(self) -> CapsuleHostResult:
        evidence = tuple(self._state.evidence)
        return CapsuleHostResult.model_validate(
            {
                "apiVersion": "servicefabric.ai/v1alpha1",
                "kind": "CapsuleHostResult",
                "metadata": self.session.metadata.model_dump(mode="json", by_alias=True),
                "spec": {
                    "status": "success" if not self.session_manager.closed else "partial",
                    "session": self.session.model_dump(mode="json", by_alias=True),
                    "warnings": [],
                    "errors": [],
                    "evidence": [item.model_dump(mode="json", by_alias=True) for item in evidence],
                    "effect_receipts": [],
                    "metrics": {"requests_served": self.session_manager.requests_served},
                },
            }
        )

    def start(self) -> "LoopbackCapsuleHost":
        if self._server is not None:
            return self

        host = "127.0.0.1"

        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _reject(self, code: int) -> None:
                response = outer.dispatch(self.command, self.path, dict(self.headers))
                self.send_response(response.status)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()

            def _serve(self, head_only: bool) -> None:
                response = outer.dispatch(self.command, self.path, dict(self.headers), head_only=head_only)
                self.send_response(response.status)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                if response.body:
                    self.wfile.write(response.body)

            def do_GET(self) -> None:  # noqa: N802
                self._serve(False)

            def do_HEAD(self) -> None:  # noqa: N802
                self._serve(True)

            def log_message(self, format: str, *args: object) -> None:  # noqa: A003
                return

            def _expired(self) -> bool:
                return outer.session_manager.expired(outer.clock())

        try:
            self._server = ThreadingHTTPServer((host, self.request.spec.requested_port), Handler)
        except PermissionError:
            self._server = None
            self._thread = None
            return self
        port = self._server.server_address[1]
        self.session.spec.port = port
        self.session.spec.base_url = f"http://127.0.0.1:{port}/"
        self.session.spec.status = self.session_manager.status
        evidence = EvidenceRecord.model_validate(
            {
                "evidence_id": f"evidence.{self.session.spec.session_id}",
                "evidence_type": "artifact",
                "source_ref": self.session.spec.session_id,
                "locator": self.session.spec.base_url,
                "content_digest": self.session.spec.capsule_digest,
                "collected_at": self.session.spec.opened_at,
                "trust_classification": "platform",
                "claims": ["capsule session opened"],
                "summary": "Loopback capsule host session opened.",
                "provenance_refs": [self.session.spec.capsule_id],
            }
        )
        self._state.evidence.append(evidence)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def dispatch(self, method: str, path: str, headers: dict[str, str] | None = None, *, head_only: bool = False) -> HostResponse:
        headers = headers or {}
        if self.session_manager.closed or self._expired():
            self.session_manager.close()
            self.session.spec.status = "expired"
            return HostResponse(410, self._security_headers(), b"")
        if method not in self.resolution.host_policy.spec.allowed_methods:
            return HostResponse(405, self._security_headers(), b"")
        if headers.get("Content-Length") not in {None, "0"}:
            return HostResponse(413, self._security_headers(), b"")
        raw_path = urlsplit(path).path
        if "%" in path or "\\" in path:
            return HostResponse(404, self._security_headers(), b"")
        normalized_path = unquote(raw_path) or "/"
        try:
            route = self.route_table.resolve(normalized_path)
        except (KeyError, ValueError):
            return HostResponse(404, self._security_headers(), b"")
        if not self.session_manager.can_serve(self.clock()):
            return HostResponse(503, self._security_headers(), b"")
        binding = self.route_table.binding(route.binding_id)
        try:
            body = self.artifact_store.open_file(binding.artifact_digest, route.artifact_path)
        except Exception:
            return HostResponse(404, self._security_headers(), b"")
        if len(body) > self.resolution.host_policy.spec.maximum_response_bytes:
            return HostResponse(413, self._security_headers(), b"")
        self.session_manager.record_request(self.clock())
        self._state.session.spec.requests_served = self.session_manager.requests_served
        self._state.session.spec.status = self.session_manager.status
        if method == "HEAD" or head_only:
            body = b""
        headers_out = self._security_headers()
        headers_out.update(
            {
                "Content-Type": route.media_type,
                "Content-Length": str(len(body)),
                "Cache-Control": "public, max-age=31536000, immutable" if route.cache_policy == "immutable" else "no-store",
            }
        )
        return HostResponse(200, headers_out, body)

    def _expired(self) -> bool:
        return self.session_manager.expired(self.clock())

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.session_manager.close()
        self.session.spec.status = self.session_manager.status
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _security_headers(self) -> dict[str, str]:
        headers = {
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'none'",
        }
        headers.update(self.resolution.host_policy.spec.security_headers)
        return headers

    def __enter__(self) -> "LoopbackCapsuleHost":
        return self.start()

    def __exit__(self, *_: object) -> None:
        self.close()


class CapsuleHostService:
    def __init__(self, portfolio: CapsulePortfolio, application_portfolio: ApplicationPortfolio, artifact_store: FileArtifactStore):
        self.portfolio = portfolio
        self.application_portfolio = application_portfolio
        self.artifact_store = artifact_store

    def open_session(self, request: CapsuleHostRequest) -> LoopbackCapsuleHost:
        host = LoopbackCapsuleHost(self.portfolio, self.application_portfolio, self.artifact_store, request)
        host.start()
        return host
