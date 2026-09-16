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
            if getattr(prop, 'status', '') in ('sold',):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'This property is already SOLD. You cannot apply for a sold house.'})
            if getattr(prop, 'status', '') in ('verifying',):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'This property is under bank verification (verifying). Please wait until review completes.'})
            # Sophisticated duplicate check - same customer wants to re-apply?
            new_bank = serializer.validated_data.get('bank')
            existing_same = MortgageApplication.objects.filter(customer=user, property=prop, status__in=['pending','document_verification','crb_check','valuation','credit_assessment','approved','disbursed']).first()
            if existing_same:
                from rest_framework.exceptions import ValidationError
                # If trying with same bank -> block, if different bank -> allow only with explicit confirm
                existing_bank_name = existing_same.bank.get_full_name() if existing_same.bank else 'previous bank'
                new_bank_name = new_bank.get_full_name() if new_bank else 'selected bank'
                if existing_same.bank_id and new_bank and existing_same.bank_id == new_bank.id:
                    raise ValidationError({'property': f'You have already applied for this house ({existing_same.application_number} with {existing_bank_name}). Status: {existing_same.status}. Check My Applications or wait for decision. If you want to apply again with same bank, please cancel the previous application first.'})
                # Different bank - need explicit confirmation
                confirm = self.request.data.get('confirm_duplicate') or self.request.data.get('allow_duplicate')
                if str(confirm).lower() not in ('true','1','yes'):
                    raise ValidationError({'property': f'You have already applied for this house ({existing_same.application_number} with {existing_bank_name}). Do you want to apply again with {new_bank_name}? Options: 1) Apply with different bank (add confirm_duplicate=true), 2) Wait for current application ({existing_same.status}), 3) Cancel previous and re-apply. Current request blocked to prevent duplicate.'})
                # If confirm_duplicate=true and different bank, allow through (fall through)
            # Block if another customer already has an active application on this property (different customer)
            taken_other = MortgageApplication.objects.filter(property=prop, status__in=['pending','document_verification','crb_check','valuation','credit_assessment','approved','disbursed']).exclude(customer=user).exists()
            if taken_other:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'property': 'This property is already applied / under bank review by another customer. Please choose another property.'})
        with transaction.atomic():
            # Auto down payment 10% - user does not fill, we calculate
            bank = serializer.validated_data.get('bank')
            loan_amount_val = serializer.validated_data.get('loan_amount')
            if loan_amount_val:
                auto_down = float(loan_amount_val) * 0.10
                serializer.validated_data['down_payment'] = auto_down
                # Also update request data for draft cleanup
                if hasattr(self.request.data, '_mutable'):
                    self.request.data._mutable = True
            if bank and bank.interest_rate:
                annual_interest_rate = float(bank.interest_rate) / 100.0
            else:
                annual_interest_rate = 0.12  # 12% placeholder if no bank
            loan_amount = float(serializer.validated_data.get('loan_amount', 0))
            months = serializer.validated_data.get('repayment_period', 0)

            monthly_installment = calculate_monthly_installment(loan_amount, annual_interest_rate, months)

            # Calculate affordability - gross income for employee, annual for business
            employment_status = serializer.validated_data.get('employment_status')
            if employment_status in ('business_owner','business','self_employed'):
                # Use annual_income if provided, else fallback to monthly_income*12
                annual_inc = serializer.validated_data.get('annual_income')
                if annual_inc:
                    monthly_income = float(annual_inc) / 12.0
                else:
                    monthly_income = float(serializer.validated_data.get('monthly_income', 0))
                    # also set annual for consistency
                    serializer.validated_data['annual_income'] = monthly_income * 12
            else:
                monthly_income = float(serializer.validated_data.get('monthly_income', 0))
            monthly_expenses = float(serializer.validated_data.get('monthly_expenses', 0))

            # --- Statutory deductions (PSSSF 5% public only, HESLB 15%, PAYE 0-30%) ---
            def _calc_paye(inc):
                try:
                    v = float(inc or 0)
                except:
                    return 0
                if v <= 270000:
                    return 0
                elif v <= 520000:
                    return (v - 270000) * 0.08
                elif v <= 760000:
                    return 20000 + (v - 520000) * 0.20
                elif v <= 1000000:
                    return 68000 + (v - 760000) * 0.25
                else:
                    return 128000 + (v - 1000000) * 0.30
            def _truthy(v):
                if v is True or v == 1:
                    return True
                s = str(v).lower().strip() if v is not None else ''
                return s in ('true','1','yes','on','checked')
            employment_sector = serializer.validated_data.get('employment_sector') or self.request.data.get('employment_sector')
            raw_psssf = serializer.validated_data.get('deduction_psssf')
            if raw_psssf is None:
                raw_psssf = self.request.data.get('deduction_psssf') or self.request.data.get('has_psssf') or self.request.data.get('psssf')
            raw_heslb = serializer.validated_data.get('deduction_heslb')
            if raw_heslb is None:
                raw_heslb = self.request.data.get('deduction_heslb') or self.request.data.get('has_heslb') or self.request.data.get('heslb')
            raw_paye = serializer.validated_data.get('deduction_paye')
            if raw_paye is None:
                raw_paye = self.request.data.get('deduction_paye') or self.request.data.get('has_paye') or self.request.data.get('paye')
            want_psssf = _truthy(raw_psssf)
            want_heslb = _truthy(raw_heslb)
            want_paye = _truthy(raw_paye)
            # PSSSF only for employed public sector per spec - ignore for business owners
            if employment_status in ('business_owner','business','self_employed'):
                want_psssf = False
            elif employment_sector and str(employment_sector).lower() != 'public':
                # if private, psssf not applicable - but allow if user explicitly, we still ignore?
                # Spec: 5% ya mshahara NA HII INAFANYA KAZI TU KWA wafanyakazi wa sekta ya umma
                # So force false if private
                if str(employment_sector).lower() == 'private':
                    want_psssf = False
            psssf_amt = float(monthly_income) * 0.05 if want_psssf else 0
            heslb_amt = float(monthly_income) * 0.15 if want_heslb else 0
            paye_amt = _calc_paye(monthly_income) if want_paye else 0
            total_deds = psssf_amt + heslb_amt + paye_amt
            net_income = float(monthly_income) - total_deds
            if net_income < 0:
                net_income = 0
            # Persist computed deductions for bank view
            serializer.validated_data['deduction_psssf'] = want_psssf
            serializer.validated_data['deduction_heslb'] = want_heslb
            serializer.validated_data['deduction_paye'] = want_paye
            if employment_sector:
                serializer.validated_data['employment_sector'] = employment_sector
            serializer.validated_data['psssf_amount'] = round(psssf_amt, 2)
            serializer.validated_data['heslb_amount'] = round(heslb_amt, 2)
            serializer.validated_data['paye_amount'] = round(paye_amt, 2)
            serializer.validated_data['total_deductions'] = round(total_deds, 2)
            serializer.validated_data['net_monthly_income'] = round(net_income, 2)

            # Other loan consolidation: if user has other loan and NOT consolidating, its monthly payment adds to expenses
            has_other = serializer.validated_data.get('has_other_loan') or self.request.data.get('has_other_loan')
            other_bank = serializer.validated_data.get('other_loan_bank') or self.request.data.get('other_loan_bank')
            other_bal = serializer.validated_data.get('other_loan_balance') or self.request.data.get('other_loan_balance')
            other_pay = serializer.validated_data.get('other_loan_monthly_payment') or self.request.data.get('other_loan_monthly_payment') or self.request.data.get('other_loan_repayment') or self.request.data.get('existing_loan_repayment')
            other_consol = serializer.validated_data.get('other_loan_consolidate') or self.request.data.get('other_loan_consolidate')
            # also legacy has_existing_loan mapping
            if not has_other:
                has_other = serializer.validated_data.get('has_existing_loan') or self.request.data.get('has_existing_loan')
            if has_other:
                serializer.validated_data['has_other_loan'] = str(has_other).lower() if str(has_other).lower() in ('yes','no') else ('yes' if _truthy(has_other) else 'no')
                has_other_norm = str(serializer.validated_data['has_other_loan']).lower()
            else:
                has_other_norm = 'no'
            if other_bank and not serializer.validated_data.get('other_loan_bank'):
                serializer.validated_data['other_loan_bank'] = other_bank
            if other_bal and not serializer.validated_data.get('other_loan_balance'):
                try:
                    serializer.validated_data['other_loan_balance'] = float(other_bal)
                except:
                    pass
            if other_pay and not serializer.validated_data.get('other_loan_monthly_payment'):
                try:
                    serializer.validated_data['other_loan_monthly_payment'] = float(other_pay)
                except:
                    pass
            if other_consol:
                serializer.validated_data['other_loan_consolidate'] = str(other_consol).lower() if str(other_consol).lower() in ('yes','no') else ('yes' if _truthy(other_consol) else 'no')
            # Effective income for affordability is net_income; effective expenses includes other loan if not consolidated
            effective_income = net_income if total_deds > 0 else monthly_income
            effective_expenses = monthly_expenses
            other_pay_val = 0
            if has_other_norm == 'yes' and str(serializer.validated_data.get('other_loan_consolidate') or other_consol or 'no').lower() == 'no':
                effective_expenses += other_pay_val
            affordability_score, dti_ratio = calculate_affordability(effective_income, effective_expenses, monthly_installment)
            # If has other loan not consolidated, DTI should include existing repayment too (combined debt)
            if has_other_norm == 'yes' and str(serializer.validated_data.get('other_loan_consolidate') or other_consol or 'no').lower() == 'no' and other_pay_val:
                combined = monthly_installment + other_pay_val
                if effective_income > 0:
                    dti_ratio = (combined / effective_income) * 100

            # DTI threshold: must be ≤40 to apply (≤30 Very Good, 31-40 Good, 41-50 High, >50 Very High)
            if dti_ratio > 40:
                from rest_framework.exceptions import ValidationError
                cat = 'High Risk' if dti_ratio <= 50 else 'Very High Risk'
                raise ValidationError({'dti_ratio': f'DTI {dti_ratio:.1f}% {cat} — haruhusiwi kuomba. Threshold ≤40% to apply (≤30 Very Good, 31-40 Good/Acceptable). Yours {dti_ratio:.1f}%. Reduce loan amount or extend period / increase income.'})

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
            # Marriage certificate file if married
            mfile = self.request.FILES.get('marriage_certificate_file') or self.request.FILES.get('marriage_certificate')
            if mfile:
                if mfile.size > 5242880:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError({'marriage_certificate_file': 'File too large. Maximum 5MB.'})
                mortgage.marriage_certificate_file = mfile
                mortgage.save(update_fields=['marriage_certificate_file'])

    @action(detail=False, methods=['post'], url_path='calculate', permission_classes=[permissions.IsAuthenticated])
    def calculate(self, request):
        """Live AI calculation without saving - for form preview"""
        try:
            loan_amount = float(request.data.get('loan_amount', 0))
            down_payment = float(request.data.get('down_payment', 0))
            repayment_period = int(request.data.get('repayment_period', 0) or 0)
            monthly_income = float(request.data.get('monthly_income', 0))
            annual_income = request.data.get('annual_income')
            monthly_expenses = float(request.data.get('monthly_expenses', 0))
            employment_status = request.data.get('employment_status')
            bank_id = request.data.get('bank') or request.data.get('bank_id')

            # For business owner, convert annual to monthly if monthly not provided
            if employment_status in ('business_owner','business','self_employed') and annual_income and not monthly_income:
                try:
                    monthly_income = float(annual_income) / 12.0
                except:
                    pass

            # --- Deductions handling (same as perform_create) ---
            def _calc_paye(inc):
                try:
                    v = float(inc or 0)
                except:
                    return 0
                if v <= 270000:
                    return 0
                elif v <= 520000:
                    return (v - 270000) * 0.08
                elif v <= 760000:
                    return 20000 + (v - 520000) * 0.20
                elif v <= 1000000:
                    return 68000 + (v - 760000) * 0.25
                else:
                    return 128000 + (v - 1000000) * 0.30
            def _truthy(v):
                if v is True or v == 1:
                    return True
                s = str(v).lower().strip() if v is not None else ''
                return s in ('true','1','yes','on','checked')
            employment_sector = request.data.get('employment_sector')
            raw_psssf = request.data.get('deduction_psssf') if request.data.get('deduction_psssf') is not None else request.data.get('has_psssf')
            raw_heslb = request.data.get('deduction_heslb') if request.data.get('deduction_heslb') is not None else request.data.get('has_heslb')
            raw_paye = request.data.get('deduction_paye') if request.data.get('deduction_paye') is not None else request.data.get('has_paye')
            want_psssf = _truthy(raw_psssf)
            want_heslb = _truthy(raw_heslb)
            want_paye = _truthy(raw_paye)
            if employment_status in ('business_owner','business','self_employed'):
                want_psssf = False
            elif employment_sector and str(employment_sector).lower() == 'private':
                want_psssf = False
            psssf_amt = float(monthly_income) * 0.05 if want_psssf else 0
            heslb_amt = float(monthly_income) * 0.15 if want_heslb else 0
            paye_amt = _calc_paye(monthly_income) if want_paye else 0
            total_deds = psssf_amt + heslb_amt + paye_amt
            net_income = float(monthly_income) - total_deds
            if net_income < 0:
                net_income = 0
            # Other loan
            has_other = request.data.get('has_other_loan') or request.data.get('has_existing_loan')
            other_pay_raw = request.data.get('other_loan_monthly_payment') or request.data.get('existing_loan_repayment') or request.data.get('other_loan_repayment')
            other_consol = request.data.get('other_loan_consolidate')
            has_other_norm = str(has_other).lower() if has_other and str(has_other).lower() in ('yes','no') else ('yes' if _truthy(has_other) else 'no')
            effective_income = net_income if total_deds > 0 else monthly_income
            effective_expenses = monthly_expenses
            other_pay_val = 0
            try:
                other_pay_val = float(other_pay_raw or 0)
            except:
                other_pay_val = 0
            if has_other_norm == 'yes' and str(other_consol or 'no').lower() == 'no':
                effective_expenses += other_pay_val

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
            affordability_score, dti_ratio = calculate_affordability(effective_income, effective_expenses, monthly_installment)
            if has_other_norm == 'yes' and str(other_consol or 'no').lower() == 'no' and other_pay_val:
                combined = monthly_installment + other_pay_val
                if effective_income > 0:
                    dti_ratio = (combined / effective_income) * 100
            risk_score = calculate_risk_score(affordability_score, employment_status)

            # DTI categories: <=30 Very Good, 31-40 Good, 41-50 High, >50 Very High
            if dti_ratio <= 30:
                dti_category = 'Very Good'
            elif dti_ratio <= 40:
                dti_category = 'Good'
            elif dti_ratio <= 50:
                dti_category = 'High Risk'
            else:
                dti_category = 'Very High Risk'
            # Threshold to allow is <=40
            can_apply = dti_ratio <= 40 and affordability_score >= 40 and risk_score <= 80

            # Recommendation - English + Swahili
            if not can_apply or dti_ratio > 40:
                if dti_ratio > 50:
                    recommendation = f"AI Advice: DTI {dti_ratio:.1f}% Very High Risk (>50) — Haruhusiwi kuomba. Reduce loan or increase income."
                elif dti_ratio > 40:
                    recommendation = f"AI Advice: DTI {dti_ratio:.1f}% High Risk (41-50) — Haruhusiwi kuomba. Threshold ≤40%. DTI 31-40 Good, ≤30 Very Good."
                else:
                    recommendation = "AI Advice: Reduce the loan amount or extend the repayment period to improve affordability."
            else:
                recommendation = f"AI Advice: DTI {dti_ratio:.1f}% {dti_category} — You meet the criteria and can proceed. Total payment TZS {monthly_installment*repayment_period:,.0f} @ {annual_rate*100:.2f}%"

            total_payment = monthly_installment * repayment_period
            total_interest = total_payment - loan_amount
            return Response({
                'monthly_installment': round(monthly_installment, 2),
                'total_payment': round(total_payment, 2),
                'total_interest': round(total_interest, 2),
                'affordability_score': round(affordability_score, 2),
                'risk_score': round(risk_score, 2),
                'dti_ratio': round(dti_ratio, 2),
                'dti_category': dti_category,
                'can_apply': can_apply,
                'annual_rate': round(annual_rate*100, 2),
                'bank_name': bank_name,
                'recommendation': recommendation,
                'employment_status': employment_status,
                'deductions': {
                    'gross_income': round(float(monthly_income), 2),
                    'psssf_amount': round(psssf_amt, 2),
                    'heslb_amount': round(heslb_amt, 2),
                    'paye_amount': round(paye_amt, 2),
                    'total_deductions': round(total_deds, 2),
                    'net_income': round(net_income, 2),
                    'want_psssf': want_psssf,
                    'want_heslb': want_heslb,
                    'want_paye': want_paye,
                },
                'effective_income': round(effective_income, 2),
                'effective_expenses': round(effective_expenses, 2),
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
        # Sync property to sold (badge Available -> Sold automatically)
        try:
            if mortgage.property_id:
                prop = mortgage.property
                if prop and prop.status != 'sold':
                    prop.status = 'sold'
                    prop.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass

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
        # If property has no other active applications, revert to available (others can apply)
        try:
            if mortgage.property_id:
                prop = mortgage.property
                if prop:
                    active = MortgageApplication.objects.filter(property=prop).exclude(pk=mortgage.pk).filter(
                        status__in=['pending', 'document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approved', 'disbursed']).exists()
                    if not active and prop.status != 'available':
                        prop.status = 'available'
                        prop.save(update_fields=['status', 'updated_at'])
        except Exception:
            pass
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
            # Try to parse numeric / text fields if present (including new deduction & other loan fields)
            for fld in ['loan_amount', 'down_payment', 'repayment_period', 'monthly_income', 'monthly_expenses',
                        'annual_income', 'business_type', 'business_registration_number',
                        'employment_sector', 'has_other_loan', 'other_loan_bank', 'other_loan_amount', 'other_loan_balance', 'other_loan_monthly_payment', 'other_loan_consolidate',
                        'has_existing_loan', 'existing_loan_bank', 'existing_loan_amount', 'existing_loan_repayment', 'existing_loan_balance',
                        'nida_number', 'dob', 'marital_status', 'marriage_certificate_number']:
                val = data.get(fld)
                if val not in [None, '']:
                    try:
                        # booleans: deduction_* are stored as bool but come as string true/false
                        if fld in ('deduction_psssf','deduction_heslb','deduction_paye'):
                            v = str(val).lower() in ('true','1','yes','on')
                            setattr(draft, fld, v)
                        else:
                            setattr(draft, fld, val)
                    except:
                        pass
            # deduction booleans also may be named differently
            for bfield, keys in [('deduction_psssf',['deduction_psssf','has_psssf','psssf']), ('deduction_heslb',['deduction_heslb','has_heslb','heslb']), ('deduction_paye',['deduction_paye','has_paye','paye'])]:
                for k in keys:
                    if data.get(k) not in [None,'']:
                        try:
                            setattr(draft, bfield, str(data.get(k)).lower() in ('true','1','yes','on','checked'))
                            break
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
            for fld in ['loan_amount', 'down_payment', 'repayment_period', 'monthly_income', 'monthly_expenses',
                        'annual_income', 'business_type', 'business_registration_number',
                        'employment_sector', 'has_other_loan', 'other_loan_bank', 'other_loan_amount', 'other_loan_balance', 'other_loan_monthly_payment', 'other_loan_consolidate',
                        'has_existing_loan', 'existing_loan_bank', 'existing_loan_amount', 'existing_loan_repayment', 'existing_loan_balance',
                        'employment_status', 'nida_number', 'dob', 'marital_status', 'marriage_certificate_number',
                        'deduction_psssf','deduction_heslb','deduction_paye']:
                val = data.get(fld)
                if val not in [None, '']:
                    if fld in ('deduction_psssf','deduction_heslb','deduction_paye'):
                        create_data[fld] = str(val).lower() in ('true','1','yes','on','checked')
                    else:
                        create_data[fld] = val
            # alias keys
            for bfield, keys in [('deduction_psssf',['has_psssf','psssf']), ('deduction_heslb',['has_heslb','heslb']), ('deduction_paye',['has_paye','paye'])]:
                if bfield not in create_data:
                    for k in keys:
                        if data.get(k) not in [None,'']:
                            create_data[bfield] = str(data.get(k)).lower() in ('true','1','yes','on','checked')
                            break
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
