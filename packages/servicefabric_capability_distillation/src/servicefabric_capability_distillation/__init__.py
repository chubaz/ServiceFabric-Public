"""Manifest-bounded capability candidate generation."""

from .distillation import (
    CapabilityDistillationError,
    CapabilityDistillationRequest,
    distill_capability_candidates,
)

__all__ = [
    "CapabilityDistillationError",
    "CapabilityDistillationRequest",
    "distill_capability_candidates",
]
