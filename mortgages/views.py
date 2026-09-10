from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.views.generic import TemplateView
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import IsBank, IsCustomer
from .ai_utils import calculate_affordability, calculate_monthly_installment, calculate_risk_score, generate_repayment_schedule
from .models import ApplicationCorrection, ApplicationTimelineEvent, MortgageApplication, MortgageDocument, RepaymentSchedule, REVIEW_STAGE_MESSAGES
from .serializers import CorrectionSerializer, MortgageApplicationSerializer, RepaymentScheduleSerializer, TimelineEventSerializer


class MortgageApplicationViewSet(viewsets.ModelViewSet):
    queryset = MortgageApplication.objects.all()
    serializer_class = MortgageApplicationSerializer
    throttle_classes = [UserRateThrottle]

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [permissions.IsAuthenticated, IsCustomer]
            # Fully verified check handled in perform_create for detailed error
        elif self.action in ['approve', 'reject', 'advance_stage', 'request_correction']:
            permission_classes = [permissions.IsAuthenticated, IsBank]
        elif self.action in ['respond_correction']:
            permission_classes = [permissions.IsAuthenticated, IsCustomer]
        elif self.action in ['calculate']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        # Allow draft retrieval/deletion for resume/delete; list still excludes drafts
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            if user.role == 'customer':
                return MortgageApplication.objects.filter(customer=user)
            elif user.role in ['bank', 'realestate']:
                return MortgageApplication.objects.all()
            elif user.role == 'seller':
                return MortgageApplication.objects.filter(property__seller=user)
        # Drafts are not shown in the normal list - they have their own endpoint (/draft) so they don't duplicate pending
        if user.role == 'customer':
            qs = MortgageApplication.objects.filter(customer=user).exclude(status='draft')
            return qs
        elif user.role in ['bank', 'realestate']:
            return MortgageApplication.objects.all().exclude(status='draft')
        elif user.role == 'seller':
            return MortgageApplication.objects.filter(property__seller=user).exclude(status='draft')
        return MortgageApplication.objects.none()

    def perform_create(self, serializer):
        # As requested: don't block apply because of verification - badge only shows verified/not verified
        # Bank/realestate/lawyer will see badge on application
        user = self.request.user
        # Prevent duplicate pending for one property - one property one active application
        prop = serializer.validated_data.get('property')
        if prop:
            # Refresh status from DB (avoid stale object)
            try:
                prop.refresh_from_db()
            except Exception:
                pass
            if getattr(prop, 'status', '') in ('sold', 'verifying'):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'This property is no longer available (sold / under bank review).'})
            # Block if another customer already has an active application on this property
            taken = MortgageApplication.objects.filter(property=prop, status__in=['pending','document_verification','crb_check','valuation','credit_assessment','approved','disbursed']).exists()
            if taken:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'This property is already applied / under bank review.'})
            exists = MortgageApplication.objects.filter(customer=user, property=prop, status__in=['pending','document_verification','crb_check','valuation','credit_assessment','approved','disbursed']).exists()
            if exists:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'You have already applied for this property. Check My Applications.'})
        with transaction.atomic():
            # Calculate monthly installment - use bank interest if selected (Steps 6-7)
            bank = serializer.validated_data.get('bank')
            if bank and bank.interest_rate:
                annual_interest_rate = float(bank.interest_rate) / 100.0
            else:
                annual_interest_rate = 0.12  # 12% placeholder if no bank
            loan_amount = float(serializer.validated_data.get('loan_amount', 0))
            months = serializer.validated_data.get('repayment_period', 0)

            monthly_installment = calculate_monthly_installment(loan_amount, annual_interest_rate, months)

            # Calculate affordability
            monthly_income = float(serializer.validated_data.get('monthly_income', 0))
            monthly_expenses = float(serializer.validated_data.get('monthly_expenses', 0))
            affordability_score, dti_ratio = calculate_affordability(monthly_income, monthly_expenses, monthly_installment)

            # Calculate risk score
            employment_status = serializer.validated_data.get('employment_status')
            risk_score = calculate_risk_score(affordability_score, employment_status)

            # Save
            # Set loan_type / mortgage_type / current_step if provided
            extra = {}
            if serializer.validated_data.get('loan_type'):
                extra['loan_type'] = serializer.validated_data.get('loan_type')
            elif self.request.data.get('loan_type'):
                extra['loan_type'] = self.request.data.get('loan_type')
            if self.request.data.get('mortgage_type'):
                extra['mortgage_type'] = self.request.data.get('mortgage_type')
            elif self.request.data.get('type'):
                extra['mortgage_type'] = self.request.data.get('type')
            extra['current_step'] = 8
            extra['status'] = 'pending'
            extra['review_stage'] = 'received'
            mortgage = serializer.save(
                customer=self.request.user,
                monthly_installment=monthly_installment,
                affordability_score=affordability_score,
                risk_score=risk_score,
                dti_ratio=dti_ratio,
                **extra
            )
            # Delete the draft(s) this submission completes. A submitted
            # application is complete, so its draft must disappear - drafts
            # remain ONLY for genuinely unfinished flows.
            # Covers: same-type draft saved before a property was chosen
            # (property NULL), same property picked under another type, and
            # the exact row the form was autosaving (draft_id/resume id).
            # Drafts of other types AND other properties are untouched.
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
                incoming_id = self.request.data.get('draft_id') or self.request.data.get('resume_draft_id')
                if incoming_id:
                    try:
                        cond |= Q(id=int(incoming_id))
                    except (ValueError, TypeError):
                        pass
                if cond:
                    base.filter(cond).delete()
            except:
                pass
            # Direct routing to selected bank + live timeline for customer
            try:
                bank_name = mortgage.bank.get_full_name() if mortgage.bank else 'the selected bank'
                ApplicationTimelineEvent.log(
                    mortgage, 'received',
                    title='Sent to bank',
                    message=f"Your application {mortgage.application_number} has been sent directly to {bank_name}. The bank has received all your details and review is starting.",
                    user=user,
                )
            except Exception:
                pass
            # Persistent bank notification (stored - never vanishes)
            try:
                from .models import BankNotification
                BankNotification.notify(
                    mortgage.bank, 'New Application Received',
                    f"{mortgage.customer.get_full_name()} submitted {mortgage.application_number} for TZS {float(mortgage.loan_amount or 0):,.0f}",
                    link=f"/bank/applications/{mortgage.id}/")
            except Exception:
                pass
            # Property becomes Applied (others see badge, cannot take it)
            try:
                if mortgage.property_id and getattr(mortgage.property, 'status', '') == 'available':
                    mortgage.property.status = 'applied'
                    mortgage.property.save(update_fields=['status', 'updated_at'])
            except Exception:
                pass
            # Handle multiple documents upload
            files = self.request.FILES.getlist('documents')
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            for f in files:
                if f.size > 5242880:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'documents': f'File {f.name} too large. Maximum size is 5MB.'})
                if f.content_type not in allowed_types and not f.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'documents': f'Invalid file type for {f.name}. Only JPG, PNG, PDF allowed.'})
                MortgageDocument.objects.create(mortgage=mortgage, file=f)

    @action(detail=False, methods=['post'], url_path='calculate', permission_classes=[permissions.IsAuthenticated])
    def calculate(self, request):
        """Live AI calculation without saving - for form preview"""
        try:
            loan_amount = float(request.data.get('loan_amount', 0))
            down_payment = float(request.data.get('down_payment', 0))
            repayment_period = int(request.data.get('repayment_period', 0) or 0)
            monthly_income = float(request.data.get('monthly_income', 0))
            monthly_expenses = float(request.data.get('monthly_expenses', 0))
            employment_status = request.data.get('employment_status')
            bank_id = request.data.get('bank') or request.data.get('bank_id')

            if not loan_amount or not repayment_period or not monthly_income:
                return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

            annual_rate = 0.12
            bank_name = None
            if bank_id:
                try:
                    from accounts.models import User
                    bk = User.objects.filter(id=bank_id, role='bank').first()
                    if bk and bk.interest_rate:
                        annual_rate = float(bk.interest_rate) / 100.0
                        bank_name = bk.get_full_name()
                except:
                    pass
            monthly_installment = calculate_monthly_installment(loan_amount, annual_rate, repayment_period)
            affordability_score, dti_ratio = calculate_affordability(monthly_income, monthly_expenses, monthly_installment)
            risk_score = calculate_risk_score(affordability_score, employment_status)

            # Recommendation - English
            if affordability_score < 80 or risk_score > 70 or dti_ratio > 40:
                recommendation = "AI Advice: Reduce the loan amount or extend the repayment period to improve affordability."
            else:
                recommendation = "AI Advice: You meet the criteria and can proceed with the application."

            return Response({
                'monthly_installment': round(monthly_installment, 2),
                'affordability_score': round(affordability_score, 2),
                'risk_score': round(risk_score, 2),
                'dti_ratio': round(dti_ratio, 2),
                'annual_rate': round(annual_rate*100, 2),
                'bank_name': bank_name,
                'recommendation': recommendation,
                'employment_status': employment_status,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Live step-by-step history - customer sees every bank confirmation."""
        mortgage = self.get_object()
        events = mortgage.timeline_events.order_by('created_at')
        return Response({
            'application_id': mortgage.id,
            'application_number': mortgage.application_number,
            'status': mortgage.status,
            'review_stage': mortgage.review_stage,
            'review_message': REVIEW_STAGE_MESSAGES.get(mortgage.review_stage, '') if mortgage.status not in ('approved', 'rejected', 'disbursed') else REVIEW_STAGE_MESSAGES.get(mortgage.status, ''),
            'bank_name': mortgage.bank.get_full_name() if mortgage.bank else None,
            'events': TimelineEventSerializer(events, many=True).data,
            'corrections': CorrectionSerializer(mortgage.corrections.order_by('-created_at'), many=True).data,
        })

    @action(detail=True, methods=['post'])
    def request_correction(self, request, pk=None):
        """Bank sends a correction request (re-upload unclear deed, type NIDA...).
        Customer sees it with instructions + input field and is notified."""
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
        """Customer answers a correction request (text and/or file)."""
        from django.utils import timezone
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
            from .models import BankNotification
            BankNotification.notify(
                mortgage.bank, 'Correction Submitted',
                f"{request.user.get_full_name()} answered your correction request on {mortgage.application_number} ({corr.target or corr.kind}).",
                link=f"/bank/applications/{mortgage.id}/review/", icon='file-text', color='emerald')
        except Exception:
            pass
        return Response(CorrectionSerializer(corr).data)

    @action(detail=True, methods=['post'])
    def advance_stage(self, request, pk=None):
        """Bank confirms one review step: document_verification / crb_check / valuation / credit_assessment / approval_decision.
        Customer instantly sees e.g. 'Bank is now at CRB verification stage'."""
        mortgage = self.get_object()
        # Bank can only advance its own applications
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
        # Map stage -> application status (approval_decision keeps pending until final approve/reject)
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
        return Response({
            'status': mortgage.status,
            'review_stage': mortgage.review_stage,
            'review_message': msg,
            'message': 'Stage updated. Customer can now see this step live.',
        })

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        mortgage = self.get_object()
        if mortgage.status in ('approved', 'disbursed'):
            return Response({'error': 'Application already approved'}, status=status.HTTP_400_BAD_REQUEST)

        mortgage.status = 'approved'
        mortgage.review_stage = 'approval_decision'
        mortgage.save(update_fields=['status', 'review_stage', 'updated_at'])
        ApplicationTimelineEvent.log(mortgage, 'approved', user=request.user)

        # Generate repayment schedule
        schedules, monthly_installment = generate_repayment_schedule(mortgage)
        for schedule in schedules:
            RepaymentSchedule.objects.create(
                mortgage=mortgage,
                installment_number=schedule['installment_number'],
                due_date=request.data.get('due_date') or '2025-01-01',  # Placeholder
                amount_due=schedule['amount_due'],
                balance_remaining=schedule['balance_remaining']
            )

        return Response({'status': 'approved', 'message': 'Mortgage approved successfully'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        mortgage = self.get_object()
        if mortgage.status == 'approved' or mortgage.status == 'disbursed':
            return Response({'error': 'Cannot reject approved or disbursed application'}, status=status.HTTP_400_BAD_REQUEST)

        mortgage.status = 'rejected'
        mortgage.review_stage = 'approval_decision'
        reason = request.data.get('reason') or request.data.get('notes') or ''
        if reason:
            mortgage.review_note = reason
        mortgage.save()
        ApplicationTimelineEvent.log(
            mortgage, 'rejected',
            message=f"The bank has finished review — this application was rejected. Reason: {reason}" if reason else REVIEW_STAGE_MESSAGES.get('rejected', ''),
            user=request.user,
        )
        return Response({'status': 'rejected', 'message': 'Mortgage rejected'})

    @action(detail=False, methods=['get', 'post', 'patch'], url_path='draft')
    def draft(self, request):
        """Save / resume draft - isolated per (mortgage_type + property). Auto-continue without asking."""
        user = request.user
        if request.method == 'GET':
            drafts = MortgageApplication.objects.filter(customer=user, status='draft').order_by('-updated_at')
            # Filter by mortgage_type / property if sent - so land vs residential don't mix
            mtype = request.query_params.get('mortgage_type') or request.query_params.get('type')
            prop = request.query_params.get('property')
            if mtype:
                drafts = drafts.filter(mortgage_type=mtype)
            if prop:
                try:
                    drafts = drafts.filter(property_id=int(prop))
                except:
                    pass
            serializer = MortgageApplicationSerializer(drafts, many=True)
            return Response(serializer.data)
        # POST / PATCH - save draft
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # Allow FormData or JSON
        loan_type = data.get('loan_type') or data.get('mortgage_type') or data.get('type')
        mortgage_type = data.get('mortgage_type') or data.get('type')
        current_step = data.get('current_step')
        try:
            current_step = int(current_step) if current_step else 1
        except:
            current_step = 1
        draft_data = {}
        # Collect all form fields into draft_data
        for k, v in list(data.items()):
            if k not in ['loan_type', 'mortgage_type', 'type', 'current_step', 'csrfmiddlewaretoken', 'draft_id', 'id', 'resume_draft_id']:
                draft_data[k] = v
        # Also store files names if any
        if hasattr(request, 'FILES') and request.FILES:
            draft_data['_files'] = list(request.FILES.keys())
        # 1) If frontend sent draft_id (idempotent saves) - update that row directly.
        # This is duplicate protection when beforeunload/visibilitychange/click send POST in parallel.
        prop_id_for_lookup = data.get('property')
        draft = None
        incoming_id = data.get('draft_id') or data.get('id') or data.get('resume_draft_id')
        if incoming_id:
            try:
                draft = MortgageApplication.objects.filter(customer=user, status='draft', id=int(incoming_id)).first()
            except (ValueError, TypeError):
                draft = None
        # 2) Find existing draft strictly isolated per (mortgage_type + property) - ili residential na land zisiingiliane
        if draft is None and mortgage_type:
            try:
                pid = int(prop_id_for_lookup) if prop_id_for_lookup not in [None, ''] else None
            except:
                pid = None
            if pid:
                draft = MortgageApplication.objects.filter(customer=user, status='draft', mortgage_type=mortgage_type, property_id=pid).first()
                if not draft:
                    # fallback: draft of that type without property (user hasn't chosen property yet)
                    draft = MortgageApplication.objects.filter(customer=user, status='draft', mortgage_type=mortgage_type, property__isnull=True).first()
            else:
                draft = MortgageApplication.objects.filter(customer=user, status='draft', mortgage_type=mortgage_type).first()
                # if draft has a different property than current (and property not yet set), leave as is - don't mix with other types
                if draft and pid is None and draft.property_id and prop_id_for_lookup:
                    # property mismatch - create new instead of reusing
                    try:
                        if int(draft.property_id) != int(prop_id_for_lookup):
                            draft = None
                    except:
                        pass
        elif draft is None:
            # no mortgage_type - use generic draft
            draft = MortgageApplication.objects.filter(customer=user, status='draft').order_by('-updated_at').first()
        if draft:
            # Update existing draft
            if loan_type:
                draft.loan_type = loan_type
            if mortgage_type:
                draft.mortgage_type = mortgage_type
            draft.current_step = current_step
            draft.draft_data = draft_data
            # Update optional fk fields if provided
            prop_id = data.get('property')
            if prop_id:
                try:
                    from properties.models import Property
                    draft.property = Property.objects.get(id=prop_id)
                except:
                    pass
            bank_id = data.get('bank')
            if bank_id:
                try:
                    from accounts.models import User
                    bk = User.objects.filter(id=bank_id, role='bank').first()
                    if bk:
                        draft.bank = bk
                except:
                    pass
            # Try to parse numeric fields if present
            for fld in ['loan_amount', 'down_payment', 'repayment_period', 'monthly_income', 'monthly_expenses']:
                val = data.get(fld)
                if val not in [None, '']:
                    try:
                        setattr(draft, fld, val)
                    except:
                        pass
            emp = data.get('employment_status')
            if emp:
                draft.employment_status = emp
            draft.save()
            self._dedupe_drafts(user, draft)
            serializer = MortgageApplicationSerializer(draft)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new draft
            create_data = {
                'status': 'draft',
                'current_step': current_step,
                'draft_data': draft_data,
            }
            if loan_type:
                create_data['loan_type'] = loan_type
            if mortgage_type:
                create_data['mortgage_type'] = mortgage_type
            prop_id = data.get('property')
            if prop_id:
                try:
                    from properties.models import Property
                    create_data['property'] = Property.objects.get(id=prop_id)
                except:
                    pass
            bank_id = data.get('bank')
            if bank_id:
                try:
                    from accounts.models import User
                    bk = User.objects.filter(id=bank_id, role='bank').first()
                    if bk:
                        create_data['bank'] = bk
                except:
                    pass
            for fld in ['loan_amount', 'down_payment', 'repayment_period', 'monthly_income', 'monthly_expenses', 'employment_status']:
                val = data.get(fld)
                if val not in [None, '']:
                    create_data[fld] = val
            draft = MortgageApplication.objects.create(customer=user, **create_data)
            self._dedupe_drafts(user, draft)
            serializer = MortgageApplicationSerializer(draft)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _dedupe_drafts(user, keep):
        """Delete sibling drafts (duplicates) of this user - same mortgage_type + same property.
        This is the final protection against duplicates from parallel autosaves
        (beforeunload + visibilitychange + click sending POST at the same time).
        Drafts of other types (land vs residential) are untouched."""
        try:
            from .models import MortgageApplication as MA
            qs = MA.objects.filter(customer=user, status='draft', mortgage_type=keep.mortgage_type).exclude(id=keep.id)
            if keep.property_id:
                qs = qs.filter(property_id=keep.property_id)
            else:
                qs = qs.filter(property__isnull=True)
            qs.delete()
        except Exception:
            pass

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


class CustomerApplyView(TemplateView):
    template_name = 'mortgage_application_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # TemplateView without LoginRequiredMixin - JWT is checked by JS, to avoid session redirect
        if self.request.user.is_authenticated:
            context['is_customer'] = getattr(self.request.user, 'role', '') == 'customer'
        else:
            context['is_customer'] = False
        return context
