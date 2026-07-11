from app.extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime

class {{APP_SLUG}}Entity(db.Model):
    __tablename__ = 'srv_{{APP_SLUG}}_entities'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False, index=True)
    label = Column(String(255), default='New Entity')
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'data': self.payload,
            'created_at': self.created_at.isoformat()
        }
