"""Bounded HTTP transport for reviewed local operation bindings."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable, Mapping
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .errors import HttpOperationAdapterError

_ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1"})
_JSON_CONTENT_TYPE = "application/json"
_MAX_TIMEOUT_SECONDS = 300
_MAX_RESPONSE_BYTES = 1_048_576


class HttpBinding(Protocol):
    """The reviewed subset of an operation binding consumed by this adapter."""

    method: str
    path: str
    request_content_type: str
    response_content_type: str
    timeout_seconds: int | None


class _NoRedirect(HTTPRedirectHandler):
    """Never allow a loopback request to be redirected to another endpoint."""

    def redirect_request(self, request: Request, *args: Any, **kwargs: Any) -> None:
        return None


def _open(request: Request, timeout: float) -> Any:
    return build_opener(_NoRedirect()).open(request, timeout=timeout)


class HttpOperationAdapter:
    """Invoke only reviewed HTTP bindings on a literal loopback endpoint."""

    def __init__(
        self,
        *,
        default_timeout_seconds: int = 10,
        opener: Callable[[Request, float], Any] | None = None,
    ) -> None:
        if isinstance(default_timeout_seconds, bool) or not 1 <= default_timeout_seconds <= _MAX_TIMEOUT_SECONDS:
            raise ValueError("default_timeout_seconds must be an integer from 1 through 300")
        self._default_timeout_seconds = default_timeout_seconds
        self._opener = opener or _open

    def invoke(self, endpoint: str, binding: HttpBinding, input_data: Any) -> Any:
        """Invoke one binding and return its JSON response value.

        GET inputs become encoded query parameters after any reviewed path-template
        substitutions. Other methods carry a compact JSON body.
        """
        origin = self._validated_origin(endpoint)
        method, path, timeout = self._validated_binding(binding)
        url, remaining_input = self._resolved_url(origin, path, input_data)
        if method == "GET":
            url = self._url_with_query(url, remaining_input)
        body = self._request_body(method, remaining_input)
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": _JSON_CONTENT_TYPE,
                **({"Content-Type": _JSON_CONTENT_TYPE} if body is not None else {}),
            },
        )
        try:
            with self._opener(request, timeout) as response:
                content_type = response.headers.get_content_type()
                if content_type != _JSON_CONTENT_TYPE:
                    raise HttpOperationAdapterError("invalid_response", "HTTP operation returned a non-JSON response")
                encoded = response.read(_MAX_RESPONSE_BYTES + 1)
        except HttpOperationAdapterError:
            raise
        except HTTPError as error:
            raise HttpOperationAdapterError("remote_rejected", "HTTP operation rejected the request") from error
        except (TimeoutError, socket.timeout) as error:
            raise HttpOperationAdapterError("timeout", "HTTP operation request timed out") from error
        except (OSError, URLError) as error:
            raise HttpOperationAdapterError("unavailable", "HTTP operation endpoint is unavailable") from error

        if len(encoded) > _MAX_RESPONSE_BYTES:
            raise HttpOperationAdapterError("response_too_large", "HTTP operation response exceeds the size limit")
        try:
            return json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HttpOperationAdapterError("invalid_response", "HTTP operation returned invalid JSON") from error

    def _validated_origin(self, endpoint: str) -> str:
        if not isinstance(endpoint, str):
            raise HttpOperationAdapterError("invalid_endpoint", "HTTP operation endpoint must be a loopback URL")
        parsed = urlsplit(endpoint)
        try:
            port = parsed.port
        except ValueError as error:
            raise HttpOperationAdapterError("invalid_endpoint", "HTTP operation endpoint must be a loopback URL") from error
        if (
            parsed.scheme != "http"
            or parsed.hostname not in _LOOPBACK_HOSTS
            or port is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise HttpOperationAdapterError("invalid_endpoint", "HTTP operation endpoint must be a loopback URL")
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))

    def _validated_binding(self, binding: HttpBinding) -> tuple[str, str, int]:
        method = getattr(binding, "method", None)
        path = getattr(binding, "path", None)
        request_content_type = getattr(binding, "request_content_type", _JSON_CONTENT_TYPE)
        response_content_type = getattr(binding, "response_content_type", _JSON_CONTENT_TYPE)
        configured_timeout = getattr(binding, "timeout_seconds", None)
        timeout = self._default_timeout_seconds if configured_timeout is None else configured_timeout
        segments = path.split("/") if isinstance(path, str) else []
        if (
            method not in _ALLOWED_METHODS
            or not isinstance(path, str)
            or not path.startswith("/")
            or "?" in path
            or "#" in path
            or "\\" in path
            or "//" in path
            or any(segment in {".", ".."} for segment in segments)
            or request_content_type != _JSON_CONTENT_TYPE
            or response_content_type != _JSON_CONTENT_TYPE
            or isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or not 1 <= timeout <= _MAX_TIMEOUT_SECONDS
        ):
            raise HttpOperationAdapterError("invalid_binding", "HTTP operation binding is not supported")
        return method, path, timeout

    def _resolved_url(self, origin: str, path: str, input_data: Any) -> tuple[str, Any]:
        values = dict(input_data) if isinstance(input_data, Mapping) else {}
        for segment in path.split("/"):
            if segment.startswith("{") and segment.endswith("}") and len(segment) > 2:
                name = segment[1:-1]
                value = values.pop(name, None)
                if value is None or isinstance(value, (bool, Mapping, list, tuple)):
                    raise HttpOperationAdapterError("invalid_input", "HTTP operation path parameters are invalid")
                path = path.replace("{" + name + "}", quote(str(value), safe=""))
            elif "{" in segment or "}" in segment:
                raise HttpOperationAdapterError("invalid_binding", "HTTP operation binding is not supported")
        if "{" in path or "}" in path:
            raise HttpOperationAdapterError("invalid_binding", "HTTP operation binding is not supported")
        return origin + path, values if isinstance(input_data, Mapping) else input_data

    def _request_body(self, method: str, input_data: Any) -> bytes | None:
        if method == "GET":
            if not isinstance(input_data, Mapping):
                raise HttpOperationAdapterError("invalid_input", "GET HTTP operation input must be an object")
            return None
        try:
            return json.dumps(input_data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise HttpOperationAdapterError("invalid_input", "HTTP operation input must be JSON serializable") from error

    def _url_with_query(self, url: str, input_data: Any) -> str:
        if not isinstance(input_data, Mapping):
            raise HttpOperationAdapterError("invalid_input", "GET HTTP operation input must be an object")
        try:
            query = urlencode(sorted(input_data.items()), doseq=True)
        except (TypeError, ValueError) as error:
            raise HttpOperationAdapterError("invalid_input", "GET HTTP operation input must be query serializable") from error
        return url if not query else url + "?" + query
