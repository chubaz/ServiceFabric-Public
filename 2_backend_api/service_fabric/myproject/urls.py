from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from api import views as api_views
from api.admin_site import admin_site
urlpatterns = [
    
    path('admin/', admin_site.urls),
    path('api/', include('api.urls')), # Il nostro nuovo file di URL
    
    # Le tue URL di autenticazione SimpleJWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]