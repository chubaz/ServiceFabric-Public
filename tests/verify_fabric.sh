#!/bin/bash

# Service Fabric Verification Script (Bash Edition)
# No dependencies required other than curl

BASE_URL="http://localhost"

echo "--- 1. Infrastructure Connectivity ---"

# Django
STATUS_DJANGO=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/services/")
echo "[Proxy -> Django] /api/services/: $STATUS_DJANGO (Expected 200/401)"

# Flask Core
STATUS_FLASK=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/app/core/status")
echo "[Proxy -> Flask] /app/core/status: $STATUS_FLASK (Expected 200)"

# FastAPI Gateway
STATUS_GATEWAY=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/v1/")
echo "[Proxy -> FastAPI] /api/v1/: $STATUS_GATEWAY (Expected 200, current: $STATUS_GATEWAY)"

echo ""
echo "--- 2. Dynamic Shard Mounting ---"
STATUS_OPENSPORT=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/app/core/OpenSport/")
echo "[Flask] Shard 'OpenSport' reachability: $STATUS_OPENSPORT (Expected 200/500)"

echo ""
echo "--- 3. Smart Rendering Logic ---"
# Test HTMX partial
HTMX_BODY=$(curl -s -H "HX-Request: true" "$BASE_URL/app/core/OpenSport/")
if [[ "$HTMX_BODY" == *"<html"* ]]; then
    echo "[HTMX] FAIL: Partial contains <html> tag"
else
    echo "[HTMX] PASS: Partial is clean (no <html> tag)"
fi

# Test Browser full wrapper
BROWSER_BODY=$(curl -s "$BASE_URL/app/core/OpenSport/")
if [[ "$BROWSER_BODY" == *"<html"* ]]; then
    echo "[Browser] PASS: Full page contains <html> tag"
else
    echo "[Browser] FAIL: Full page missing <html> tag"
fi

echo ""
echo "--- 4. Shared Asset Integrity ---"
STATUS_SHARED=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/app/core/_shared/utils/fabric-client.js")
echo "[Assets] Shared utility access: $STATUS_SHARED (Expected 200)"

echo ""
echo "Verification complete."
