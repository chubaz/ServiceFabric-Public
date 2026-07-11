from __future__ import annotations

import hashlib
import os

import chromadb
from chromadb.utils import embedding_functions
from google import genai


class VectorDependencyError(RuntimeError):
    """The configured embedding dependency could not safely produce vectors."""


class VectorStoreService:
    def __init__(self):
        persist_dir = os.environ.get("VECTOR_STORAGE_PATH", "/app/user_media/embeddings/chroma_core")
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.ef = self._gemini_embedding_wrapper if self.gemini_key else embedding_functions.DefaultEmbeddingFunction()

    def _gemini_embedding_wrapper(self, texts):
        client = genai.Client(api_key=self.gemini_key)
        embeddings = []
        for text in texts:
            try:
                response = client.models.embed_content(model="text-embedding-004", contents=text)
                embeddings.append(response.embeddings[0].values)
            except Exception as exc:
                raise VectorDependencyError("Gemini embedding request failed") from exc
        return embeddings

    @staticmethod
    def physical_collection_name(tenant_id: str, logical_collection_id: str) -> str:
        tenant_hash = hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:12]
        return f"sf_{tenant_hash}_{logical_collection_id}"

    def get_collection(self, tenant_id: str, logical_collection_id: str):
        return self.client.get_or_create_collection(
            name=self.physical_collection_name(tenant_id, logical_collection_id),
            embedding_function=self.ef,
        )

    def ingest(self, tenant_id: str, logical_collection_id: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        collection = self.get_collection(tenant_id, logical_collection_id)
        collection.add(documents=documents, metadatas=metadatas, ids=ids)
        return {"status": "success", "count": len(ids)}

    def search(self, tenant_id: str, logical_collection_id: str, query_text: str, top_k: int = 3, metadata_filter: dict | None = None):
        collection = self.get_collection(tenant_id, logical_collection_id)
        results = collection.query(query_texts=[query_text], n_results=top_k, where=metadata_filter or None)
        formatted = []
        if results["documents"] and results["documents"][0]:
            for index, document in enumerate(results["documents"][0]):
                formatted.append(
                    {
                        "content": document,
                        "metadata": results["metadatas"][0][index],
                        "distance": results["distances"][0][index] if "distances" in results else None,
                    }
                )
        return formatted

    def delete_by_ids(self, tenant_id: str, logical_collection_id: str, ids: list[str]):
        collection = self.get_collection(tenant_id, logical_collection_id)
        collection.delete(ids=ids)
        return {"status": "deleted", "count": len(ids)}


vector_store = VectorStoreService()
