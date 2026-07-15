from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "capability_rest_gateway"
sys.path.insert(0, str(SERVICE_ROOT))

from servicefabric_capability_rest_gateway import (  # noqa: E402
    CapabilityRestGateway,
    LoopbackCapabilityRestServer,
)


class _Runtime:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.running = True

    def list_capabilities(self, application_id: str | None = None) -> tuple[dict[str, object], ...]:
        self.calls.append(("list_capabilities", application_id))
        return ({"metadata": {"id": "notes.create"}, "applications": ["research-notes"]},)

    def describe_capability(self, capability_id: str) -> dict[str, object]:
        self.calls.append(("describe_capability", capability_id))
        return {"metadata": {"id": capability_id}, "spec": {"operationRef": "notes.create"}}

    def availability(self, capability_id: str) -> dict[str, object]:
        self.calls.append(("availability", capability_id))
        return {
            "capabilityId": capability_id,
            "state": "available" if self.running else "unavailable",
            "reason": "module_healthy" if self.running else "module_stopped",
        }

    def invoke(self, capability_id: str, input_value: object) -> dict[str, object]:
        self.calls.append(("invoke", capability_id, input_value))
        return {"capability_id": capability_id, "output": {"id": 1}}


def _get_json(url: str) -> tuple[int, object]:
    with urlopen(url, timeout=2) as response:
        return response.status, json.load(response)


class CapabilityRestGatewayTests(unittest.TestCase):
    def test_discovery_and_description_delegate_to_runtime(self) -> None:
        runtime = _Runtime()
        with LoopbackCapabilityRestServer(CapabilityRestGateway(runtime)) as server:
            list_status, listed = _get_json(f"{server.endpoint}/v1/capabilities?application=research-notes")
            describe_status, described = _get_json(f"{server.endpoint}/v1/capabilities/notes.create")

        self.assertEqual((list_status, describe_status), (200, 200))
        self.assertEqual(listed["capabilities"][0]["metadata"]["id"], "notes.create")
        self.assertEqual(described["spec"]["operationRef"], "notes.create")
        self.assertEqual(
            runtime.calls,
            [("list_capabilities", "research-notes"), ("describe_capability", "notes.create")],
        )

    def test_availability_and_invocation_share_runtime_while_registration_remains(self) -> None:
        runtime = _Runtime()
        with LoopbackCapabilityRestServer(CapabilityRestGateway(runtime)) as server:
            available_status, available = _get_json(
                f"{server.endpoint}/v1/capabilities/notes.create/availability"
            )
            request = Request(
                f"{server.endpoint}/v1/capabilities/notes.create:invoke",
                data=json.dumps({"input": {"title": "One"}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                invoked_status, invoked = response.status, json.load(response)
            runtime.running = False
            stopped_status, stopped = _get_json(
                f"{server.endpoint}/v1/capabilities/notes.create/availability"
            )
            listed_status, listed = _get_json(f"{server.endpoint}/v1/capabilities")

        self.assertEqual((available_status, invoked_status, stopped_status, listed_status), (200, 200, 200, 200))
        self.assertEqual(available["state"], "available")
        self.assertEqual(invoked["output"], {"id": 1})
        self.assertEqual(
            stopped,
            {"capabilityId": "notes.create", "reason": "module_stopped", "state": "unavailable"},
        )
        self.assertEqual(listed["capabilities"][0]["metadata"]["id"], "notes.create")
        self.assertIn(("invoke", "notes.create", {"title": "One"}), runtime.calls)

    def test_server_rejects_non_loopback_binding_and_invalid_invocation_body(self) -> None:
        gateway = CapabilityRestGateway(_Runtime())
        with self.assertRaisesRegex(ValueError, "127.0.0.1"):
            LoopbackCapabilityRestServer(gateway, host="0.0.0.0")

        with LoopbackCapabilityRestServer(gateway) as server:
            request = Request(
                f"{server.endpoint}/v1/capabilities/notes.create:invoke",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with self.assertRaises(HTTPError) as raised:
                urlopen(request, timeout=2)

        self.assertEqual(raised.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
