import unittest

from pydantic import ValidationError

from servicefabric_contracts import (
    ApplicationArtifactManifest,
    ApplicationDefinition,
    ApplicationRevision,
    SourceBundleManifest,
    StaticWebBuildSpec,
)


DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64
METADATA = {
    "id": "examples.hello-static",
    "name": "Hello static",
    "description": "Reviewed static application",
    "owner_ref": {"kind": "team", "id": "platform"},
}


class ApplicationContractTests(unittest.TestCase):
    def test_definition_is_strict_and_static_only(self):
        payload = {
            "apiVersion": "servicefabric.ai/v1alpha1",
            "kind": "ApplicationDefinition",
            "metadata": METADATA,
            "spec": {
                "application_id": "examples.hello-static",
                "display_name": "Hello static",
                "description": "Reviewed static application",
                "application_type": "static_web",
                "status": "reviewed",
            },
        }
        self.assertEqual(ApplicationDefinition.model_validate(payload).spec.application_type, "static_web")
        payload["spec"]["command"] = "npm run build"
        with self.assertRaises(ValidationError):
            ApplicationDefinition.model_validate(payload)

    def test_revision_rejects_mutable_or_host_source_references(self):
        payload = {
            "apiVersion": "servicefabric.ai/v1alpha1",
            "kind": "ApplicationRevision",
            "metadata": METADATA,
            "spec": {
                "application_id": "examples.hello-static",
                "revision": "1.0.0",
                "application_type": "static_web",
                "source_bundle_ref": "hello-source-v1",
                "source_digest": DIGEST,
                "build_spec": {"entry_document": "index.html"},
                "created_from": OTHER_DIGEST,
            },
        }
        revision = ApplicationRevision.model_validate(payload)
        self.assertEqual(revision.spec.revision, "1.0.0")
        payload["spec"]["source_bundle_ref"] = "/tmp/source"
        with self.assertRaises(ValidationError):
            ApplicationRevision.model_validate(payload)

    def test_source_manifest_is_sorted_and_non_executable(self):
        valid = {
            "source_digest": DIGEST,
            "files": [{"path": "index.html", "content_digest": OTHER_DIGEST, "media_type": "text/html", "size_bytes": 3}],
            "total_size_bytes": 3,
        }
        self.assertEqual(SourceBundleManifest.model_validate(valid).files[0].path, "index.html")
        valid["files"][0]["executable"] = True
        with self.assertRaises(ValidationError):
            SourceBundleManifest.model_validate(valid)

    def test_build_spec_rejects_commands_and_unsafe_paths(self):
        with self.assertRaises(ValidationError):
            StaticWebBuildSpec.model_validate({"entry_document": "../index.html"})
        with self.assertRaises(ValidationError):
            StaticWebBuildSpec.model_validate({"entry_document": "index.html", "package_manager": "npm"})

    def test_artifact_requires_sorted_files_and_entry_document(self):
        payload = {
            "apiVersion": "servicefabric.ai/v1alpha1",
            "kind": "ApplicationArtifactManifest",
            "metadata": {**METADATA, "id": "artifact.hello-static"},
            "spec": {
                "artifact_id": "artifact.hello-static",
                "artifact_digest": DIGEST,
                "application_id": "examples.hello-static",
                "application_revision": "1.0.0",
                "builder_id": "static-web-builder",
                "builder_revision": "1.0.0",
                "source_digest": OTHER_DIGEST,
                "build_spec_digest": DIGEST,
                "files": [{"path": "index.html", "content_digest": OTHER_DIGEST, "media_type": "text/html", "size_bytes": 3}],
                "entry_document": "index.html",
                "total_size_bytes": 3,
                "reproducibility": "reproducible",
                "provenance": {
                    "source_manifest_ref": "hello-source-v1",
                    "source_digest": OTHER_DIGEST,
                    "build_spec_digest": DIGEST,
                    "builder_id": "static-web-builder",
                    "builder_revision": "1.0.0",
                },
            },
        }
        self.assertEqual(ApplicationArtifactManifest.model_validate(payload).spec.total_size_bytes, 3)
        payload["spec"]["entry_document"] = "missing.html"
        with self.assertRaises(ValidationError):
            ApplicationArtifactManifest.model_validate(payload)
