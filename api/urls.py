from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from .views import (
    ContractViewSet,
    MortgageViewSet,
    PropertyViewSet,
    TransactionViewSet,
    UserProfileView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="MorgiHome API",
        default_version='v1',
        description="API ya MorgiHome - Mortgage Management System",
        terms_of_service="https://www.morgihome.com/terms/",
        contact=openapi.Contact(email="info@morgihome.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=False,
    permission_classes=[permissions.IsAuthenticated],
)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='api-property')
router.register(r'mortgages', MortgageViewSet, basename='api-mortgage')
router.register(r'contracts', ContractViewSet, basename='api-contract')
router.register(r'transactions', TransactionViewSet, basename='api-transaction')

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('profile/', UserProfileView.as_view(), name='api-profile'),
    path('', include(router.urls)),
]