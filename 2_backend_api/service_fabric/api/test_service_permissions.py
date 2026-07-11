from django.contrib.auth.models import Permission
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import ServiceInstance, ServiceTemplate, User


class ServiceInstancePermissionTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='password')
        self.other_user = User.objects.create_user(email='other@example.com', password='password')
        self.administrator = User.objects.create_user(
            email='administrator@example.com', password='password', is_staff=True
        )
        self.template = ServiceTemplate.objects.create(name='Template', template_key='template')

    def create_service(self, owner, *, free_tier=True, hidden=False):
        index = ServiceInstance.objects.count()
        return ServiceInstance.objects.create(
            owner=owner,
            template=self.template,
            name='Service',
            service_slug=f'service-{index}',
            url_prefix=f'/service-{index}',
            is_free_tier=free_tier,
            is_hidden=hidden,
        )

    def test_anonymous_users_can_read_only_eligible_free_tier_services(self):
        visible = self.create_service(self.owner, free_tier=True, hidden=False)
        hidden = self.create_service(self.owner, free_tier=True, hidden=True)

        response = self.client.get(reverse('service-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['id'] for item in response.data], [str(visible.id)])
        self.assertEqual(self.client.get(reverse('service-detail', args=[hidden.id])).status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_user_can_read_owned_hidden_and_eligible_free_tier_services(self):
        owned_hidden = self.create_service(self.other_user, free_tier=False, hidden=True)
        free_tier = self.create_service(self.owner, free_tier=True, hidden=False)
        self.client.force_authenticate(self.other_user)

        response = self.client.get(reverse('service-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({item['id'] for item in response.data}, {str(owned_hidden.id), str(free_tier.id)})

    def test_free_tier_visibility_does_not_grant_update_patch_or_delete(self):
        for method in ('put', 'patch', 'delete'):
            service = self.create_service(self.owner, free_tier=True)
            self.client.force_authenticate(self.other_user)
            url = reverse('service-detail', args=[service.id])
            if method == 'put':
                response = self.client.put(url, {'name': 'Changed'}, format='json')
            elif method == 'patch':
                response = self.client.patch(url, {'name': 'Changed'}, format='json')
            else:
                response = self.client.delete(url)

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertTrue(ServiceInstance.objects.filter(id=service.id).exists())

    def test_owner_and_expressly_authorized_administrator_can_mutate(self):
        service = self.create_service(self.owner, free_tier=True)
        url = reverse('service-detail', args=[service.id])

        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {'name': 'Owner Changed'}, format='json').status_code, status.HTTP_200_OK)

        permission = Permission.objects.get(codename='change_serviceinstance')
        self.administrator.user_permissions.add(permission)
        self.client.force_authenticate(self.administrator)
        self.assertEqual(self.client.patch(url, {'name': 'Admin Changed'}, format='json').status_code, status.HTTP_200_OK)
