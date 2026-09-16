from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils import timezone

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
    queryset = Property.objects.filter(is_deleted=False)
    serializer_class = PropertySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'description']
    ordering_fields = ['price', 'created_at', 'area']

    def get_queryset(self):
        qs = Property.objects.filter(is_deleted=False)
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
        # Include search query on list
        return qs

    def get_object(self):
        obj = super().get_object()
        if obj.is_deleted:
            raise NotFound("Property not found or deleted.")
        return obj

    def _check_delete_blocked(self, instance):
        """Block if any customer has active mortgage application or mortgage already taken."""
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        # 1) Tayari imechukuliwa mkopo? - mortgage approved/disbursed au contract exists au status sold/rented
        if instance.status in ('sold', 'rented'):
            raise PermissionDenied("Cannot delete this property - it has already been sold/completed (status: %s)." % instance.get_status_display())
        if Contract.objects.filter(mortgage__property=instance).exists():
            raise PermissionDenied("Cannot delete this property - it already has an active mortgage contract.")
        active_qs = MortgageApplication.objects.filter(property=instance).exclude(status__in=('draft', 'rejected'))
        if active_qs.filter(status__in=('approved', 'disbursed')).exists():
            raise PermissionDenied("Cannot delete this property - it already has an approved/disbursed mortgage.")
        if active_qs.exists():
            first = active_qs.select_related('customer').first()
            name = ""
            try:
                name = (first.customer.get_full_name() or first.customer.email) if first and first.customer else ""
            except Exception:
                name = ""
            status_lbl = first.get_status_display() if first else ""
            if name:
                raise PermissionDenied(f"Cannot delete this property - customer {name} has already started a mortgage application for this house (status: {status_lbl}). Deletion is not allowed while there are ongoing applications.")
            raise PermissionDenied(f"Cannot delete this property - a customer has already started a mortgage application (status: {status_lbl}).")

    def perform_destroy(self, instance):
        # Owner-only soft delete
        user = self.request.user
        if instance.seller_id != getattr(user, 'id', None):
            raise PermissionDenied("You can only delete your own property.")

        self._check_delete_blocked(instance)
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Permission check: owner only
        if instance.seller_id != getattr(request.user, 'id', None):
            raise PermissionDenied("You can only delete your own property.")
        self._check_delete_blocked(instance)
        self.perform_destroy(instance)
        return Response(status=204)

    def perform_update(self, serializer):
        instance = serializer.instance
        if instance and instance.is_deleted:
            raise NotFound("Property not found or deleted.")
        if instance and instance.seller_id != getattr(self.request.user, 'id', None):
            raise PermissionDenied("You can only edit your own property.")
        serializer.save()

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

        properties = Property.objects.filter(status='available', is_deleted=False)

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
