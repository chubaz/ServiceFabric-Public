from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from api.credential_store import CredentialStoreError, ProviderCredential, get_credential_store
from api.models import CloudIntegration


class Command(BaseCommand):
    help = 'Move legacy CloudIntegration credentials into the configured credential store without printing secrets.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        try:
            store = get_credential_store()
        except CredentialStoreError as exc:
            raise CommandError('Credential store is unavailable') from exc

        queryset = CloudIntegration.objects.filter(
            Q(access_token__isnull=False) & ~Q(access_token='')
            | Q(refresh_token__isnull=False) & ~Q(refresh_token='')
        ).order_by('pk')
        if options['limit']:
            queryset = queryset[:options['limit']]

        report = {'pending': 0, 'migrated': 0, 'failed': 0}
        for integration in queryset:
            report['pending'] += 1
            try:
                if options['dry_run']:
                    report['migrated'] += 1
                    continue
                binding_id = integration.credential_binding_id
                if not binding_id:
                    binding_id = store.put(
                        owner_id=integration.user_id,
                        provider=integration.service,
                        credential=ProviderCredential(integration.access_token, integration.refresh_token),
                    )
                    # Persist the opaque binding before verification so retries can resume safely.
                    CloudIntegration.objects.filter(pk=integration.pk).update(credential_binding_id=binding_id)
                store.get_lease(
                    binding_id=binding_id,
                    owner_id=integration.user_id,
                    provider=integration.service,
                    purpose='legacy-credential-migration-verification',
                )
                CloudIntegration.objects.filter(pk=integration.pk).update(
                    credential_binding_id=binding_id,
                    access_token=None,
                    refresh_token=None,
                    credential_migration_status=CloudIntegration.CredentialMigrationStatus.MIGRATED,
                )
                report['migrated'] += 1
            except CredentialStoreError:
                CloudIntegration.objects.filter(pk=integration.pk).update(
                    credential_migration_status=CloudIntegration.CredentialMigrationStatus.FAILED,
                )
                report['failed'] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Credential migration report: pending={report['pending']} migrated={report['migrated']} failed={report['failed']}"
        ))
