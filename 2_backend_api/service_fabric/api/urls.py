from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'templates', views.ServiceTemplateViewSet, basename='template')
router.register(r'services', views.ServiceInstanceViewSet, basename='service')

urlpatterns = [
    path('auth/login/', views.CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('services/generate/', views.trigger_app_generation, name='generate-app'),
    path('', include(router.urls)),
]