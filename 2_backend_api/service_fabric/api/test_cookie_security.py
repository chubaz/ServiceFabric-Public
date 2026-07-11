from django.test import TestCase, override_settings

from .models import User


class CookieSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='cookie@example.com', password='password')

    @override_settings(AUTH_COOKIE_SECURE=True, AUTH_COOKIE_SAMESITE='Strict', AUTH_COOKIE_PATH='/')
    def test_access_cookie_uses_explicit_security_settings(self):
        response = self.client.post('/api/auth/login/', {'email': self.user.email, 'password': 'password'})

        self.assertEqual(response.status_code, 200)
        cookie = response.cookies['sf_access_token']
        self.assertTrue(cookie['httponly'])
        self.assertTrue(cookie['secure'])
        self.assertEqual(cookie['samesite'], 'Strict')
        self.assertEqual(cookie['path'], '/')
