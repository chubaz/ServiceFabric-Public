# myapp/admin_site.py
from django.contrib.admin import AdminSite

class ServiceFabricAdminSite(AdminSite):
    site_header = "Service Fabric Administration" # [cite: 1114]
    site_title = "Service Fabric Admin" # [cite: 1115]
    index_title = "Dashboard Principale" # [cite: 1121]
    
    # Esempio di metodo per aggiungere contesto per il theaming
    def each_context(self, request):
        context = super().each_context(request)
        # Aggiungi qui le variabili di contesto necessarie per i template custom
        context['theme_color'] = '#44B78B' # Django Primary Green
        context['accent_color'] = '#FFC107' # Amber/Yellow per i link
        return context

# Aggiungere l'istanza alla URLconf (vedi documentazione hook URLconf)
# myproject/urls.py

admin_site = ServiceFabricAdminSite(name='service_fabric_admin') 
# [cite_start]path('admin/', admin_site.urls), # Aggiornare la URLconf con l'istanza [cite: 1178]

