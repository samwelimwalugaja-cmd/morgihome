from datetime import date

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import IsBank, IsCustomer, IsSeller
from .models import Contract, Transaction
from .serializers import ContractSerializer, TransactionSerializer


class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.action in ['create']:
            # Contract created by Admin (is_staff) or Bank
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['execute']:
            # Executed by Admin
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['sign']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Contract.objects.all()
        elif user.role == 'customer':
            return Contract.objects.filter(customer=user)
        elif user.role == 'seller':
            return Contract.objects.filter(seller=user)
        elif user.role == 'bank':
            return Contract.objects.filter(bank=user)
        return Contract.objects.none()

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        contract = self.get_object()
        user = request.user

        if contract.status not in ['draft', 'pending_signature']:
            return Response({'error': 'Contract cannot be signed'}, status=status.HTTP_400_BAD_REQUEST)

        if user.role == 'customer':
            contract.customer_signed = True
        elif user.role == 'seller':
            contract.seller_signed = True
        elif user.role == 'bank':
            contract.bank_signed = True
        elif user.is_staff or user.is_superuser:
            # Admin signing not needed, execution via execute endpoint
            return Response({'error': 'Admin does not sign, use execute'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        contract.status = 'pending_signature'

        if contract.is_fully_signed():
            contract.status = 'signed'
            contract.signed_date = date.today()

        contract.save()
        return Response({'status': contract.status, 'message': 'Signed successfully'})

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        contract = self.get_object()
        user = request.user
        # Only Admin or Bank can execute
        if not (user.is_staff or user.is_superuser or user.role == 'bank'):
            return Response({'error': 'Only Admin or Bank can execute contracts'}, status=status.HTTP_403_FORBIDDEN)

        if contract.status != 'signed':
            return Response({'error': 'Contract must be signed first'}, status=status.HTTP_400_BAD_REQUEST)

        contract.status = 'executed'
        contract.executed_date = date.today()
        contract.save()

        # Update mortgage status
        mortgage = contract.mortgage
        mortgage.status = 'disbursed'
        mortgage.save()

        return Response({'status': 'executed', 'message': 'Contract executed successfully'})


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == 'bank':
            return Transaction.objects.all()
        elif user.role == 'customer':
            return Transaction.objects.filter(contract__customer=user)
        elif user.role == 'seller':
            return Transaction.objects.filter(contract__seller=user)
        return Transaction.objects.none()

    def perform_create(self, serializer):
        # Generate reference number automatically
        serializer.save()
