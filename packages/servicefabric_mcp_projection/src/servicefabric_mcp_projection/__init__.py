"""Bounded MCP projection types and gateway adapters."""

from .models import (
    McpCallRequest, McpCallResponse, McpCancellationRequest, McpClientCapabilities,
    McpEnvelope, McpProgressNotification, McpProtocolError, McpServerCapabilities,
    McpSessionContext, McpTaskView, McpToolPage, ProjectedMcpTool,
)
from .discovery import DiscoveryService, ProjectionCandidate
from .translation import CallTranslationError, CallTranslator
from .results import project_error, project_result

__all__ = [
    "McpCallRequest", "McpCallResponse", "McpCancellationRequest", "McpClientCapabilities",
    "McpEnvelope", "McpProgressNotification", "McpProtocolError", "McpServerCapabilities",
    "McpSessionContext", "McpTaskView", "McpToolPage", "ProjectedMcpTool",
    "DiscoveryService", "ProjectionCandidate",
    "CallTranslationError", "CallTranslator",
    "project_error", "project_result",
]
