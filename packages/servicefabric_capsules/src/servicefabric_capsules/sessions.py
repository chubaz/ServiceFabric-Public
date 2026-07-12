"""Session lifecycle helpers for bounded capsule hosting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CapsuleSessionManager:
    opened_at: datetime
    expires_at: datetime
    idle_timeout_seconds: int
    maximum_requests: int
    requests_served: int = 0
    status: str = "opening"
    closed: bool = False
    last_request_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.opened_at.tzinfo is None or self.opened_at.utcoffset() is None:
            raise ValueError("opened_at must be timezone-aware")
        if self.expires_at.tzinfo is None or self.expires_at.utcoffset() is None:
            raise ValueError("expires_at must be timezone-aware")
        if self.expires_at < self.opened_at:
            raise ValueError("session expiry cannot precede opening")
        if self.maximum_requests < 1:
            raise ValueError("maximum requests must be positive")
        if self.idle_timeout_seconds < 1:
            raise ValueError("idle timeout must be positive")
        self.last_request_at = self.opened_at

    def activate(self) -> None:
        if not self.closed:
            self.status = "open"

    def expired(self, now: datetime | None = None) -> bool:
        now = now or _utcnow()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        last_request = self.last_request_at or self.opened_at
        return now >= self.expires_at or (now - last_request) > timedelta(seconds=self.idle_timeout_seconds)

    def can_serve(self, now: datetime | None = None) -> bool:
        return not self.closed and not self.expired(now) and self.requests_served < self.maximum_requests

    def record_request(self, now: datetime | None = None) -> None:
        if not self.can_serve(now):
            raise ValueError("session cannot serve more requests")
        self.requests_served += 1
        self.last_request_at = now or _utcnow()

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.status = "closed"

