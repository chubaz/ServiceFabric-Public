# api/admin.py

from django.contrib import admin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CloudIntegration, User, ServiceTemplate, ServiceInstance
from .admin_site import admin_site 

# =============================================================
# 1. FORMS PERSONALIZZATI (Rimuovono il campo 'username')
# =============================================================

# Form per la CREAZIONE (Aggiungi Utente)
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        # Usiamo il tuo modello User personalizzato
        model = User
        # L'unico campo necessario per la creazione è l'email (il tuo USERNAME_FIELD)
        # e i campi richiesti da BaseUserManager/PermissionsMixin
        fields = ('email', 'first_name', 'last_name', 'is_staff')
        
    def clean(self):
        cleaned_data = super().clean()
        # Se ci sono errori, stampali nel terminale
        if self.errors:
            print("================ FORM ERRORS ================")
            print(self.errors)
            print("=============================================")
        return cleaned_data

    
# Form per la MODIFICA (Cambia Utente)
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        # Qui elenchiamo tutti i campi disponibili per la modifica
        # BaseUserAdmin cerca 'username' per default, quindi lo escludiamo implicitamente.
        fields = ('email', 'first_name', 'last_name', 
                  'is_active', 'is_staff', 'is_superuser', 
                  'groups', 'user_permissions')

# =============================================================
# 2. ADMIN PERSONALIZZATO (Utilizza i form corretti)
# =============================================================

@admin.register(User, site=admin_site)
class CustomUserAdmin(BaseUserAdmin):
    # Collega le tue custom forms al ModelAdmin
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm # <--- FIX per la pagina ADD
    
    # Campi da visualizzare nella vista di modifica (Change View)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informazioni Personali', {'fields': ('first_name', 'last_name')}),
        ('Dati Tecnici e Permessi', {
            'classes': ('collapse',),
            'fields': (
                ('is_active', 'is_staff', 'is_superuser'),
                'groups', 
                'user_permissions',
            ),
        }),
        ('Dati Storici', {
            'fields': ('date_joined', 'last_login', 'id'),
            'classes': ('collapse',),
        }),
    )

    # Campi da visualizzare nella vista di creazione (Add View)
    # Deve essere un campo separato per la creazione!
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'), # password2 è per la conferma
        }),
        ('Autorizzazioni', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        })
    )

    # Assicurati che i campi di sola lettura siano qui.
    readonly_fields = ('date_joined', 'last_login', 'id')
    list_display = ('email', 'first_name', 'is_staff', 'is_active', 'id')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')
    
    # Rimuovi l'istanza 'admin.site' predefinita se necessario:
    # try:
    #    admin.site.unregister(User)
    # except admin.sites.NotRegistered:
    #    pass
    
@admin.register(ServiceTemplate, site=admin_site)
class ServiceTemplateAdmin(admin.ModelAdmin):
    # 1. Definizione della Lista (Changelist View)
    list_display = ('name', 'template_key', 'description', 'icon')
    list_filter = ('name',)
    search_fields = ('name', 'description', 'template_key')
    ordering = ('name',)

    # 2. Struttura del Modulo di Modifica (Change Form)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'icon'),
            'description': 'Informazioni sul template visualizzate agli utenti.'
        }),
        ('Dati Tecnici (Chiave di Sistema)', {
            # Non collassabile perché la chiave è essenziale e deve essere visualizzata
            'fields': ('template_key',), 
        }),
    )

    # 3. Generazione Automatica della Chiave (Slug)
    # Genera 'template_key' automaticamente dal campo 'name'.
    prepopulated_fields = {'template_key': ('name',)} 

    # 4. Campi di Sola Lettura
    # Nessuno, perché tutti i campi possono essere modificati.
    readonly_fields = ()
    
@admin.register(ServiceInstance, site=admin_site)
class ServiceInstanceAdmin(admin.ModelAdmin):
    # 1. Definizione della Lista (Changelist View)
    list_display = ('name', 'template', 'description', 'service_slug', 'is_public', 'is_hidden', 'created_at', 'service_type', 'status', 'url_prefix', 'state_config', 'is_active', 'is_free_tier')
    list_editable = ('is_free_tier', 'is_active', 'status', 'is_hidden')
    list_filter = ('name','is_free_tier', 'is_hidden')
    search_fields = ('name', 'description', 'template', 'updated_at', 'created_at')
    ordering = ('name',)

    # 2. Struttura del Modulo di Modifica (Change Form)
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'service_slug', 'is_public', 'is_hidden', 'owner', 'service_type', 'status', 'url_prefix', 'state_config', 'is_active', 'is_free_tier'),
            'description': 'Informazioni sull\'instance accessibili dagli utenti.'
        }),
        ('Dati Tecnici (Chiave di Sistema)', {
            # Non collassabile perché la chiave è essenziale e deve essere visualizzata
            'fields': ('template',), 
        }),
    )

    # 3. Generazione Automatica della Chiave (Slug)
    # Genera 'template_key' automaticamente dal campo 'name'.
    # prepopulated_fields = {'template_key': ('name',)} 

    # 4. Campi di Sola Lettura
    # Nessuno, perché tutti i campi possono essere modificati.
    readonly_fields = ()


@admin.register(CloudIntegration, site=admin_site)
class CloudIntegrationAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'credential_binding_id', 'credential_migration_status', 'expires_at', 'last_synced')
    list_filter = ('service', 'credential_migration_status')
    search_fields = ('user__email', 'credential_binding_id')
    readonly_fields = ('credential_binding_id', 'credential_migration_status', 'created_at', 'updated_at')
    fields = ('user', 'service', 'credential_binding_id', 'expires_at', 'scopes', 'last_synced', 'credential_migration_status', 'created_at', 'updated_at')
