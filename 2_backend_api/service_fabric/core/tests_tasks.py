from django.test import TestCase
from unittest.mock import patch
from api.models import ServiceInstance, ServiceTemplate, User
from core.tasks import create_service_task

class TestTasks(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@example.com", password="password")
        self.template = ServiceTemplate.objects.create(
            name="Test Template",
            template_key="test_template"
        )
        self.instance = ServiceInstance.objects.create(
            owner=self.user,
            template=self.template,
            name="Test Service",
            service_slug="test-service"
        )

    @patch('core.tasks.GeneratorLogic')
    def test_create_service_task_success(self, MockGeneratorLogic):
        # Setup mock
        mock_logic = MockGeneratorLogic.return_value

        # Call the task
        create_service_task(str(self.instance.id))

        # Verify GeneratorLogic was called correctly
        MockGeneratorLogic.assert_called_once_with(str(self.instance.id))
        mock_logic.prepare_files.assert_called_once()
        mock_logic.generate_configs.assert_called_once()
        mock_logic.start_service.assert_called_once()
        mock_logic.update_proxy.assert_called_once()

        # Verify instance state
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, ServiceInstance.ServiceStatus.RUNNING)

    @patch('core.tasks.GeneratorLogic')
    def test_create_service_task_error(self, MockGeneratorLogic):
        # Setup mock to raise exception
        mock_logic = MockGeneratorLogic.return_value
        mock_logic.prepare_files.side_effect = Exception("Mocked error")

        # Call the task
        create_service_task(str(self.instance.id))

        # Verify instance state on error
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, ServiceInstance.ServiceStatus.ERROR)
        self.assertIn("Creazione fallita: Mocked error", self.instance.description)
