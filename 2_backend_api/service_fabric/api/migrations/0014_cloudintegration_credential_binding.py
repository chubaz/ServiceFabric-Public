import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('api', '0013_serviceinstance_is_hidden')]

    operations = [
        migrations.AddField(
            model_name='cloudintegration',
            name='credential_binding_id',
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='cloudintegration',
            name='scopes',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='cloudintegration',
            name='credential_migration_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('MIGRATED', 'Migrated'), ('FAILED', 'Failed'), ('NO_CREDENTIAL', 'No credential present')], default='PENDING', max_length=20),
        ),
        migrations.AddField(model_name='cloudintegration', name='created_at', field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now), preserve_default=False),
        migrations.AddField(model_name='cloudintegration', name='updated_at', field=models.DateTimeField(auto_now=True)),
        migrations.AlterField(model_name='cloudintegration', name='access_token', field=models.TextField(blank=True, editable=False, null=True)),
        migrations.AlterField(model_name='cloudintegration', name='refresh_token', field=models.TextField(blank=True, editable=False, null=True)),
    ]
