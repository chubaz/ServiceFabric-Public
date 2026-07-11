from __future__ import annotations

import json
import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from app.api.dependencies.auth import require_tenant, verify_fabric_token
from app.core.config import settings
from app.security.principal import PrincipalContext
from app.services.vector_store import VectorDependencyError, vector_store

router = APIRouter()
COLLECTION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,46}$")


def _validate_collection_id(collection: str) -> str:
    if not COLLECTION_ID_PATTERN.fullmatch(collection):
        raise ValueError("collection must be a 1-47 character logical identifier")
    return collection


class IngestRequest(BaseModel):
    collection: str
    documents: list[str]
    metadatas: list[dict[str, Any]]
    ids: list[str]

    @model_validator(mode="after")
    def validate_request(self) -> "IngestRequest":
        _validate_collection_id(self.collection)
        if not self.documents or len(self.documents) > settings.MAX_VECTOR_DOCUMENTS:
            raise ValueError("documents must contain between 1 and the configured maximum")
        if len(self.documents) != len(self.metadatas) or len(self.documents) != len(self.ids):
            raise ValueError("documents, metadatas, and ids must have matching lengths")
        if any(not document or len(document) > settings.MAX_VECTOR_DOCUMENT_CHARS for document in self.documents):
            raise ValueError("document exceeds the configured size limit")
        if any(len(json.dumps(metadata, separators=(",", ":")).encode()) > settings.MAX_VECTOR_METADATA_BYTES for metadata in self.metadatas):
            raise ValueError("metadata exceeds the configured size limit")
        return self


class SearchRequest(BaseModel):
    collection: str
    query: str = Field(min_length=1, max_length=settings.MAX_VECTOR_DOCUMENT_CHARS)
    top_k: int = Field(default=3, ge=1)
    filter: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_request(self) -> "SearchRequest":
        _validate_collection_id(self.collection)
        if self.top_k > settings.MAX_VECTOR_TOP_K:
            raise ValueError("top_k exceeds the configured maximum")
        if self.filter and len(json.dumps(self.filter, separators=(",", ":")).encode()) > settings.MAX_VECTOR_METADATA_BYTES:
            raise ValueError("filter exceeds the configured size limit")
        return self


@router.post("/ingest")
async def ingest_vectors(
    req: IngestRequest,
    principal: PrincipalContext = Depends(verify_fabric_token),
):
    principal = require_tenant(principal)
    try:
        return vector_store.ingest(
            tenant_id=principal.tenant_id,
            logical_collection_id=req.collection,
            documents=req.documents,
            metadatas=req.metadatas,
            ids=req.ids,
        )
    except VectorDependencyError as exc:
        raise HTTPException(status_code=503, detail="Embedding provider is unavailable") from exc


@router.post("/search")
async def search_vectors(
    req: SearchRequest,
    principal: PrincipalContext = Depends(verify_fabric_token),
):
    principal = require_tenant(principal)
    try:
        return vector_store.search(
            tenant_id=principal.tenant_id,
            logical_collection_id=req.collection,
            query_text=req.query,
            top_k=req.top_k,
            metadata_filter=req.filter,
        )
    except VectorDependencyError as exc:
        raise HTTPException(status_code=503, detail="Embedding provider is unavailable") from exc


@router.delete("/delete")
async def delete_vectors(
    collection: Annotated[str, Query(min_length=1, max_length=47)],
    ids: list[str] = Query(min_length=1, max_length=settings.MAX_VECTOR_DOCUMENTS),
    principal: PrincipalContext = Depends(verify_fabric_token),
):
    principal = require_tenant(principal)
    try:
        return vector_store.delete_by_ids(
            tenant_id=principal.tenant_id,
            logical_collection_id=_validate_collection_id(collection),
            ids=ids,
        )
    except VectorDependencyError as exc:
        raise HTTPException(status_code=503, detail="Vector store is unavailable") from exc
