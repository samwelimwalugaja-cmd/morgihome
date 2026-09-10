from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MortgageApplicationViewSet

router = DefaultRouter()
router.register(r'mortgages', MortgageApplicationViewSet, basename='mortgage')

urlpatterns = [
    path('', include(router.urls)),
]
