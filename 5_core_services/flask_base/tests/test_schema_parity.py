from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DJANGO_ROOT = REPOSITORY_ROOT / '2_backend_api' / 'service_fabric'
FLASK_ROOT = REPOSITORY_ROOT / '5_core_services' / 'flask_base'
sys.path.insert(0, str(DJANGO_ROOT))
sys.path.insert(0, str(FLASK_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
os.environ.setdefault('SECRET_KEY', 'test-secret')

import django

django.setup()

from api.models import ServiceInstance as DjangoServiceInstance
from app.models import ServiceInstance as FlaskServiceInstance


class SchemaParityTests(unittest.TestCase):
    def test_flask_compatibility_mapping_matches_django_service_instance_contract(self):
        django_fields = {field.column: field for field in DjangoServiceInstance._meta.concrete_fields}
        flask_columns = FlaskServiceInstance.__table__.columns

        self.assertEqual(DjangoServiceInstance._meta.pk.get_internal_type(), 'UUIDField')
        self.assertEqual(django_fields['owner_id'].get_internal_type(), 'ForeignKey')
        self.assertEqual(flask_columns['id'].type.__class__.__name__, 'UUID')
        self.assertEqual(flask_columns['owner_id'].type.__class__.__name__, 'UUID')

        for column_name in ('template_id', 'service_type', 'url_prefix', 'service_slug'):
            self.assertEqual(flask_columns[column_name].nullable, django_fields[column_name].null)
        for column_name in ('name', 'description', 'state_config', 'status', 'is_public', 'is_hidden', 'is_active', 'is_free_tier'):
            self.assertEqual(flask_columns[column_name].nullable, django_fields[column_name].null)

        self.assertTrue(hasattr(FlaskServiceInstance, 'is_free_tier'))
