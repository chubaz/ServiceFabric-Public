from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from servicefabric_agent_tools import BoundedAgentTools


class _CapabilityFacade:
    def __init__(self, capabilities: object = ()) -> None:
        self.capabilities = capabilities
        self.application_ids: list[str] = []

    def discover(self, application_id: str) -> object:
        self.application_ids.append(application_id)
        return self.capabilities


class _FailingCapabilityFacade:
    def discover(self, application_id: str) -> object:
        raise RuntimeError(f"private provider failure for {application_id}")


class WorkspaceInspectionTests(unittest.TestCase):
    def test_repository_root_is_inspected_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke("workspace.inspect", {})

        self.assertEqual(result.status, "success")
        self.assertEqual(
            result.data, {"path": str(Path(root).resolve()), "exists": True}
        )

    def test_missing_path_is_reported_without_writing_it(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke(
                "workspace.inspect", {"path": "missing/file.txt"}
            )

            self.assertEqual(result.status, "success")
            self.assertFalse(result.data["exists"])
            self.assertFalse((Path(root) / "missing").exists())

    def test_parent_traversal_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke(
                "workspace.inspect", {"path": "../outside"}
            )

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.summary, "path escapes repository")

    def test_absolute_path_outside_repository_is_blocked(self) -> None:
        with (
            tempfile.TemporaryDirectory() as root,
            tempfile.TemporaryDirectory() as outside,
        ):
            result = BoundedAgentTools(root).invoke(
                "workspace.inspect", {"path": outside}
            )

        self.assertEqual(result.status, "blocked")

    def test_symlink_escape_is_blocked(self) -> None:
        with (
            tempfile.TemporaryDirectory() as root,
            tempfile.TemporaryDirectory() as outside,
        ):
            Path(root, "escape").symlink_to(outside, target_is_directory=True)
            result = BoundedAgentTools(root).invoke(
                "workspace.inspect", {"path": "escape/secret.txt"}
            )

        self.assertEqual(result.status, "blocked")

    def test_invalid_inspection_arguments_fail_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            tools = BoundedAgentTools(root)
            invalid_path = tools.invoke("workspace.inspect", {"path": None})
            unsupported = tools.invoke("workspace.inspect", {"depth": 2})

        self.assertEqual(invalid_path.status, "failed")
        self.assertEqual(unsupported.status, "failed")


class CapabilityDiscoveryTests(unittest.TestCase):
    def test_discovery_delegates_to_public_facade(self) -> None:
        facade = _CapabilityFacade(({"capability_id": "text.upper"},))
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root, facade).invoke(
                "capabilities.discover", {"application_id": "text-app"}
            )

        self.assertEqual(result.status, "success")
        self.assertEqual(facade.application_ids, ["text-app"])
        self.assertEqual(result.data["capabilities"], facade.capabilities)

    def test_discovery_without_facade_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke(
                "capabilities.discover", {"application_id": "text-app"}
            )

        self.assertEqual(result.status, "blocked")

    def test_invalid_discovery_arguments_fail_without_calling_facade(self) -> None:
        facade = _CapabilityFacade()
        with tempfile.TemporaryDirectory() as root:
            tools = BoundedAgentTools(root, facade)
            missing = tools.invoke("capabilities.discover", {})
            blank = tools.invoke(
                "capabilities.discover", {"application_id": "  "}
            )
            extra = tools.invoke(
                "capabilities.discover",
                {"application_id": "text-app", "raw": True},
            )

        self.assertEqual([missing.status, blank.status, extra.status], ["failed"] * 3)
        self.assertEqual(facade.application_ids, [])

    def test_facade_failure_is_returned_without_private_details(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root, _FailingCapabilityFacade()).invoke(
                "capabilities.discover", {"application_id": "text-app"}
            )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.summary, "capability discovery failed")
        self.assertNotIn("private", result.summary)


class AllowlistTests(unittest.TestCase):
    def test_unknown_tool_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke("workspace.write", {})

        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.summary, "tool is not allowlisted")

    def test_non_mapping_arguments_fail(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            result = BoundedAgentTools(root).invoke(
                "workspace.inspect", None  # type: ignore[arg-type]
            )

        self.assertEqual(result.status, "failed")


if __name__ == "__main__":
    unittest.main()
