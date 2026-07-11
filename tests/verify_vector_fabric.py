import sys
import os

# Ensure we can import from shared utils
# In the container, 6_service_catalog is mounted at /app/services_catalog
# But for local dev testing we use the relative path
sys.path.append(os.path.abspath('6_service_catalog'))

try:
    from _shared.utils.fabric_sdk import fabric
except ImportError:
    print("Could not find fabric_sdk. Ensure the path is correct.")
    sys.exit(1)

def test_fabric_memory():
    print("\n" + "="*50)
    print("🚀 SERVICE FABRIC: CENTRAL VECTOR STORE TEST")
    print("="*50)
    
    collection = "fabric_integration_test"
    test_id = f"test_{os.urandom(4).hex()}"
    content = "The Service Fabric uses a hub-and-spoke model for real-time events and vectorized knowledge."

    # 1. Ingest into Central Store
    print(f"\n[STEP 1] Ingesting knowledge...")
    print(f"   Content: '{content}'")
    
    ingest_res = fabric.vector_store.ingest(
        collection=collection,
        documents=[content],
        metadatas=[{"app": "test_suite", "version": "1.0"}],
        ids=[test_id]
    )
    
    if "error" in ingest_res:
        print(f"   ❌ INGESTION FAILED: {ingest_res['error']}")
        return

    print(f"   ✅ SUCCESS: Knowledge stored in Central Gateway.")

    # 2. Semantic Search
    query = "How does the Service Fabric handle events and knowledge?"
    print(f"\n[STEP 2] Performing Semantic Search...")
    print(f"   Query: '{query}'")
    
    search_res = fabric.vector_store.search(
        collection=collection,
        query=query,
        top_k=1
    )

    if isinstance(search_res, list) and len(search_res) > 0:
        found_text = search_res[0].get('content')
        distance = search_res[0].get('distance', 0)
        print(f"   ✅ SUCCESS: Fabric retrieved relevant context!")
        print(f"   🧠 Retrieved: '{found_text}'")
        print(f"   📏 Similarity Distance: {distance:.4f}")
    else:
        print(f"   ❌ SEARCH FAILED: No results returned. Response: {search_res}")

    print("\n" + "="*50)
    print("✨ TEST COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_fabric_memory()
