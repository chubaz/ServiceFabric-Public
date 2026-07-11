import uuid
from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from django.utils.text import slugify

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, ListModelMixin
from .models import ServiceTemplate, ServiceInstance
from .serializers import (
    ServiceTemplateSerializer, ServiceInstanceSerializer, ServiceCreateSerializer
)
from core.service_generator import generate_service_app

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView


# Importiamo la logica di creazione che definiremo in T5
from core.service_generator import start_service_creation_task 

class ServiceTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API (sola lettura) per elencare i template disponibili.
    (Fase 4 del T2, per popolare il menu a tendina)
    """
    queryset = ServiceTemplate.objects.all()
    serializer_class = ServiceTemplateSerializer
    permission_classes = [permissions.AllowAny] # Disponibile a tutti per popolamento UI

class ServiceInstanceViewSet(
    RetrieveModelMixin, 
    UpdateModelMixin, 
    DestroyModelMixin, 
    ListModelMixin,
    viewsets.GenericViewSet # Importante: non eredita 'create()'
):
    """
    API per gestire le istanze dei servizi (le "card" del dashboard).
    Permette:
    - GET (list): Popola il dashboard (Fase 3 del T2)
    - GET (retrieve): Dettagli di un servizio (per il polling dello stato)
    - POST (create): NON USATO (usiamo un'azione custom)
    - PUT/PATCH: Per aggiornare nome, descrizione, o 'is_public'
    - DELETE: Per distruggere un servizio
    """
    serializer_class = ServiceInstanceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Logic:
        - Anonymous User -> Sees ONLY is_free_tier=True services
        - Logged User -> Sees their own services AND is_free_tier=True services
        - Filtering: Excludes hidden services unless 'include_hidden=true' is provided.
        """
        user = self.request.user
        include_hidden = self.request.query_params.get('include_hidden', 'false').lower() == 'true'
        
        # Base filter for visibility
        if user.is_authenticated:
            # Combine owned services OR free services
            queryset = ServiceInstance.objects.filter(
                Q(owner=user) | Q(is_free_tier=True)
            )
        else:
            # Only free services for anonymous
            queryset = ServiceInstance.objects.filter(is_free_tier=True)

        if not include_hidden:
            queryset = queryset.filter(is_hidden=False)

        return queryset.select_related('template')
    
    @action(detail=False, methods=['post'], serializer_class=ServiceCreateSerializer)
    def create_service(self, request):
        """
        Endpoint custom per la CREAZIONE (Fase 4 del T2).
        URL: /api/services/create_service/
        """
        serializer = ServiceCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        validated_data = serializer.validated_data
        template = ServiceTemplate.objects.get(template_key=validated_data['template_key'])
        user = request.user
        
        # Genera uno slug pulito dal nome (es. "Il mio Progetto" -> "il-mio-progetto")
        app_slug = slugify(validated_data['name'])
        
        # --- LOGICA "FACTORY" (Generazione Fisica) ---
        try:
            # Chiamata al generatore di file
            new_app_files = generate_service_app(
                template_key=template.template_key,
                new_app_name=validated_data['name'],
                new_app_slug=app_slug,
                user=user
            )
        except Exception as e:
            return Response({"error": f"Errore durante la generazione fisica: {str(e)}"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                                               
        # --- LOGICA "STATE PROVISIONER" ---
        # 1. Inizializza lo stato con i default del template e le preferenze utente
        state_config = template.default_state_config.copy()
        state_config['theme_color'] = validated_data.get('theme_color', 'indigo')
        
        # 2. Crea l'istanza per il dashboard (T3)
        generated_prefix = f"/{app_slug}"
        
        service_instance = ServiceInstance.objects.create(
            owner=user,
            template=template,
            service_type=app_slug, # --- ALLINEATO ALLO SLUG ---
            url_prefix=generated_prefix,
            service_slug=app_slug, # --- ALLINEATO ALLO SLUG ---
            name=validated_data['name'],
            description=validated_data.get('description', ''),
            state_config=state_config,
            status=ServiceInstance.ServiceStatus.RUNNING 
        )
        
        # 3. Rispondiamo con l'istanza creata
        response_serializer = ServiceInstanceSerializer(service_instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    
    def perform_destroy(self, instance):
        """
        Sovrascritto per gestire la cancellazione (DELETE /api/services/{id}/).
        
        MIGLIORAMENTO: È istantaneo. Non ci sono container (T1)
        o file (T1) da pulire.
        """
        # Semplicemente cancelliamo l'oggetto (T3).
        instance.delete()
        
        # Non c'è più bisogno di schedulare task T9.
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CookieTokenObtainPairView(TokenObtainPairView):
    """
    View di Login custom: oltre a restituire il JSON, setta il cookie HttpOnly.
    Questo permette al browser di autenticarsi automaticamente verso Flask.
    """
    def post(self, request, *args, **kwargs):
        # 1. Esegui la logica standard di login (verifica credenziali)
        response = super().post(request, *args, **kwargs)
        
        # 2. Se il login è ok, estrai il token
        if response.status_code == 200:
            access_token = response.data.get('access')
            
            # 3. Imposta il Cookie CONDIVISO
            # httponly=True: Il JS non può leggerlo (Protezione XSS totale)
            # samesite='Lax': Protegge da CSRF base
            # path='/': Fondamentale! Rende il cookie visibile su tutto il dominio (anche a Nginx/Flask)
            response.set_cookie(
                'sf_access_token',  # Nome del cookie
                access_token,
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True, 
                samesite='Lax',
                path='/', 
                secure=False # Metti True in produzione (HTTPS)
            )
            
        return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_app_generation(request):
    """
    Endpoint per avviare il T5 (Fabbrica App).
    Riceve il template_key e il nome desiderato per la nuova app.
    """
    template_key = request.data.get('template_key')
    app_name = request.data.get('app_name')

    if not template_key or not app_name:
        return Response({"error": "template_key e app_name sono obbligatori."}, status=status.HTTP_400_BAD_REQUEST)

    # Genera uno slug pulito dal nome (es. "Il mio Progetto" -> "il-mio-progetto")
    app_slug = slugify(app_name)

    try:
        # Avvia la creazione fisica
        new_app = generate_service_app(
            template_key=template_key,
            new_app_name=app_name,
            new_app_slug=app_slug,
            user=request.user
        )
        
        return Response({
            "status": "success",
            "message": f"App '{new_app.name}' generata con successo!",
            "app_slug": new_app.app_slug,
            "app_id": new_app.id
        }, status=status.HTTP_201_CREATED)
        
    except FileExistsError as e:
        return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
    except FileNotFoundError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": f"Errore di sistema: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)