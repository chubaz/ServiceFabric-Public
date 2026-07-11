# Service Fabric Infrastructure Testing

This document describes the automated integration tests designed to verify the Service Fabric's core architectural mandates.

## 1. Integration Suite (`tests/fabric_integration_suite.py`)

This script tests the **connectivity and routing** across the entire stack. It acts as an external client hitting the Nginx Proxy.

### How to Run
From the project root:
```bash
python3 tests/fabric_integration_suite.py
```
*Note: Ensure the Docker containers are running and the Proxy is accessible on localhost:80.*

### What is tested?
1.  **Proxy Routing**: Asserts that Nginx correctly forwards requests to `backend_api`, `core_flask_service`, and `fastapi_core`.
2.  **Dynamic Service Mounting**: Hits a known shard (e.g., `/app/core/OpenSport/`) to verify that the Flask Core has dynamically registered the Blueprint from the catalog.
3.  **Smart Rendering (HTMX vs Browser)**: 
    - Sends an `HX-Request: true` header and asserts the response is a **partial** (no `<html>` tags).
    - Sends a standard request and asserts the response is a **full wrapper** (contains `<html>` tags).
4.  **Shared Utility Access**: Verifies that the internal routing for `/_shared/` utilities is functional.

## 2. Assertion Targets (Current Status)

| Feature | Assertion Method | Expected Result |
| :--- | :--- | :--- |
| **Service Discovery** | `flask routes` in `core_flask_service` | All 45+ shards must be listed. |
| **Auth Handshake** | `test_jwt_handshake` (in suite) | 200 OK using shared secret. |
| **Gateway Socket** | `curl -i -N -H "Upgrade: websocket"` | 101 Switching Protocols. |
| **Vector Ingest** | `POST /api/v1/vector/ingest` | 200 OK with document IDs. |

---

## 3. Manual Verification Steps

### Check Flask Mounting Logs
```bash
docker-compose logs core_flask_service | grep "Mounted"
```

### Verify Nginx Config Generation
```bash
docker-compose exec proxy nginx -T | grep "location /app/core"
```

### Database Consistency
```bash
docker-compose exec backend_api python manage.py showmigrations
```
