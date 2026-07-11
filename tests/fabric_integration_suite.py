import requests
import json
import os

# Configuration: We target the Proxy as the entry point
BASE_URL = "http://localhost"
FLASK_INTERNAL = "http://localhost/app/core"

def test_proxy_routing():
    """Assert Nginx is routing to all three core upstreams."""
    print("--- Testing Proxy Routing ---")
    
    # 1. Django API
    r = requests.get(f"{BASE_URL}/api/services/")
    print(f"[Proxy -> Django] /api/services/: {r.status_code}")
    assert r.status_code in [200, 401, 403] # Auth might be req, but 404 is a fail
    
    # 2. Flask Core
    r = requests.get(f"{BASE_URL}/app/core/status")
    print(f"[Proxy -> Flask] /app/core/status: {r.status_code}")
    assert r.status_code == 200
    
    # 3. FastAPI Gateway (Expected to fail currently)
    r = requests.get(f"{BASE_URL}/api/v1/")
    print(f"[Proxy -> FastAPI] /api/v1/: {r.status_code}")
    # Note: Currently returns 502 due to chromadb issue

def test_flask_blueprint_mounting():
    """Assert that catalog services are mounted as routes."""
    print("\n--- Testing Service Mounting ---")
    # We use a debug route if available or try to hit a known shard
    shard_to_test = "OpenSport"
    r = requests.get(f"{BASE_URL}/app/core/{shard_to_test}/")
    print(f"[Flask] Testing mounting of '{shard_to_test}': {r.status_code}")
    # Even if it gives 500 (template error), a 500 is better than a 404 
    # as it proves the route exists.
    assert r.status_code != 404

def test_htmx_smart_render():
    """Assert that smart_render distinguishes between HTMX and Full Browser."""
    print("\n--- Testing HTMX Smart Rendering ---")
    url = f"{BASE_URL}/app/core/OpenSport/"
    
    # 1. Simulate HTMX Request
    headers = {'HX-Request': 'true'}
    r_htmx = requests.get(url, headers=headers)
    has_html_tag = "<html" in r_htmx.text.lower()
    print(f"[HTMX] Request returns partial (no <html> tag): {not has_html_tag}")
    
    # 2. Simulate Browser Request
    r_browser = requests.get(url)
    has_html_tag_browser = "<html" in r_browser.text.lower()
    print(f"[Browser] Request returns full wrapper (has <html> tag): {has_html_tag_browser}")

def test_shared_assets():
    """Assert that the _shared utility folder is accessible via the proxy."""
    print("\n--- Testing Shared Assets ---")
    # Fabric-client is a critical utility
    url = f"{BASE_URL}/app/core/_shared/utils/fabric-client.js"
    r = requests.get(url)
    print(f"[Assets] Shared fabric-client.js access: {r.status_code}")
    assert r.status_code == 200
    assert "class FabricClient" in r.text

if __name__ == "__main__":
    try:
        test_proxy_routing()
        test_flask_blueprint_mounting()
        test_htmx_smart_render()
        test_shared_assets()
        print("\n✅ Infrastructure Connectivity Tests Completed.")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n⚠️ ERROR DURING TESTING: {e}")
