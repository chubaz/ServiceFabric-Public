import unittest
from pydantic import ValidationError
from servicefabric_contracts.invocation import DeploymentInvocationTarget, RevisionInvocationTarget
class InvocationTests(unittest.TestCase):
    def test_target_modes_are_explicit(self):
        self.assertEqual(DeploymentInvocationTarget(target_kind="deployment", tool_id="math.calculate", deployment_ref="math-prod").target_kind, "deployment")
        with self.assertRaises(ValidationError): RevisionInvocationTarget(target_kind="revision", tool_id="math.calculate", revision_ref="latest")
