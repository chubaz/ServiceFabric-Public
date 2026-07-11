import requests
import json
import time

def test_engine_generate():
    url = "http://localhost:5000/dryfus_engine/api/v1/generate"
    
    # Minimal DAG for testing
    dag = {
        "id": "test-dag",
        "title": "Test DAG",
        "nodes": {
            "node-1": {
                "id": "node-1",
                "title": "Introduction",
                "node_type": "CHAPTER",
                "parent_id": "test-dag",
                "depends_on": [],
                "state": "IDLE",
                "shadow_summary": "Introduction to testing.",
                "target_word_count": 100
            }
        }
    }
    
    payload = {
        "dag": dag,
        "provider": "google",
        "model": "gemini-2.0-flash"
    }
    
    print(f"🚀 Sending request to {url}...")
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        print(f"📡 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("📖 Receiving stream:")
            for line in response.iter_lines():
                if line:
                    print(line.decode('utf-8'))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Request failed: {e}")

if __name__ == "__main__":
    test_engine_generate()
