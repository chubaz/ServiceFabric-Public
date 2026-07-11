from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class CredentialStoreError(RuntimeError):
    pass


class CredentialStoreConfigurationError(CredentialStoreError):
    pass


class CredentialAccessDenied(CredentialStoreError):
    pass


class CredentialRevoked(CredentialStoreError):
    pass


@dataclass(frozen=True, slots=True)
class ProviderCredential:
    access_token: str | None = field(repr=False)
    refresh_token: str | None = field(repr=False)
    client_secret: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class CredentialLease:
    binding_id: uuid.UUID
    owner_id: uuid.UUID
    provider: str
    purpose: str
    credential: ProviderCredential = field(repr=False)


class CredentialStore(Protocol):
    def put(self, *, owner_id: uuid.UUID, provider: str, credential: ProviderCredential) -> uuid.UUID: ...

    def get_lease(self, *, binding_id: uuid.UUID, owner_id: uuid.UUID, provider: str, purpose: str) -> CredentialLease: ...

    def revoke(self, *, binding_id: uuid.UUID, owner_id: uuid.UUID) -> None: ...


class DevelopmentFileCredentialStore:
    """Development/test-only Fernet-encrypted credential file store."""

    def __init__(self, *, encryption_key: str, path: str):
        if not encryption_key:
            raise CredentialStoreConfigurationError('Credential-store encryption key is required')
        try:
            self._fernet = Fernet(encryption_key.encode('ascii'))
        except (ValueError, TypeError) as exc:
            raise CredentialStoreConfigurationError('Credential-store encryption key is invalid') from exc
        self._path = Path(path)

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError) as exc:
            raise CredentialStoreError('Credential store is unavailable') from exc

    def _save(self, data: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(dir=self._path.parent, prefix='.credentials-', text=True)
        try:
            with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
                json.dump(data, handle, sort_keys=True)
            os.replace(temporary_path, self._path)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def _encrypt(self, payload: dict[str, object]) -> str:
        return self._fernet.encrypt(json.dumps(payload, separators=(',', ':')).encode('utf-8')).decode('ascii')

    def _decrypt(self, value: str) -> dict[str, object]:
        try:
            return json.loads(self._fernet.decrypt(value.encode('ascii')).decode('utf-8'))
        except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CredentialStoreError('Credential binding cannot be decrypted') from exc

    def put(self, *, owner_id: uuid.UUID, provider: str, credential: ProviderCredential) -> uuid.UUID:
        binding_id = uuid.uuid4()
        data = self._load()
        data[str(binding_id)] = self._encrypt({
            'owner_id': str(owner_id),
            'provider': provider,
            'revoked': False,
            'access_token': credential.access_token,
            'refresh_token': credential.refresh_token,
            'client_secret': credential.client_secret,
        })
        self._save(data)
        return binding_id

    def get_lease(self, *, binding_id: uuid.UUID, owner_id: uuid.UUID, provider: str, purpose: str) -> CredentialLease:
        if not purpose:
            raise CredentialAccessDenied('Credential purpose is required')
        encrypted = self._load().get(str(binding_id))
        if not encrypted:
            raise CredentialAccessDenied('Credential binding is unavailable')
        payload = self._decrypt(encrypted)
        if payload.get('owner_id') != str(owner_id) or payload.get('provider') != provider:
            raise CredentialAccessDenied('Credential binding is not authorized')
        if payload.get('revoked'):
            raise CredentialRevoked('Credential binding has been revoked')
        return CredentialLease(
            binding_id=binding_id, owner_id=owner_id, provider=provider, purpose=purpose,
            credential=ProviderCredential(payload.get('access_token'), payload.get('refresh_token'), payload.get('client_secret')),
        )

    def revoke(self, *, binding_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        data = self._load()
        encrypted = data.get(str(binding_id))
        if not encrypted:
            raise CredentialAccessDenied('Credential binding is unavailable')
        payload = self._decrypt(encrypted)
        if payload.get('owner_id') != str(owner_id):
            raise CredentialAccessDenied('Credential binding is not authorized')
        payload['revoked'] = True
        data[str(binding_id)] = self._encrypt(payload)
        self._save(data)


class ProductionSecretManagerCredentialStore:
    """Boundary for an approved production secrets-manager adapter, intentionally unimplemented."""

    def __init__(self, *args, **kwargs):
        raise CredentialStoreConfigurationError('No approved production credential-store adapter is configured')


def get_credential_store() -> CredentialStore:
    if settings.CREDENTIAL_STORE_ENVIRONMENT == 'production':
        raise CredentialStoreConfigurationError('Cloud integrations are disabled until an approved production store is configured')
    if settings.CREDENTIAL_STORE_BACKEND != 'development_file':
        raise CredentialStoreConfigurationError('Development credential store is not configured')
    return DevelopmentFileCredentialStore(
        encryption_key=settings.CREDENTIAL_STORE_ENCRYPTION_KEY,
        path=settings.CREDENTIAL_STORE_PATH,
    )


def get_integration_lease(*, integration, owner_id: uuid.UUID, purpose: str) -> CredentialLease:
    if integration.user_id != owner_id or not integration.credential_binding_id:
        raise CredentialAccessDenied('Credential binding is not authorized')
    return get_credential_store().get_lease(
        binding_id=integration.credential_binding_id,
        owner_id=owner_id,
        provider=integration.service,
        purpose=purpose,
    )
