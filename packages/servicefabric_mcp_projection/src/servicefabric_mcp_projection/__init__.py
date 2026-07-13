"""Bounded MCP projection types and gateway adapters."""

from .models import (
    McpCallRequest, McpCallResponse, McpCancellationRequest, McpClientCapabilities,
    McpEnvelope, McpProgressNotification, McpProtocolError, McpServerCapabilities,
    McpSessionContext, McpTaskView, McpToolPage, ProjectedMcpTool,
)
from .discovery import DiscoveryService, ProjectionCandidate
from .translation import CallTranslationError, CallTranslator
from .results import project_acceptance, project_error, project_result
from .profile import MCP_PROTOCOL_PROFILE
from .progress import CancellationProjector, ProgressProjector
from .tasks import project_task
from .sessions import SessionError, SessionManager, TrustedMcpTransportContext
from .transport import InProcessTransport, TransportError

__all__ = [
    "McpCallRequest", "McpCallResponse", "McpCancellationRequest", "McpClientCapabilities",
    "McpEnvelope", "McpProgressNotification", "McpProtocolError", "McpServerCapabilities",
    "McpSessionContext", "McpTaskView", "McpToolPage", "ProjectedMcpTool",
    "DiscoveryService", "ProjectionCandidate",
    "CallTranslationError", "CallTranslator",
    "project_acceptance", "project_error", "project_result", "MCP_PROTOCOL_PROFILE",
    "CancellationProjector", "ProgressProjector",
    "project_task",
    "SessionError", "SessionManager", "TrustedMcpTransportContext",
    "InProcessTransport", "TransportError",
]
