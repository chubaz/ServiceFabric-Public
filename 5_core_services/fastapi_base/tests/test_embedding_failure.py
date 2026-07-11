from __future__ import annotations

import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch

FASTAPI_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("VECTOR_STORAGE_PATH", "/tmp/servicefabric-fastapi-tests")
sys.path.insert(0, str(FASTAPI_ROOT))

from app.services.vector_store import VectorDependencyError, VectorStoreService


class EmbeddingFailureTests(unittest.TestCase):
    def test_gemini_failure_never_returns_a_zero_vector(self) -> None:
        service = VectorStoreService.__new__(VectorStoreService)
        service.gemini_key = "test-key"
        with patch("app.services.vector_store.genai.Client") as client_class:
            client_class.return_value.models.embed_content.side_effect = RuntimeError("provider unavailable")
            with self.assertRaises(VectorDependencyError):
                service._gemini_embedding_wrapper(["document"])
