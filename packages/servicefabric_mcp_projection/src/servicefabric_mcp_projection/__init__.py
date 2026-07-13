"""Bounded MCP projection types and gateway adapters."""

from .models import (
    McpCallRequest, McpCallResponse, McpCancellationRequest, McpClientCapabilities,
    McpEnvelope, McpProgressNotification, McpProtocolError, McpServerCapabilities,
    McpSessionContext, McpTaskView, McpToolPage, ProjectedMcpTool,
)
from .discovery import DiscoveryService, ProjectionCandidate
from .translation import CallTranslationError, CallTranslator
from .results import project_error, project_result
from .progress import CancellationProjector, ProgressProjector
from .tasks import project_task
from .sessions import SessionError, SessionManager
from .transport import InProcessTransport, TransportError

__all__ = [
    "McpCallRequest", "McpCallResponse", "McpCancellationRequest", "McpClientCapabilities",
    "McpEnvelope", "McpProgressNotification", "McpProtocolError", "McpServerCapabilities",
    "McpSessionContext", "McpTaskView", "McpToolPage", "ProjectedMcpTool",
    "DiscoveryService", "ProjectionCandidate",
    "CallTranslationError", "CallTranslator",
    "project_error", "project_result",
    "CancellationProjector", "ProgressProjector",
    "project_task",
    "SessionError", "SessionManager",
    "InProcessTransport", "TransportError",
]
