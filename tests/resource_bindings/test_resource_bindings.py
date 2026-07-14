"""Tests for local resource binding abstractions."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for package in (
    "servicefabric_application_model",
    "servicefabric_resource_bindings",
):
    sys.path.insert(0, str(ROOT / "packages" / package))

from servicefabric_application_model import ResourceRequest
from servicefabric_resource_bindings import (
    DuplicateResourceBinding,
    InvalidResourceBinding,
    LocalResourceDefinition,
    ResourceBindingCatalog,
    ResourceBindingRequest,
    ResourceBindingTypeMismatch,
    StaticLocalResourceProvider,
    environment_key_for,
)


class ResourceBindingTests(unittest.TestCase):
    def test_static_provider_binds_canonical_resource_request(self) -> None:
        provider = StaticLocalResourceProvider(
            [
                LocalResourceDefinition(
                    id="primary-store",
                    type="relational-database",
                    endpoint="postgresql://127.0.0.1:5432/app",
                    secret_refs={"password": "secret://workspace/resources/primary-store/password"},
                )
            ]
        )
        request = ResourceBindingRequest.from_application_request(
            ResourceRequest(
                id="primary-store",
                type="relational-database",
                scope="application",
            )
        )

        binding = provider.bind(request)

        self.assertEqual(binding.id, "primary-store")
        self.assertEqual(
            binding.environment,
            {"SF_PRIMARY_STORE_URL": "postgresql://127.0.0.1:5432/app"},
        )
        self.assertEqual(
            binding.secret_refs,
            {
                "SF_PRIMARY_STORE_PASSWORD": (
                    "secret://workspace/resources/primary-store/password"
                )
            },
        )

    def test_catalog_plans_flattened_environment_and_secret_refs(self) -> None:
        catalog = ResourceBindingCatalog(
            [
                StaticLocalResourceProvider(
                    [
                        LocalResourceDefinition(
                            id="jobs-queue",
                            type="message-queue",
                            endpoint="redis://localhost:6379/0",
                            environment={"SF_JOBS_QUEUE_NAME": "jobs"},
                        )
                    ]
                )
            ]
        )

        plan = catalog.plan(
            "worker",
            [
                ResourceBindingRequest(
                    id="jobs-queue",
                    type="message-queue",
                    scope="application",
                )
            ],
        )

        self.assertEqual(plan.module_id, "worker")
        self.assertEqual(
            plan.environment,
            {
                "SF_JOBS_QUEUE_NAME": "jobs",
                "SF_JOBS_QUEUE_URL": "redis://localhost:6379/0",
            },
        )
        self.assertEqual(plan.secret_refs, {})

    def test_reject_duplicate_resource_ids(self) -> None:
        with self.assertRaises(DuplicateResourceBinding):
            StaticLocalResourceProvider(
                [
                    LocalResourceDefinition(id="cache", type="redis"),
                    LocalResourceDefinition(id="cache", type="redis"),
                ]
            )

    def test_reject_type_mismatch(self) -> None:
        provider = StaticLocalResourceProvider(
            [LocalResourceDefinition(id="cache", type="redis")]
        )

        with self.assertRaises(ResourceBindingTypeMismatch):
            provider.bind(ResourceBindingRequest(id="cache", type="message-queue"))

    def test_reject_public_endpoint_and_literal_credentials(self) -> None:
        with self.assertRaisesRegex(InvalidResourceBinding, "loopback"):
            StaticLocalResourceProvider(
                [
                    LocalResourceDefinition(
                        id="primary-store",
                        type="relational-database",
                        endpoint="postgresql://db.example.test:5432/app",
                    )
                ]
            )

        with self.assertRaisesRegex(InvalidResourceBinding, "credentials"):
            StaticLocalResourceProvider(
                [
                    LocalResourceDefinition(
                        id="primary-store",
                        type="relational-database",
                        endpoint="postgresql://user:pass@127.0.0.1:5432/app",
                    )
                ]
            )

    def test_reject_literal_secret_values(self) -> None:
        with self.assertRaisesRegex(InvalidResourceBinding, "opaque"):
            StaticLocalResourceProvider(
                [
                    LocalResourceDefinition(
                        id="primary-store",
                        type="relational-database",
                        secret_refs={"password": "plain-text-password"},
                    )
                ]
            )

    def test_environment_key_is_deterministic(self) -> None:
        self.assertEqual(environment_key_for("primary-store", "url"), "SF_PRIMARY_STORE_URL")


if __name__ == "__main__":
    unittest.main()
