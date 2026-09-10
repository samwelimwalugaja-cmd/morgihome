from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsEmailVerified, IsFullyVerified, IsIdentityVerified, IsRealEstate, IsSeller
from .models import Property
from .serializers import PropertySerializer


class SellerAddPropertyView(TemplateView):
    template_name = 'seller_add_property.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # TemplateView has no LoginRequiredMixin - JWT is checked by JS requireAuth(), to avoid session redirect even if logged in via JWT
        if self.request.user.is_authenticated:
            ctx['is_seller'] = getattr(self.request.user, 'role', '') in ['seller', 'realestate']
        else:
            ctx['is_seller'] = False
        return ctx


class SellerPropertyListView(TemplateView):
    template_name = 'seller_properties.html'


class SellerBuyersView(TemplateView):
    template_name = 'seller_buyers.html'


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'description']
    ordering_fields = ['price', 'created_at', 'area']

    def get_queryset(self):
        qs = Property.objects.all()
        # ?mine=1 -> properties of logged-in seller/realestate (mobile seller portal)
        if self.request.query_params.get('mine') in ('1', 'true', 'yes'):
            user = self.request.user
            if user.is_authenticated and getattr(user, 'role', '') in ('seller', 'realestate'):
                return qs.filter(seller=user)
            return qs.none()
        seller_id = self.request.query_params.get('seller')
        if seller_id:
            try:
                qs = qs.filter(seller_id=int(seller_id))
            except (ValueError, TypeError):
                pass
        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Listing property still only needs login, badge shows verified/not verified (no blocking)
            permission_classes = [permissions.IsAuthenticated, (IsSeller | IsRealEstate)]
        elif self.action in ['list', 'retrieve', 'search']:
            # As requested: user continues with all activities, badge only shows verified/not verified - no block
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        property_type = request.query_params.get('property_type')

        properties = Property.objects.filter(status='available')

        if query:
            properties = properties.filter(
                Q(title__icontains=query) |
                Q(location__icontains=query) |
                Q(description__icontains=query)
            )

        if min_price:
            properties = properties.filter(price__gte=min_price)
        if max_price:
            properties = properties.filter(price__lte=max_price)
        if property_type:
            properties = properties.filter(property_type=property_type)

        serializer = self.get_serializer(properties, many=True)
        return Response(serializer.data)
