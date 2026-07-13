"""Unit tests for workspace path and root resolution."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from servicefabric_workspace.errors import InvalidWorkspaceConfiguration
from servicefabric_workspace.resolution import resolve_workspace


class TestResolution(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_default_current_directory_resolution(self) -> None:
        context = resolve_workspace()
        self.assertEqual(context.layout.root, Path.cwd())
        self.assertEqual(context.layout.state, Path.cwd() / ".servicefabric")
        self.assertEqual(context.mode, "external")
        self.assertEqual(context.resolution_source, "current-directory")

    @patch.dict(os.environ, {}, clear=True)
    def test_explicit_resolution(self) -> None:
        root = Path("/tmp/custom-workspace")
        context = resolve_workspace(explicit_workspace=root)
        self.assertEqual(context.layout.root, root)
        self.assertEqual(context.layout.state, root / ".servicefabric")
        self.assertEqual(context.mode, "external")
        self.assertEqual(context.resolution_source, "explicit")

    @patch.dict(os.environ, {"SERVICEFABRIC_WORKSPACE": "/tmp/env-workspace"}, clear=True)
    def test_environment_workspace_resolution(self) -> None:
        context = resolve_workspace()
        self.assertEqual(context.layout.root, Path("/tmp/env-workspace"))
        self.assertEqual(context.layout.state, Path("/tmp/env-workspace/.servicefabric"))
        self.assertEqual(context.mode, "external")
        self.assertEqual(context.resolution_source, "environment")

    @patch.dict(os.environ, {"SERVICEFABRIC_HOME": "/tmp/legacy-home"}, clear=True)
    def test_legacy_home_resolution_without_yaml(self) -> None:
        context = resolve_workspace()
        self.assertEqual(context.layout.state, Path("/tmp/legacy-home"))
        self.assertEqual(context.mode, "legacy-state-only")
        self.assertEqual(context.resolution_source, "legacy-home")

    @patch.dict(os.environ, {"SERVICEFABRIC_WORKSPACE": "/tmp/ws", "SERVICEFABRIC_HOME": "/tmp/ws/state"}, clear=True)
    def test_both_environment_variables(self) -> None:
        context = resolve_workspace()
        self.assertEqual(context.layout.root, Path("/tmp/ws"))
        self.assertEqual(context.layout.state, Path("/tmp/ws/state"))
        self.assertEqual(context.mode, "external")
        self.assertEqual(context.resolution_source, "environment")

    def test_unsafe_relationships(self) -> None:
        # state is equal to root in external mode must be rejected
        with self.assertRaises(InvalidWorkspaceConfiguration):
            resolve_workspace(explicit_workspace=Path("/tmp/ws"), explicit_state=Path("/tmp/ws"))

        # state is a parent of root in external mode must be rejected
        with self.assertRaises(InvalidWorkspaceConfiguration):
            resolve_workspace(explicit_workspace=Path("/tmp/parent/child"), explicit_state=Path("/tmp/parent"))


if __name__ == "__main__":
    unittest.main()
