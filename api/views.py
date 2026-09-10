from datetime import date

from django.db.models import Q
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.models import User
from accounts.permissions import IsBank, IsCustomer, IsRealEstate, IsSeller
from mortgages.models import MortgageApplication, RepaymentSchedule
from properties.models import Property
from transactions.models import Contract, Transaction

from .serializers import (
    ContractDetailSerializer,
    ContractListSerializer,
    MortgageApplicationDetailSerializer,
    MortgageApplicationListSerializer,
    PropertyDetailSerializer,
    PropertyListSerializer,
    RepaymentScheduleSerializer,
    TransactionSerializer,
    UserProfileSerializer,
    UserSerializer,
)

# ----- USER VIEWS -----
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ----- PROPERTY VIEWS -----
class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    permission_classes = [permissions.AllowAny]
    throttle_classes = [UserRateThrottle]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'location', 'description']
    ordering_fields = ['price', 'created_at', 'area']

    def get_queryset(self):
        qs = Property.objects.all()
        # ?mine=1 -> properties of logged-in seller (mobile seller portal)
        if self.request.query_params.get('mine') in ('1', 'true', 'yes'):
            user = self.request.user
            if user.is_authenticated and getattr(user, 'role', '') in ('seller', 'realestate'):
                return qs.filter(seller=user)
            return qs.none()
        # ?seller=<id> -> properties of a specific seller (public)
        seller_id = self.request.query_params.get('seller')
        if seller_id:
            try:
                qs = qs.filter(seller_id=int(seller_id))
            except (ValueError, TypeError):
                pass
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        return PropertyDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'gallery', 'set_cover']:
            # NOTE: `|` works on CLASSES, not instances - (IsSeller() | IsRealEstate()) raises TypeError
            return [permissions.IsAuthenticated(), (IsSeller | IsRealEstate)()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=['post'], url_path='gallery')
    def gallery(self, request, pk=None):
        """Upload gallery images (mobile seller) - multipart field 'images' (max 5 per request, 5MB each)."""
        prop = self.get_object()
        if prop.seller != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'You can only add photos to your own properties.'}, status=status.HTTP_403_FORBIDDEN)
        from properties.models import PropertyImage
        files = request.FILES.getlist('images')
        if not files:
            return Response({'error': 'No images provided. Use multipart field "images".'}, status=status.HTTP_400_BAD_REQUEST)
        if len(files) > 5:
            return Response({'error': 'Maximum 5 images per upload.'}, status=status.HTTP_400_BAD_REQUEST)
        created = []
        existing = prop.gallery.count()
        for idx, f in enumerate(files):
            if f.size > 5242880:
                return Response({'error': f'File {f.name} too large. Maximum 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
            if f.content_type not in ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'] and not f.name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                return Response({'error': f'Invalid file type for {f.name}. Only JPG, PNG, WEBP allowed.'}, status=status.HTTP_400_BAD_REQUEST)
            is_cover = (existing == 0 and idx == 0 and not prop.gallery.filter(is_cover=True).exists())
            g = PropertyImage.objects.create(property=prop, image=f, is_cover=is_cover, order=existing + idx)
            if is_cover and not prop.image:
                prop.image = f
                prop.save(update_fields=['image'])
            created.append({'id': g.id, 'image': g.image.url if g.image else None, 'is_cover': g.is_cover})
        return Response({'uploaded': len(created), 'images': created}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='set-cover')
    def set_cover(self, request, pk=None):
        """Set cover image: body {image_id} (gallery) - mobile seller."""
        prop = self.get_object()
        if prop.seller != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'You can only edit your own properties.'}, status=status.HTTP_403_FORBIDDEN)
        from properties.models import PropertyImage
        try:
            image_id = int(request.data.get('image_id'))
        except (ValueError, TypeError):
            return Response({'error': 'image_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            g = prop.gallery.get(id=image_id)
        except PropertyImage.DoesNotExist:
            return Response({'error': 'Image not found for this property.'}, status=status.HTTP_404_NOT_FOUND)
        g.is_cover = True
        g.save()  # model.save() removes covers of others
        prop.image = g.image
        prop.save(update_fields=['image'])
        return Response({'message': 'Cover updated.', 'cover_image_url': prop.cover_image_url})

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


# ----- MORTGAGE VIEWS -----
class MortgageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return MortgageApplication.objects.filter(customer=user)
        elif user.role in ['bank', 'realestate']:
            return MortgageApplication.objects.all()
        elif user.role == 'seller':
            return MortgageApplication.objects.filter(property__seller=user)
        return MortgageApplication.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return MortgageApplicationListSerializer
        return MortgageApplicationDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsCustomer()]
        elif self.action in ['approve', 'reject', 'advance_stage', 'request_correction']:
            return [permissions.IsAuthenticated(), IsBank()]
        elif self.action in ['respond_correction']:
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # AI features are calculated in the model (use ai_utils from phase 4) - use bank rate if available
        from mortgages.ai_utils import calculate_affordability, calculate_monthly_installment, calculate_risk_score

        bank = serializer.validated_data.get('bank')
        if bank and bank.interest_rate:
            annual_interest_rate = float(bank.interest_rate) / 100.0
        else:
            annual_interest_rate = 0.12
        loan_amount = float(serializer.validated_data.get('loan_amount', 0))
        months = serializer.validated_data.get('repayment_period', 0)

        monthly_installment = calculate_monthly_installment(loan_amount, annual_interest_rate, months)

        monthly_income = float(serializer.validated_data.get('monthly_income', 0))
        monthly_expenses = float(serializer.validated_data.get('monthly_expenses', 0))
        affordability_score, dti_ratio = calculate_affordability(monthly_income, monthly_expenses, monthly_installment)

        employment_status = serializer.validated_data.get('employment_status')
        risk_score = calculate_risk_score(affordability_score, employment_status)

        mortgage = serializer.save(
            customer=self.request.user,
            monthly_installment=monthly_installment,
            affordability_score=affordability_score,
            risk_score=risk_score,
            dti_ratio=dti_ratio,
            review_stage='received',
        )
        # Submitted = complete: remove its draft(s) so no draft lingers.
        # Drafts remain ONLY for genuinely unfinished flows (other types/properties untouched).
        try:
            from django.db.models import Q
            base = MortgageApplication.objects.filter(
                customer=self.request.user, status='draft').exclude(id=mortgage.id)
            cond = Q()
            if mortgage.mortgage_type:
                cond |= Q(mortgage_type=mortgage.mortgage_type) & (
                    Q(property__isnull=True) | Q(property_id=mortgage.property_id))
            if mortgage.property_id:
                cond |= Q(property_id=mortgage.property_id)
            if cond:
                base.filter(cond).delete()
        except Exception:
            pass
        # Direct routing: log receipt so customer + bank see it instantly
        try:
            from mortgages.models import ApplicationTimelineEvent
            bank_name = mortgage.bank.get_full_name() if mortgage.bank else 'the selected bank'
            ApplicationTimelineEvent.log(
                mortgage, 'received',
                title='Sent to bank',
                message=f"Your application {mortgage.application_number} has been sent directly to {bank_name}. The bank has received all your details and review is starting.",
                user=self.request.user,
            )
        except Exception:
            pass
        try:
            from mortgages.models import BankNotification
            BankNotification.notify(
                mortgage.bank, 'New Application Received',
                f"{mortgage.customer.get_full_name()} submitted {mortgage.application_number} for TZS {float(mortgage.loan_amount or 0):,.0f}",
                link=f"/bank/applications/{mortgage.id}/")
        except Exception:
            pass

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        from mortgages.models import REVIEW_STAGE_MESSAGES
        from mortgages.serializers import CorrectionSerializer, TimelineEventSerializer
        mortgage = self.get_object()
        events = mortgage.timeline_events.order_by('created_at')
        if mortgage.status in ('approved', 'rejected', 'disbursed'):
            msg = REVIEW_STAGE_MESSAGES.get(mortgage.status, '')
        else:
            msg = REVIEW_STAGE_MESSAGES.get(mortgage.review_stage, '')
        return Response({
            'application_id': mortgage.id,
            'application_number': mortgage.application_number,
            'status': mortgage.status,
            'review_stage': mortgage.review_stage,
            'review_message': msg,
            'bank_name': mortgage.bank.get_full_name() if mortgage.bank else None,
            'events': TimelineEventSerializer(events, many=True).data,
            'corrections': CorrectionSerializer(mortgage.corrections.order_by('-created_at'), many=True).data,
        })

    @action(detail=True, methods=['post'])
    def request_correction(self, request, pk=None):
        from mortgages.models import ApplicationCorrection, ApplicationTimelineEvent
        from mortgages.serializers import CorrectionSerializer
        mortgage = self.get_object()
        if request.user.role == 'bank' and mortgage.bank_id and mortgage.bank_id != request.user.id:
            return Response({'error': 'This application was sent to a different bank.'}, status=status.HTTP_403_FORBIDDEN)
        kind = request.data.get('kind', 'document')
        if kind not in ('document', 'nida', 'info', 'other'):
            kind = 'document'
        target = (request.data.get('target') or '')[:200]
        instructions = (request.data.get('instructions') or '').strip()
        if not instructions:
            return Response({'error': 'Instructions are required.'}, status=status.HTTP_400_BAD_REQUEST)
        corr = ApplicationCorrection.objects.create(
            application=mortgage, kind=kind, target=target,
            instructions=instructions, created_by=request.user)
        ApplicationTimelineEvent.log(
            mortgage, 'note', title='Correction requested',
            message=f"Bank requested a correction on {mortgage.application_number} ({target or kind}): {instructions[:200]}. Open your application to respond.",
            user=request.user)
        return Response(CorrectionSerializer(corr).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def respond_correction(self, request, pk=None):
        from django.utils import timezone
        from mortgages.models import ApplicationCorrection, ApplicationTimelineEvent
        from mortgages.serializers import CorrectionSerializer
        mortgage = self.get_object()
        cid = request.data.get('correction_id')
        try:
            corr = ApplicationCorrection.objects.get(id=cid, application=mortgage, status='pending')
        except (ApplicationCorrection.DoesNotExist, ValueError, TypeError):
            return Response({'error': 'Correction request not found.'}, status=status.HTTP_404_NOT_FOUND)
        corr.response_text = (request.data.get('response_text') or '')[:2000]
        f = request.FILES.get('response_file')
        if f:
            if f.size > 5242880:
                return Response({'error': 'File too large. Maximum 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
            corr.response_file = f
        if not corr.response_text and not corr.response_file:
            return Response({'error': 'Write an answer or attach a file.'}, status=status.HTTP_400_BAD_REQUEST)
        corr.status = 'resolved'
        corr.resolved_at = timezone.now()
        corr.save()
        ApplicationTimelineEvent.log(
            mortgage, 'note', title='Correction submitted',
            message=f"You answered the bank's correction request on {mortgage.application_number} ({corr.target or corr.kind}). The bank will continue review.",
            user=request.user)
        try:
            from mortgages.models import BankNotification
            BankNotification.notify(
                mortgage.bank, 'Correction Submitted',
                f"{request.user.get_full_name()} answered your correction request on {mortgage.application_number} ({corr.target or corr.kind}).",
                link=f"/bank/applications/{mortgage.id}/review/", icon='file-text', color='emerald')
        except Exception:
            pass
        return Response(CorrectionSerializer(corr).data)

    @action(detail=True, methods=['post'])
    def advance_stage(self, request, pk=None):
        from mortgages.models import ApplicationTimelineEvent, REVIEW_STAGE_MESSAGES
        mortgage = self.get_object()
        if request.user.role == 'bank' and mortgage.bank_id and mortgage.bank_id != request.user.id:
            return Response({'error': 'This application was sent to a different bank.'}, status=status.HTTP_403_FORBIDDEN)
        stage = (request.data.get('stage') or '').strip()
        note = (request.data.get('note') or '').strip()
        valid = ['document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approval_decision']
        if stage not in valid:
            return Response({'error': f"Invalid stage. Use one of: {', '.join(valid)}"}, status=status.HTTP_400_BAD_REQUEST)
        if (mortgage.review_stage or '') == stage and not note:
            return Response({'status': mortgage.status, 'review_stage': mortgage.review_stage,
                             'review_message': 'Already at this stage. Nothing changed.'})
        status_map = {
            'document_verification': 'document_verification',
            'crb_check': 'crb_check',
            'valuation': 'valuation',
            'credit_assessment': 'credit_assessment',
            'approval_decision': 'credit_assessment',
        }
        mortgage.review_stage = stage
        mortgage.status = status_map.get(stage, mortgage.status)
        if note:
            mortgage.review_note = note
        mortgage.save(update_fields=['review_stage', 'status', 'review_note', 'updated_at'])
        msg = REVIEW_STAGE_MESSAGES.get(stage, stage)
        if note:
            msg = f"{msg} — Bank note: {note}"
        ApplicationTimelineEvent.log(mortgage, stage, message=msg, user=request.user)
        return Response({'status': mortgage.status, 'review_stage': mortgage.review_stage, 'review_message': msg})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        mortgage = self.get_object()
        if mortgage.status in ('approved', 'disbursed'):
            return Response({'error': 'Application already approved'}, status=status.HTTP_400_BAD_REQUEST)

        mortgage.status = 'approved'
        mortgage.review_stage = 'approval_decision'
        mortgage.save(update_fields=['status', 'review_stage', 'updated_at'])
        try:
            from mortgages.models import ApplicationTimelineEvent
            ApplicationTimelineEvent.log(mortgage, 'approved', user=request.user)
        except Exception:
            pass

        # Generate repayment schedule
        from mortgages.ai_utils import generate_repayment_schedule
        schedules, monthly_installment = generate_repayment_schedule(mortgage)
        for schedule in schedules:
            RepaymentSchedule.objects.create(
                mortgage=mortgage,
                installment_number=schedule['installment_number'],
                due_date=request.data.get('due_date') or '2025-01-01',
                amount_due=schedule['amount_due'],
                balance_remaining=schedule['balance_remaining']
            )

        return Response({'status': 'approved', 'message': 'Mortgage approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        mortgage = self.get_object()
        if mortgage.status in ['approved', 'disbursed']:
            return Response({'error': 'Cannot reject approved or disbursed application'}, status=status.HTTP_400_BAD_REQUEST)

        mortgage.status = 'rejected'
        mortgage.review_stage = 'approval_decision'
        reason = request.data.get('reason') or ''
        if reason:
            mortgage.review_note = reason
        mortgage.save()
        try:
            from mortgages.models import ApplicationTimelineEvent, REVIEW_STAGE_MESSAGES
            msg = f"The bank has finished review — this application was rejected. Reason: {reason}" if reason else REVIEW_STAGE_MESSAGES.get('rejected', '')
            ApplicationTimelineEvent.log(mortgage, 'rejected', message=msg, user=request.user)
        except Exception:
            pass
        return Response({'status': 'rejected', 'message': 'Mortgage rejected'})

    @action(detail=True, methods=['get'])
    def repayment_schedule(self, request, pk=None):
        mortgage = self.get_object()
        schedules = RepaymentSchedule.objects.filter(mortgage=mortgage).order_by('installment_number')
        serializer = RepaymentScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def affordability(self, request, pk=None):
        mortgage = self.get_object()
        return Response({
            'affordability_score': mortgage.affordability_score,
            'risk_score': mortgage.risk_score,
            'dti_ratio': mortgage.dti_ratio,
            'monthly_installment': mortgage.monthly_installment,
            'status': mortgage.status
        })


# ----- CONTRACT VIEWS -----
class ContractViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

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

    def get_serializer_class(self):
        if self.action == 'list':
            return ContractListSerializer
        return ContractDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'execute']:
            return [permissions.IsAuthenticated()]
        elif self.action == 'sign':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

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
        if not (user.is_staff or user.is_superuser or user.role == 'bank'):
            return Response({'error': 'Only Admin or Bank can execute contracts'}, status=status.HTTP_403_FORBIDDEN)
        if contract.status != 'signed':
            return Response({'error': 'Contract must be signed first'}, status=status.HTTP_400_BAD_REQUEST)

        contract.status = 'executed'
        contract.executed_date = date.today()
        contract.save()

        mortgage = contract.mortgage
        mortgage.status = 'disbursed'
        mortgage.save()

        return Response({'status': 'executed', 'message': 'Contract executed successfully'})


# ----- TRANSACTION VIEWS -----
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser or user.role == 'bank':
            return Transaction.objects.all()
        elif user.role == 'customer':
            return Transaction.objects.filter(contract__customer=user)
        elif user.role == 'seller':
            return Transaction.objects.filter(contract__seller=user)
        return Transaction.objects.none()

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        import uuid
        if not serializer.validated_data.get('reference_number'):
            serializer.save(reference_number=f"TRX-{uuid.uuid4().hex[:12].upper()}")
        else:
            serializer.save()
