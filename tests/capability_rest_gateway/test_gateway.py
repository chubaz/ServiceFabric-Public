from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "capability_rest_gateway" / "src"
sys.path.insert(0, str(SERVICE_ROOT))

from servicefabric_capability_rest_gateway import (  # noqa: E402
    CapabilityRestGateway,
    LoopbackCapabilityRestServer,
)


class CapabilityUnavailableError(RuntimeError):
    pass


class _Facade:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.running = True

    def list_capabilities(self, application_id: str | None = None) -> tuple[object, ...]:
        self.calls.append(("list_capabilities", application_id))
        return (self._description("notes.create"),)

    def describe_capability(self, capability_id: str) -> object:
        self.calls.append(("describe_capability", capability_id))
        if capability_id == "missing":
            raise LookupError(capability_id)
        return self._description(capability_id)

    def capability_availability(self, capability_id: str) -> object:
        self.calls.append(("capability_availability", capability_id))
        return SimpleNamespace(
            capability_id=capability_id,
            application_id="research-notes",
            module_id="api",
            state="available" if self.running else "unavailable",
            reason="module_healthy" if self.running else "module_stopped",
        )

    def invoke_capability(self, capability_id: str, input_value: object) -> object:
        self.calls.append(("invoke_capability", capability_id, input_value))
        if capability_id == "unavailable":
            raise CapabilityUnavailableError()
        return SimpleNamespace(
            capability_id=capability_id,
            operation_id="notes.create",
            binding_id="api.notes.create",
            output={"id": 1, "tags": ("note",)},
        )

    @staticmethod
    def _description(capability_id: str) -> object:
        return SimpleNamespace(
            capability_id=capability_id,
            title="Create note",
            objective="Create a note",
            operation_id="notes.create",
            digest="sha256:example",
            application_ids=("research-notes",),
        )


def _get_json(url: str) -> tuple[int, object]:
    with urlopen(url, timeout=2) as response:
        return response.status, json.load(response)


class CapabilityRestGatewayTests(unittest.TestCase):
    def test_discovery_and_description_delegate_to_consumer_facade(self) -> None:
        facade = _Facade()
        with LoopbackCapabilityRestServer(CapabilityRestGateway(facade)) as server:
            list_status, listed = _get_json(f"{server.endpoint}/capabilities?application=research-notes")
            describe_status, described = _get_json(f"{server.endpoint}/capabilities/notes.create")

        self.assertEqual((list_status, describe_status), (200, 200))
        self.assertEqual(listed, {"capabilities": [described]})
        self.assertEqual(described["operationId"], "notes.create")
        self.assertEqual(
            facade.calls,
            [("list_capabilities", "research-notes"), ("describe_capability", "notes.create")],
        )

    def test_availability_and_invocation_use_facade_with_required_routes(self) -> None:
        facade = _Facade()
        with LoopbackCapabilityRestServer(CapabilityRestGateway(facade)) as server:
            available_status, available = _get_json(f"{server.endpoint}/capabilities/notes.create/availability")
            request = Request(
                f"{server.endpoint}/capabilities/notes.create/invoke",
                data=json.dumps({"input": {"title": "One"}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                invoked_status, invoked = response.status, json.load(response)
            facade.running = False
            stopped_status, stopped = _get_json(f"{server.endpoint}/capabilities/notes.create/availability")

        self.assertEqual((available_status, invoked_status, stopped_status), (200, 200, 200))
        self.assertEqual(available["state"], "available")
        self.assertEqual(invoked["output"], {"id": 1, "tags": ["note"]})
        self.assertEqual(stopped["reason"], "module_stopped")
        self.assertIn(("invoke_capability", "notes.create", {"title": "One"}), facade.calls)

    def test_server_rejects_non_loopback_binding_and_bounds_facade_errors(self) -> None:
        facade = _Facade()
        gateway = CapabilityRestGateway(facade)
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            LoopbackCapabilityRestServer(gateway, host="0.0.0.0")

        with LoopbackCapabilityRestServer(gateway) as server:
            for url, expected in (
                (f"{server.endpoint}/capabilities/missing", 404),
                (f"{server.endpoint}/capabilities/unavailable/invoke", 409),
            ):
                request = (
                    Request(url, data=b'{"input":{}}', headers={"Content-Type": "application/json"}, method="POST")
                    if url.endswith("/invoke")
                    else url
                )
                with self.assertRaises(HTTPError) as raised:
                    urlopen(request, timeout=2)
                self.assertEqual(raised.exception.code, expected)


if __name__ == "__main__":
    unittest.main()
