"""Bounded capsule client projection."""

from __future__ import annotations


class CapsuleClient:
    def __init__(self, host_service):
        self.host_service = host_service

    def open_session(self, request):
        return self.host_service.open_session(request)

    def dispatch(self, session, method: str, path: str, *, head_only: bool = False):
        return session.dispatch(method, path, head_only=head_only)

    def close_session(self, session) -> None:
        session.close()

