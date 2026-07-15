"""Reviewed, loopback-only HTTP transport for static operation bindings."""

from .adapter import HttpOperationAdapter
from .errors import HttpOperationAdapterError

__all__ = ["HttpOperationAdapter", "HttpOperationAdapterError"]
