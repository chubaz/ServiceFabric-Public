from __future__ import annotations

import unittest

from pydantic import ValidationError

from servicefabric_contracts.metadata import ResourceMetadata


class MetadataTests(unittest.TestCase):
    def test_rejects_invalid_identifier(self) -> None:
        with self.assertRaises(ValidationError):
            ResourceMetadata.model_validate({"id": "Invalid Id", "name": "Name", "description": "Description", "owner_ref": {"kind": "team", "id": "team-a"}})

    def test_rejects_credential_metadata(self) -> None:
        with self.assertRaises(ValidationError):
            ResourceMetadata.model_validate({"id": "package-a", "name": "Name", "description": "Description", "annotations": {"api_key": "not-allowed"}, "owner_ref": {"kind": "team", "id": "team-a"}})

    def test_rejects_non_normalized_metadata_key(self) -> None:
        with self.assertRaises(ValidationError):
            ResourceMetadata.model_validate({"id": "package-a", "name": "Name", "description": "Description", "labels": {"Invalid Key": "value"}, "owner_ref": {"kind": "team", "id": "team-a"}})
