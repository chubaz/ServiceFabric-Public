from app.extensions import db
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy import Column, Integer, String, Boolean, DateTime
import uuid

class ServiceInstance(db.Model):
    """
    Mappatura della tabella 'api_serviceinstance' gestita da Django.
    Flask usa questo modello in modalità 'Read-Only' per configurare il routing e i plugin.
    """
    __tablename__ = 'api_serviceinstance'

    # 1. Mappatura Identica dei Campi
    # Django usa UUID come primary key nel nostro design
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 2. Foreign Key "Logica"
    # In Django il campo è 'owner', nel DB la colonna diventa 'owner_id'.
    # Qui la definiamo come intero (assumendo che Auth User di Django usi ID interi standard).
    owner_id = Column(Integer, nullable=False)

    # 3. Metadati del Servizio
    # service_type corrisponde alla cartella nel Service Catalog (es. 'music_roadshow_v1')
    service_type = Column(String(100), nullable=False)
    
    # url_prefix per il routing (es. '/users/123/roadshow')
    url_prefix = Column(String(255), unique=True, nullable=False)
    
    # 4. Il Cuore della Configurazione Dinamica
    # Mappiamo il JSONField di Django al tipo JSON di Postgres
    state_config = Column(JSON, default=dict)
    
    is_active = Column(Boolean, default=True)
    
    # Non ci interessa mappare created_at/updated_at se Flask non deve usarli,
    # ma è buona norma averli per completezza in lettura.
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return f"<ServiceInstance {self.service_type} ({self.url_prefix})>"

    def to_dict(self):
        """Helper per debugging e API interne"""
        return {
            "id": str(self.id),
            "owner_id": self.owner_id,
            "service_type": self.service_type,
            "url_prefix": self.url_prefix,
            "config": self.state_config,
            "is_free_tier": self.is_free_tier
        }