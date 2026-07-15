import unittest

from pydantic import ValidationError

from servicefabric_capability_model import CapabilityDefinition


EFFECTS = {
    "effects": [{
        "effect_type": "external_read",
        "target_category": "scholarly-service",
        "scope": "research records",
        "reversibility": "not_applicable",
        "verification_required": False,
        "approval_required": False,
        "idempotency_required": False,
    }]
}


def declaration():
    return CapabilityDefinition.model_validate({
        "apiVersion": "servicefabric.local/v1",
        "kind": "CapabilityDefinition",
        "metadata": {"id": "research.scholarship_search", "title": "Scholarly Literature Search", "domain": "research"},
        "spec": {
            "operationRef": "research.search_papers",
            "objective": "Discover scholarly records relevant to a research question.",
            "capabilityClass": "retrieval",
            "concepts": ["academic literature", "scholarly papers"],
            "expectedInputs": ["research query"],
            "expectedOutputs": ["ranked scholarly records"],
            "effects": EFFECTS,
        },
    })


class CapabilityDefinitionTests(unittest.TestCase):
    def test_loads_and_serializes_deterministically(self):
        capability = declaration()
        self.assertEqual(capability.spec.operation_ref, "research.search_papers")
        self.assertEqual(capability.model_dump(by_alias=True), capability.model_dump(by_alias=True))
        self.assertIsNotNone(capability.spec.effect_contract)

    def test_is_immutable_and_strict(self):
        capability = declaration()
        with self.assertRaises(ValidationError):
            capability.spec = capability.spec
        with self.assertRaises(ValidationError):
            CapabilityDefinition.model_validate({**declaration().model_dump(by_alias=True), "extra": True})

    def test_rejects_non_exact_operation_reference(self):
        payload = declaration().model_dump(by_alias=True)
        payload["spec"]["operationRef"] = "research.*"
        with self.assertRaises(ValidationError):
            CapabilityDefinition.model_validate(payload)

    def test_rejects_duplicate_terms(self):
        payload = declaration().model_dump(by_alias=True)
        payload["spec"]["concepts"] = ["papers", "Papers"]
        with self.assertRaises(ValidationError):
            CapabilityDefinition.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
