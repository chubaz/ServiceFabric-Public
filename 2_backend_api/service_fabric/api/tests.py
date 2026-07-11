from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, ServiceTemplate, ServiceInstance

class ServiceCreateTest(APITestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        self.template = ServiceTemplate.objects.create(
            name='Test Template',
            template_key='test-template',
            default_state_config={'key': 'value'}
        )
        self.create_url = reverse('service-create-service')

    def test_create_service_authenticated(self):
        """Test creating a service as an authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'My New Service',
            'template_key': 'test-template'
        }
        response = self.client.post(self.create_url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ServiceInstance.objects.count(), 1)
        instance = ServiceInstance.objects.first()
        self.assertEqual(instance.name, 'My New Service')
        self.assertEqual(instance.owner, self.user)
        self.assertEqual(instance.template, self.template)
        self.assertEqual(instance.status, ServiceInstance.ServiceStatus.RUNNING)
        # Verify slug starts with base name (unique part follows)
        self.assertTrue(instance.service_slug.startswith('my-new-service'))
        self.assertGreater(len(instance.service_slug), len('my-new-service'))

    def test_create_service_unauthenticated(self):
        """Test creating a service without authentication."""
        data = {
            'name': 'Unauthenticated Service',
            'template_key': 'test-template'
        }
        response = self.client.post(self.create_url, data)

        # Depending on permission_classes in the viewset,
        # it might be 401 Unauthorized or 403 Forbidden.
        # ServiceInstanceViewSet has permission_classes = [permissions.IsAuthenticated]
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(ServiceInstance.objects.count(), 0)

    def test_create_service_invalid_template(self):
        """Test creating a service with a non-existent template key."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Invalid Template Service',
            'template_key': 'non-existent-template'
        }
        response = self.client.post(self.create_url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('template_key', response.data)
        self.assertEqual(ServiceInstance.objects.count(), 0)
