from __future__ import annotations

import asyncio
import sys
import unittest
import os
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

FASTAPI_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("VECTOR_STORAGE_PATH", "/tmp/servicefabric-fastapi-tests")
sys.path.insert(0, str(FASTAPI_ROOT))

from app.api.dependencies.auth import verify_fabric_token
from app.api.endpoints.vector import IngestRequest, SearchRequest, ingest_vectors
from app.services.vector_store import VectorDependencyError, VectorStoreService
from tests.helpers import issue_token


class VectorSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.principal = asyncio.run(verify_fabric_token(f"Bearer {issue_token()}"))
        self.payload = IngestRequest(
            collection="knowledge",
            documents=["safe document"],
            metadatas=[{"source": "test"}],
            ids=["document-1"],
        )

    def test_vector_routes_reject_anonymous_requests(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(verify_fabric_token(None))
        self.assertEqual(raised.exception.status_code, 401)

    def test_physical_collection_is_tenant_scoped(self) -> None:
        self.assertNotEqual(
            VectorStoreService.physical_collection_name("tenant-a", "knowledge"),
            VectorStoreService.physical_collection_name("tenant-b", "knowledge"),
        )

    def test_ingest_uses_verified_tenant_not_a_global_collection_name(self) -> None:
        with patch("app.api.endpoints.vector.vector_store.ingest", return_value={"status": "success", "count": 1}) as ingest:
            response = asyncio.run(ingest_vectors(self.payload, self.principal))
        self.assertEqual(response["status"], "success")
        self.assertEqual(ingest.call_args.kwargs["tenant_id"], "tenant-a")
        self.assertEqual(ingest.call_args.kwargs["logical_collection_id"], "knowledge")

    def test_top_k_and_collection_id_are_bounded(self) -> None:
        with self.assertRaises(ValueError):
            SearchRequest(collection="invalid collection", query="query", top_k=999)

    def test_embedding_failure_is_an_explicit_dependency_error(self) -> None:
        with patch(
            "app.api.endpoints.vector.vector_store.ingest", side_effect=VectorDependencyError("provider failure")
        ):
            with self.assertRaises(HTTPException) as raised:
                asyncio.run(ingest_vectors(self.payload, self.principal))
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "Embedding provider is unavailable")
