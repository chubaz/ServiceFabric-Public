from __future__ import annotations

import unittest

from pydantic import TypeAdapter, ValidationError

from servicefabric_contracts.artifacts import ArtifactReference


class ArtifactTests(unittest.TestCase):
    def test_oci_requires_digest(self) -> None:
        with self.assertRaises(ValidationError):
            TypeAdapter(ArtifactReference).validate_python({"artifact_kind": "oci_image", "image": "registry.example/app"})

    def test_external_artifact_has_no_credentials(self) -> None:
        with self.assertRaises(ValidationError):
            TypeAdapter(ArtifactReference).validate_python({"artifact_kind": "external_service", "service_ref": "provider-a", "endpoint": "https://provider.example", "token": "secret"})
