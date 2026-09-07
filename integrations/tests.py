from django.test import TestCase
from django.contrib.auth.models import User
from .models import Integration, OAuthConnection


class IntegrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_integration_creation(self):
        integration = Integration.objects.create(
            user=self.user,
            provider='gmail',
            access_token='test-token'
        )
        self.assertEqual(integration.provider, 'gmail')
        self.assertTrue(integration.is_active)


class OAuthConnectionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_oauth_connection_creation(self):
        conn = OAuthConnection.objects.create(
            user=self.user,
            provider='gmail',
            access_token='test-access-token',
            refresh_token='test-refresh-token'
        )
        self.assertEqual(conn.provider, 'gmail')
        self.assertTrue(conn.is_active)