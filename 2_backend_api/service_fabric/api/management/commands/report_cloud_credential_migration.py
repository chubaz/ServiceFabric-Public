from django.core.management.base import BaseCommand
from django.db.models import Q

from api.models import CloudIntegration


class Command(BaseCommand):
    help = 'Report CloudIntegration credential migration status without exposing credential values.'

    def handle(self, *args, **options):
        counts = {
            status: CloudIntegration.objects.filter(credential_migration_status=status).count()
            for status, _ in CloudIntegration.CredentialMigrationStatus.choices
        }
        pending_plaintext = CloudIntegration.objects.filter(
            ~Q(access_token__isnull=True) & ~Q(access_token='')
            | ~Q(refresh_token__isnull=True) & ~Q(refresh_token='')
        ).count()
        self.stdout.write(
            'Credential migration report: '
            f"pending={counts['PENDING']} migrated={counts['MIGRATED']} failed={counts['FAILED']} "
            f"no_credential={counts['NO_CREDENTIAL']} plaintext_pending={pending_plaintext}"
        )
