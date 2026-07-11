from app.extensions import db
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

class {{APP_SLUG}}Item(db.Model):
    """
    Rappresenta un'entità di dati specifica per questo Shard.
    Il nome della classe verrà convertito in CamelCase dall'App Factory.
    """
    __tablename__ = 'srv_{{APP_SLUG}}_items'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), default='Senza Titolo')
    content = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        }
