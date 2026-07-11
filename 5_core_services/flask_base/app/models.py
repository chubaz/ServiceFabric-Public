from app.extensions import db
from sqlalchemy import BigInteger, Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID


class ServiceInstance(db.Model):
    """Read-oriented compatibility mapping for Django-owned ``api_serviceinstance``."""

    __tablename__ = 'api_serviceinstance'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    template_id = Column(BigInteger, nullable=True)
    service_type = Column(String(100), nullable=True)
    url_prefix = Column(String(255), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    state_config = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False)
    service_slug = Column(String(100), unique=True, nullable=True)
    is_public = Column(Boolean, nullable=False)
    is_hidden = Column(Boolean, nullable=False)
    is_active = Column(Boolean, nullable=False)
    is_free_tier = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<ServiceInstance {self.service_type} ({self.url_prefix})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'owner_id': str(self.owner_id),
            'service_type': self.service_type,
            'url_prefix': self.url_prefix,
            'config': self.state_config,
            'is_free_tier': self.is_free_tier,
        }
