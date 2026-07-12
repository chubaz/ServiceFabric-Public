import unittest

from servicefabric_client import ServiceFabricClient
from servicefabric_client.application_cli import execute, parser


class Runtime:
    def list_applications(self): return ("examples.hello-static",)


class ClientCliTests(unittest.TestCase):
    def test_client_delegates_to_service_boundary(self):
        client = ServiceFabricClient(Runtime())
        self.assertEqual(client.list_applications(), ("examples.hello-static",))

    def test_cli_is_bounded_and_machine_readable(self):
        output = execute(ServiceFabricClient(Runtime()), ["app", "list"])
        self.assertEqual(output, '{"applications": ["examples.hello-static"]}')
        options = parser().format_help()
        self.assertNotIn("command", options)
        self.assertNotIn("source-directory", options)
