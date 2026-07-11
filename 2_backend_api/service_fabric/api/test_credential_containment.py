import json
import tempfile
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .admin import CloudIntegrationAdmin
from .credential_store import (
    CredentialAccessDenied,
    CredentialRevoked,
    CredentialStoreError,
    CredentialStoreConfigurationError,
    DevelopmentFileCredentialStore,
    ProviderCredential,
    get_credential_store,
)
from .models import CloudIntegration, User
from .serializers import CloudIntegrationSerializer


class CredentialContainmentTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.com', password='password')
        self.other_owner = User.objects.create_user(email='other@example.com', password='password')
        self.credential = ProviderCredential('access-secret', 'refresh-secret', 'client-secret')
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.store_path = f'{self.temporary_directory.name}/credentials.json'
        self.key = Fernet.generate_key().decode('ascii')

    def tearDown(self):
        self.temporary_directory.cleanup()

    def legacy_integration(self, *, owner=None):
        integration = CloudIntegration(
            user=owner or self.owner,
            service=CloudIntegration.ServiceChoices.GOOGLE_DRIVE,
            access_token='access-secret',
            refresh_token='refresh-secret',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        CloudIntegration.objects.bulk_create([integration])
        return CloudIntegration.objects.get(user=integration.user, service=integration.service)

    @override_settings(CREDENTIAL_STORE_ENVIRONMENT='development', CREDENTIAL_STORE_BACKEND='development_file')
    def test_missing_encryption_key_fails_development_store_startup(self):
        with self.assertRaises(CredentialStoreConfigurationError):
            get_credential_store()

    @override_settings(CREDENTIAL_STORE_ENVIRONMENT='production', CREDENTIAL_STORE_BACKEND='development_file')
    def test_production_without_approved_backend_fails_closed(self):
        with self.assertRaises(CredentialStoreConfigurationError):
            get_credential_store()

    def test_store_enforces_owner_provider_and_revocation(self):
        store = DevelopmentFileCredentialStore(encryption_key=self.key, path=self.store_path)
        binding_id = store.put(owner_id=self.owner.id, provider='GDRIVE', credential=self.credential)
        self.assertNotIn('access-secret', Path(self.store_path).read_text(encoding='utf-8'))
        lease = store.get_lease(binding_id=binding_id, owner_id=self.owner.id, provider='GDRIVE', purpose='sync')
        self.assertEqual(lease.credential.access_token, 'access-secret')
        self.assertNotIn('access-secret', repr(lease))
        self.assertNotIn('access-secret', repr(lease.credential))
        with self.assertRaises(TypeError):
            json.dumps(lease)
        with self.assertRaises(CredentialAccessDenied):
            store.get_lease(binding_id=binding_id, owner_id=self.other_owner.id, provider='GDRIVE', purpose='sync')
        with self.assertRaises(CredentialAccessDenied):
            store.get_lease(binding_id=binding_id, owner_id=self.owner.id, provider='DROPBOX', purpose='sync')
        store.revoke(binding_id=binding_id, owner_id=self.owner.id)
        with self.assertRaises(CredentialRevoked):
            store.get_lease(binding_id=binding_id, owner_id=self.owner.id, provider='GDRIVE', purpose='sync')

    def test_new_plaintext_model_writes_are_rejected_and_metadata_is_safe(self):
        integration = CloudIntegration(
            user=self.owner,
            service=CloudIntegration.ServiceChoices.GOOGLE_DRIVE,
            access_token='access-secret',
            refresh_token='refresh-secret',
            expires_at=timezone.now() + timedelta(hours=1),
        )
        with self.assertRaises(ValueError):
            integration.save()
        safe = CloudIntegration.objects.create(
            user=self.owner,
            service=CloudIntegration.ServiceChoices.GOOGLE_DRIVE,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        representation = CloudIntegrationSerializer(safe).data
        self.assertNotIn('access_token', representation)
        self.assertNotIn('refresh_token', representation)
        self.assertNotIn('secret', repr(safe))
        admin = CloudIntegrationAdmin(CloudIntegration, AdminSite())
        self.assertNotIn('access_token', admin.fields)
        self.assertNotIn('refresh_token', admin.fields)

    @override_settings(CREDENTIAL_STORE_ENVIRONMENT='development', CREDENTIAL_STORE_BACKEND='development_file')
    def test_migration_is_idempotent_clears_only_after_verification_and_redacts_reports(self):
        integration = self.legacy_integration()
        with self.settings(CREDENTIAL_STORE_ENCRYPTION_KEY=self.key, CREDENTIAL_STORE_PATH=self.store_path):
            output = StringIO()
            call_command('migrate_cloud_credentials', stdout=output)
            integration.refresh_from_db()
            self.assertIsNotNone(integration.credential_binding_id)
            self.assertIsNone(integration.access_token)
            self.assertIsNone(integration.refresh_token)
            self.assertEqual(integration.credential_migration_status, CloudIntegration.CredentialMigrationStatus.MIGRATED)
            self.assertNotIn('access-secret', output.getvalue())

            second = StringIO()
            call_command('migrate_cloud_credentials', stdout=second)
            self.assertIn('pending=0', second.getvalue())
            report = StringIO()
            call_command('report_cloud_credential_migration', stdout=report)
            self.assertNotIn('access-secret', report.getvalue())

    @override_settings(CREDENTIAL_STORE_ENVIRONMENT='development', CREDENTIAL_STORE_BACKEND='development_file')
    def test_failed_migration_preserves_legacy_values_and_can_resume(self):
        integration = self.legacy_integration()
        with self.settings(CREDENTIAL_STORE_ENCRYPTION_KEY=self.key, CREDENTIAL_STORE_PATH=self.store_path):
            store = DevelopmentFileCredentialStore(encryption_key=self.key, path=self.store_path)
            with patch('api.management.commands.migrate_cloud_credentials.get_credential_store', return_value=store), patch.object(
                store, 'get_lease', side_effect=CredentialStoreError('verification failed')
            ):
                call_command('migrate_cloud_credentials')
            integration.refresh_from_db()
            self.assertEqual(integration.access_token, 'access-secret')
            self.assertEqual(integration.credential_migration_status, CloudIntegration.CredentialMigrationStatus.FAILED)
            self.assertIsNotNone(integration.credential_binding_id)

            call_command('migrate_cloud_credentials')
            integration.refresh_from_db()
            self.assertIsNone(integration.access_token)
            self.assertEqual(integration.credential_migration_status, CloudIntegration.CredentialMigrationStatus.MIGRATED)
