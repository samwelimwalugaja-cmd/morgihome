from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ContractViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
