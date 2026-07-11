from rest_framework import serializers, generics, permissions
from .models import User, ServiceTemplate, ServiceInstance

class UserSerializer(serializers.ModelSerializer):
    """ Serializza solo le informazioni pubbliche dell'utente. """
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']
        # Non esponiamo mai 'password' o 'is_staff'

class ServiceTemplateSerializer(serializers.ModelSerializer):
    """ Serializza il catalogo dei template disponibili. """
    class Meta:
        model = ServiceTemplate
        fields = ['id', 'name', 'template_key', 'description', 'icon']

class ServiceInstanceSerializer(serializers.ModelSerializer):
    """ 
    Serializza un servizio creato dall'utente per il dashboard. 
    Usa 'template_key' per mostrare il nome del template.
    """
    template = serializers.StringRelatedField(source='template.name')
    status = serializers.CharField(source='get_status_display', read_only=True) # Mostra 'Running' invece di 'RUNNING'
    full_service_url = serializers.SerializerMethodField()
    href_url = serializers.SerializerMethodField()

    class Meta:
        model = ServiceInstance
        fields = [
            'id', 'name', 'service_type','is_active','description', 'status', 
            'full_service_url', 'href_url', 'is_public', 'is_hidden', 'created_at', 'template', 'is_free_tier'
        ]
        read_only_fields = ['status', 'created_at']
        
    def get_full_service_url(self, obj):      
        # Nota: obj è l'istanza del ServiceInstance
        prefix = obj.url_prefix if obj.url_prefix.startswith('/') else f"/{obj.url_prefix}"
        return f"http://localhost:8080/app/core{prefix}/"
    
    def get_href_url(self, obj):      
        # Nota: obj è l'istanza del ServiceInstance
        prefix = obj.url_prefix if obj.url_prefix.startswith('/') else f"/{obj.url_prefix}"
        return f"/app/core{prefix}/"
    
class ServiceCreateSerializer(serializers.Serializer):
    """
    Serializzatore per la creazione avanzata di un servizio.
    """
    name = serializers.CharField(max_length=100)
    template_key = serializers.SlugField()
    description = serializers.CharField(required=False, allow_blank=True)
    theme_color = serializers.CharField(max_length=20, default="indigo")

    def validate_template_key(self, value):
        """ Controlla che il template scelto esista nel DB. """
        if not ServiceTemplate.objects.filter(template_key=value).exists():
            raise serializers.ValidationError("Template non valido o non trovato.")
        return value
    