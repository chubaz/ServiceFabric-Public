from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modello utente personalizzato che usa l'email come username.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    is_staff = models.BooleanField(default=False) # Accesso all'admin Django
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    

class ServiceTemplate(models.Model):
    """
    Rappresenta un "prototipo" o "boilerplate" disponibile 
    nella cartella 3_service_templates/.
    """
    name = models.CharField(max_length=100) # Es. "Flask + React Prototyper"
    template_key = models.SlugField(max_length=50, unique=True) # Es. "flask_react_base"
    description = models.TextField(blank=True) # Spiegazione per l'utente
    icon = models.CharField(max_length=50, blank=True)
    
    # --- NUOVO CAMPO FONDAMENTALE ---
    # Definisce lo "stato" di default per una nuova istanza (T3)
    default_state_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="La configurazione JSON di default per le nuove istanze."
    )
    def __str__(self):
        return self.name
    
    
class ServiceInstance(models.Model):
    """
    Rappresenta un'istanza di un servizio generato, 
    appartenente a un utente.
    """
    class ServiceStatus(models.TextChoices):
        RUNNING = 'RUNNING', 'Running'         # Attivo (badge verde)
        STOPPED = 'STOPPED', 'Stopped'         # Fermato (badge rosso)
        ERROR = 'ERROR', 'Error'             # Errore (badge rosso)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # --- Relazioni Fondamentali ---
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="service_instances"
    )
    
    template = models.ForeignKey(
        ServiceTemplate, 
        on_delete=models.PROTECT, 
        related_name="instances",
        blank=True,
        null=True
    )
    
    service_type = models.CharField(max_length=100, help_text="Nome della cartella del Blueprint nel catalogo", null=True, blank=True)
    
    url_prefix = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # --- Informazioni Utente ---
    name = models.CharField(max_length=100) # Es. "My Data App"
    description = models.TextField(blank=True)
    
    # --- Informazioni Tecniche (per il T5: Generatore) ---
    
    state_config = models.JSONField(
        default=dict,
        blank=True,
    )
    
    status = models.CharField(
        max_length=20, 
        choices=ServiceStatus.choices, 
        default=ServiceStatus.RUNNING
    )
    
    # Data Validation poiché accedono al network.
    service_slug = models.SlugField(max_length=100, unique=True, blank=True, null=True) # Es. "my-data-app"

    
    # --- Nuova Funzionalità "Socialize" ---
    is_public = models.BooleanField(
        default=False, 
        help_text="Se vero, questo servizio può apparire nel blog pubblico."
    )
    
    is_hidden = models.BooleanField(
        default=False, 
        help_text="Se vero, l'istanza viene nascosta dalla dashboard pur rimanendo attiva e di proprietà dell'utente."
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    is_free_tier = models.BooleanField(
        default=False, 
        help_text="If checked, this service is available to public visitors without login."
    )
    class Meta:
        db_table = 'api_serviceinstance'
        verbose_name = 'Service Instance'
        verbose_name_plural = 'Service Instances'
        indexes = [
            models.Index(fields=['url_prefix']),
            models.Index(fields=['owner', 'service_type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
       
    
class Post(models.Model):
    """
    Rappresenta un singolo post del blog creato da un utente
    per "socializzare" il risultato di un servizio.
    """
    class PostStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Bozza'
        PUBLISHED = 'PUBLISHED', 'Pubblicato'

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Collega al nostro User (T3)
        on_delete=models.CASCADE,
        related_name="blog_posts"
    )
    
    # --- Il gancio "Socialize" ---
    # Collega opzionalmente questo post a uno specifico servizio
    # del dashboard dell'utente.
    service_linked = models.ForeignKey(
        ServiceInstance, # Collega al ServiceInstance (T3)
        on_delete=models.SET_NULL, # Se il servizio è cancellato, il post resta
        null=True, blank=True,
        related_name="blog_posts"
    )
    
    content = models.TextField() # Il corpo del post
    status = models.CharField(
        max_length=10, 
        choices=PostStatus.choices, 
        default=PostStatus.DRAFT
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Comment(models.Model):
    """
    Permette agli utenti (T3) di commentare i Post (T6).
    """
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE, 
        related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="comments"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Commento di {self.author.email} su {self.post.title}"

class Conversation(models.Model):
    """
    Rappresenta una singola "stanza" di chat o un thread di messaggi.
    Collega due o più utenti (T3).
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
        verbose_name="Partecipanti"
    )
    # Potremmo aggiungere un 'subject' se vogliamo una "mailbox"
    # subject = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversazione tra {self.participants.count()} utenti"

class Message(models.Model):
    """
    Rappresenta un singolo messaggio inviato da un utente (T3)
    all'interno di una conversazione (T7).
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Manteniamo il messaggio anche se l'utente è cancellato
        null=True,
        related_name="sent_messages"
    )
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Campo "read" (TBD): per le spunte di lettura, avremmo
    # bisogno di un ManyToManyField a User (read_by)

    class Meta:
        ordering = ['timestamp'] # I messaggi sono sempre ordinati

    def __str__(self):
        return f"Messaggio da {self.sender} in {self.conversation.id}"
    
class CloudIntegration(models.Model):
    """
    Memorizza (in modo sicuro) le credenziali OAuth2 per un singolo 
    servizio cloud (es. Google Drive) per un singolo utente (T3).
    """
    class ServiceChoices(models.TextChoices):
        GOOGLE_DRIVE = 'GDRIVE', 'Google Drive'
        DROPBOX = 'DROPBOX', 'Dropbox'
        # ...altri futuri servizi

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="cloud_integrations"
    )
    service = models.CharField(
        max_length=20, 
        choices=ServiceChoices.choices
    )
    
    # --- CREDENZIALI CRITTOGRAFATE ---
    # NON salvare mai i token in chiaro.
    # Usiamo campi crittografati (richiede 'django-pgcrypto' o simili)
    # Per semplicità, qui usiamo TextField, ma in T10 (Sicurezza)
    # implementeremo la crittografia.
    
    access_token = models.TextField() # Idealmente EncryptedTextField
    refresh_token = models.TextField() # Idealmente EncryptedTextField
    expires_at = models.DateTimeField()
    
    last_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Un utente può avere solo un'integrazione per servizio
        unique_together = ('user', 'service')

    def __str__(self):
        return f"{self.user.email} - {self.get_service_display()}"
    
class ServiceApp(models.Model):
    """
    Rappresenta un'applicazione generata fisicamente nel catalogo.
    """
    name = models.CharField(max_length=100)
    app_slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    template_source = models.ForeignKey(ServiceTemplate, on_delete=models.SET_NULL, null=True)
    owners = models.ManyToManyField(User, related_name="owned_apps")
    
    default_state_config = models.JSONField(default=dict, blank=True)
    default_app_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserActivityLog(models.Model):
    """
    Traccia eventi significativi dell'utente per l'analisi e l'audit.
    NON traccia ogni click.
    """
    class EventType(models.TextChoices):
        # Autenticazione (T4)
        USER_LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'User Logged In'
        USER_LOGIN_FAILURE = 'LOGIN_FAILURE', 'User Login Failed'
        # Servizi (T5/T3)
        SERVICE_CREATED = 'SVC_CREATED', 'Service Created'
        SERVICE_DELETED = 'SVC_DELETED', 'Service Deleted'
        SERVICE_STATE_UPDATED = 'SVC_STATE_UPDATED', 'Service State Updated'
        # Blog (T6)
        POST_CREATED = 'POST_CREATED', 'Blog Post Created'
        # Cloud (T8)
        CLOUD_INTEGRATION_ADDED = 'CLOUD_INT_ADDED', 'Cloud Integration Added'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Manteniamo i log anche se l'utente è cancellato
        null=True, blank=True
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Usiamo JSONField per metadati flessibili
    # Es. per 'SVC_CREATED', potremmo salvare: {'service_id': 123, 'template': 'flask_react_base'}
    metadata = models.JSONField(default=dict, null=True, blank=True)
    
    # Campo opzionale per l'indirizzo IP (per audit di sicurezza)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "User Activity Log"