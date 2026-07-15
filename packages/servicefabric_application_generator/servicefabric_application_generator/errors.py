"""Errors raised while materializing a reviewed application blueprint."""

class GeneratorError(RuntimeError):
    """Base class for generator failures."""

class GenerationCollision(GeneratorError):
    """The target already contains an application or unsafe generated path."""

class InvalidGenerationParameter(GeneratorError, ValueError):
    """A required, unknown, or unsafe generation parameter was supplied."""

class GenerationRollback(GeneratorError):
    """Generation failed and the target was rolled back."""
