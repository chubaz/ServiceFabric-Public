"""Independent WSGI example using only the remote ServiceFabric client."""

import json
import os
from urllib.parse import parse_qs

from servicefabric_client.config import ServiceFabricConnection
from servicefabric_client.connection import RemoteServiceFabricClient


def application(environ, start_response):
    query = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0]
    if not query:
        start_response("400 Bad Request", [("Content-Type", "application/json")])
        return [b'{"error":"q is required"}']
    connection = ServiceFabricConnection.load(os.environ.get("SERVICEFABRIC_CONNECTION", "servicefabric.toml"))
    result = RemoteServiceFabricClient(connection.endpoint, toolset=connection.toolset).invoke("research.search_papers", {"query": query, "maximum_results": 5})
    body = json.dumps(result.model_dump(mode="json", by_alias=True), sort_keys=True).encode()
    start_response("200 OK", [("Content-Type", "application/json"), ("Content-Length", str(len(body)))])
    return [body]
