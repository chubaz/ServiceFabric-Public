from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.vector_store import vector_store

router = APIRouter()

class IngestRequest(BaseModel):
    collection: str
    documents: List[str]
    metadatas: List[Dict]
    ids: List[str]

class SearchRequest(BaseModel):
    collection: str
    query: str
    top_k: Optional[int] = 3
    filter: Optional[Dict] = None

@router.post("/ingest")
async def ingest_vectors(req: IngestRequest):
    try:
        return vector_store.ingest(
            collection_name=req.collection,
            documents=req.documents,
            metadatas=req.metadatas,
            ids=req.ids
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_vectors(req: SearchRequest):
    try:
        return vector_store.search(
            collection_name=req.collection,
            query_text=req.query,
            top_k=req.top_k,
            metadata_filter=req.filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete")
async def delete_vectors(collection: str, ids: List[str]):
    try:
        return vector_store.delete_by_ids(collection, ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
