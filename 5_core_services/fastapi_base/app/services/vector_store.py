import os
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from app.core.config import settings

class VectorStoreService:
    def __init__(self):
        # 1. Setup Persistence
        # Ensure it maps to the global user_media volume in Docker
        persist_dir = os.environ.get("VECTOR_STORAGE_PATH", "/app/user_media/embeddings/chroma_core")
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # 2. Setup Embedding Logic
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Default to Gemini if available (cost effective)
        if self.gemini_key:
            self.ef = self._gemini_embedding_wrapper
        else:
            self.ef = embedding_functions.DefaultEmbeddingFunction()

    def _gemini_embedding_wrapper(self, texts):
        """Wrapper for Gemini Embedding API."""
        client = genai.Client(api_key=self.gemini_key)
        embeddings = []
        for text in texts:
            try:
                res = client.models.embed_content(
                    model="text-embedding-004",
                    contents=text
                )
                embeddings.append(res.embeddings[0].values)
            except Exception:
                embeddings.append([0.0] * 768)
        return embeddings

    def get_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.ef
        )

    def ingest(self, collection_name: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        collection = self.get_collection(collection_name)
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return {"status": "success", "count": len(ids)}

    def search(self, collection_name: str, query_text: str, top_k: int = 3, metadata_filter: dict = None):
        collection = self.get_collection(collection_name)
        
        # Build filter if provided
        where_filter = metadata_filter if metadata_filter else None
        
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_filter
        )
        
        # Format results for the API
        formatted = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else None
                })
        return formatted

    def delete_by_ids(self, collection_name: str, ids: list[str]):
        collection = self.get_collection(collection_name)
        collection.delete(ids=ids)
        return {"status": "deleted", "count": len(ids)}

vector_store = VectorStoreService()
