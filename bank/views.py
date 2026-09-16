"""
MorgiHome - Bank Views
All views use Shadcn Admin template (bank_base.html)
Mock data - replace with real queries from Application, Contract, Repayment models

!! IMPORTANT - BANK SECURITY REMOVED !!
- Bank does NOT require verification (is_verified) - can access all sections
- Verification remains only for USER (customer) and SELLER -> see accounts/decorators.py
- No @login_required or @verified_required for Bank intentionally
"""
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt


REVIEW_STEP_ORDER = ['received', 'document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approval_decision']
# "Pending decision" = everything the bank has not decided yet. Confirming a
# review stage moves the status forward but the application is still pending
# until it is approved/rejected/disbursed - it must NOT drop out of Pending.
PENDING_STATUSES = ['pending', 'document_verification', 'crb_check', 'valuation', 'credit_assessment']
REVIEW_STEP_LABELS = {
    'received': 'Received — all customer details delivered to bank',
    'document_verification': 'Document Verification — ID, payslip, bank statement',
    'crb_check': 'CRB Check — Credit Reference Bureau history',
    'valuation': 'Property Valuation',
    'credit_assessment': 'Credit Assessment — income & affordability',
    'approval_decision': 'Final Approval Decision',
}

# Short toast messages per action (user asked: alert iwe fupi, inahusiana na button)
STAGE_SUCCESS_MESSAGES = {
    'received': 'Application received successfully.',
    'document_verification': 'Documents verified successfully.',
    'crb_check': 'CRB info approved successfully.',
    'valuation': 'Valuation confirmed successfully.',
    'credit_assessment': 'Credit assessment completed successfully.',
    'approval_decision': 'Moved to final decision successfully.',
}


def _sync_property_status(app):
    """Keep Property badge in sync with loan progress:
    - approved/disbursed -> sold (house taken, others cannot apply)
    - any verify stage (document_verification/crb/valuation/credit) -> verifying
    - rejected -> back to available if no other active application on same property
    - pending/received with application -> applied
    """
    try:
        prop = getattr(app, 'property', None)
        if prop is None:
            return
        from mortgages.models import MortgageApplication as MA
        status = getattr(app, 'status', '')
        if status in ('approved', 'disbursed'):
            if prop.status != 'sold':
                prop.status = 'sold'
                prop.save(update_fields=['status', 'updated_at'])
            return
        if status in ('document_verification', 'crb_check', 'valuation', 'credit_assessment'):
            if prop.status not in ('sold',):
                prop.status = 'verifying'
                prop.save(update_fields=['status', 'updated_at'])
            return
        if status == 'rejected':
            # revert only if no other active application remains on this property
            active = MA.objects.filter(property=prop).exclude(pk=app.pk).filter(
                status__in=['pending', 'document_verification', 'crb_check',
                            'valuation', 'credit_assessment', 'approved', 'disbursed']).exists()
            if not active and prop.status != 'available':
                prop.status = 'available'
                prop.save(update_fields=['status', 'updated_at'])
            return
        # pending / received -> applied (house taken, waiting bank)
        if status in ('pending',):
            if prop.status == 'available':
                prop.status = 'applied'
                prop.save(update_fields=['status', 'updated_at'])
    except Exception:
        pass


def _bank_user(request):
    """Return user if logged-in bank, otherwise None (view all data).
    Supports both session (request.user) and JWT Bearer token (localStorage)."""
    u = getattr(request, 'user', None)
    if u is not None and getattr(u, 'is_authenticated', False) and getattr(u, 'role', '') == 'bank':
        return u
    # Try JWT Bearer token from Authorization header (for users logged in via localStorage)
    try:
        auth = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION') or ''
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1].strip()
            # Try DRF JWT authentication
            try:
                from rest_framework_simplejwt.authentication import JWTAuthentication
                # Create a mock request with header for JWT auth
                validated = JWTAuthentication().authenticate(request)
                if validated:
                    user, _ = validated
                    if getattr(user, 'role', '') == 'bank':
                        return user
            except Exception:
                pass
            # Fallback: decode token directly
            try:
                from rest_framework_simplejwt.tokens import AccessToken
                tok = AccessToken(token)
                user_id = tok.get('user_id')
                from accounts.models import User
                user = User.objects.filter(id=user_id, role='bank').first()
                if user and getattr(user, 'role', '') == 'bank':
                    return user
            except Exception:
                pass
    except Exception:
        pass
    return None


def _risk_label(score):
    try:
        s = float(score or 0)
    except (TypeError, ValueError):
        s = 0
    if s < 40:
        return 'Low'
    if s > 70:
        return 'High'
    return 'Medium'


def _app_dict(app):
    cust = getattr(app, 'customer', None)
    name = cust.get_full_name() if cust else '-'
    try:
        photo = cust.profile_image.url if cust and cust.profile_image else ''
    except Exception:
        photo = ''
    try:
        ref = app.application_number
    except Exception:
        ref = f"APP-{app.id}"
    return {
        "id": app.id,
        "ref": ref,
        "customer": name,
        "initials": (getattr(cust, 'initials', '') or (name[:1] if name else '-')) if cust else '-',
        "photo": photo,
        "phone": getattr(cust, 'phone_number', '') if cust else '',
        "amount": float(app.loan_amount or 0),
        "type": app.get_mortgage_type_display() if getattr(app, 'mortgage_type', None) else 'House',
        "term": app.repayment_period or 0,
        "income": float(app.monthly_income or 0),
        "score": int(app.affordability_score or 0),
        "ai_risk": _risk_label(getattr(app, 'risk_score', 0)),
        "ai_percent": int(app.affordability_score or 0),
        "status": app.status,
        "date": app.created_at.strftime('%Y-%m-%d') if getattr(app, 'created_at', None) else '',
        "link": f"/bank/applications/{app.id}/",
    }


def _scoped_apps(request):
    """Applications of logged-in bank (bank=user); guests see all."""
    from mortgages.models import MortgageApplication
    qs = MortgageApplication.objects.exclude(status='draft').select_related('customer', 'property', 'bank')
    bu = _bank_user(request)
    if bu is not None:
        qs = qs.filter(bank=bu)
    return qs


def _scoped_contracts(request):
    from transactions.models import Contract
    qs = Contract.objects.select_related('mortgage__property', 'customer', 'bank')
    bu = _bank_user(request)
    if bu is not None:
        qs = qs.filter(bank=bu)
    return qs


def _month_buckets(n=6):
    """Last n months (label + year + month), oldest first."""
    from datetime import date
    today = timezone.now().date()
    out = []
    y, m = today.year, today.month
    for _ in range(n):
        out.append({'label': date(y, m, 1).strftime('%b'), 'year': y, 'month': m})
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def bank_dashboard(request):
    """
    GET /bank/dashboard/ - REAL DATA from DB (no mock).
    If logged in as bank, you see only your bank's data.
    """
    from transactions.models import Contract
    from django.db.models import Sum
    qs = _scoped_apps(request)
    total = qs.count()
    pending = qs.filter(status__in=PENDING_STATUSES).count()
    approved = qs.filter(status='approved').count()
    cqs = _scoped_contracts(request)
    disbursed = cqs.filter(status='executed').count()
    disbursed_amount = cqs.filter(status='executed').aggregate(total=Sum('mortgage__loan_amount'))['total'] or 0
    low = qs.filter(risk_score__lt=40).count()
    medium = qs.filter(risk_score__gte=40, risk_score__lt=70).count()
    high = qs.filter(risk_score__gte=70).count()
    ai_summary = {"low": low, "medium": medium, "high": high,
                  "low_pct": round(low / total * 100) if total else 0,
                  "medium_pct": round(medium / total * 100) if total else 0,
                  "high_pct": round(high / total * 100) if total else 0}
    months = _month_buckets(6)
    chart_labels, chart_apps, chart_appr = [], [], []
    for b in months:
        chart_labels.append(b['label'])
        mqs = qs.filter(created_at__year=b['year'], created_at__month=b['month'])
        chart_apps.append(mqs.count())
        chart_appr.append(mqs.filter(status__in=['approved', 'disbursed']).count())
    recent = [_app_dict(a) for a in qs.order_by('-created_at')[:5]]
    bu = _bank_user(request)
    context = {
        "today": timezone.now().strftime("%d %b %Y"),
        "stats": {"total": total, "pending": pending, "approved": approved, "disbursed": disbursed, "disbursed_amount": disbursed_amount},
        "approval_rate": round(approved / total * 100, 1) if total else 0,
        "chart_labels": chart_labels,
        "chart_applications": chart_apps,
        "chart_approved": chart_appr,
        "ai_summary": ai_summary,
        "recent_applications": recent,
        "bank_name": bu.get_full_name() if bu else "Bank",
    }
    return render(request, "bank/bank_dashboard.html", context)


def bank_applications(request):
    """
    GET /bank/applications/ - REAL DATA from DB (no mock).
    """
    from django.db.models import Q
    status_filter = request.GET.get("status", "")
    risk_filter = request.GET.get("risk", "")
    search_q = request.GET.get("q", "")
    qs = _scoped_apps(request).order_by('-created_at')
    total_all = qs.count()
    pending_count = qs.filter(status__in=PENDING_STATUSES).count()
    if status_filter == 'pending':
        # Pending = all undecided applications (fresh + every review stage).
        qs = qs.filter(status__in=PENDING_STATUSES)
    elif status_filter:
        qs = qs.filter(status=status_filter)
    if risk_filter == 'low':
        qs = qs.filter(risk_score__lt=40)
    elif risk_filter == 'medium':
        qs = qs.filter(risk_score__gte=40, risk_score__lt=70)
    elif risk_filter == 'high':
        qs = qs.filter(risk_score__gte=70)
    if search_q:
        qs = qs.filter(Q(customer__email__icontains=search_q) | Q(customer__first_name__icontains=search_q) | Q(customer__last_name__icontains=search_q) | Q(property__title__icontains=search_q))
        try:
            qs = qs | _scoped_apps(request).filter(id=int(search_q))
        except (ValueError, TypeError):
            pass
    apps = [_app_dict(app) for app in qs[:50]]
    # Risk breakdown for header when filtered
    risk_info = ''
    if risk_filter == 'low':
        risk_info = 'Low Risk — DTI ≤30 Very Good, Afford ≥80, Risk <40'
    elif risk_filter == 'medium':
        risk_info = 'Medium Risk — DTI 31-40 Good/Acceptable, Risk 40-70'
    elif risk_filter == 'high':
        risk_info = 'High Risk — DTI 41-50 High, >50 Very High, Risk ≥70'
    context = {"applications": apps, "status_filter": status_filter, "risk_filter": risk_filter, "risk_info": risk_info, "search_q": search_q,
               "total_count": qs.count(), "total_all": total_all, "pending_count": pending_count}
    return render(request, "bank/bank_applications.html", context)


def _filtered_applications(request, preset_status):
    """Helper: list filtered by All/Pending/Approved/Rejected (sidebar dropdown)."""
    from django.http import QueryDict
    q = request.GET.copy()
    if preset_status == "all":
        q.pop("status", None)
    elif preset_status:
        q["status"] = preset_status
    request.GET = q
    return bank_applications(request)


def bank_applications_all(request):
    """GET /bank/applications/all/"""
    return _filtered_applications(request, "all")


def bank_applications_pending(request):
    """GET /bank/applications/pending/"""
    return _filtered_applications(request, "pending")


def bank_applications_approved(request):
    """GET /bank/applications/approved/"""
    return _filtered_applications(request, "approved")


def bank_applications_rejected(request):
    """GET /bank/applications/rejected/"""
    return _filtered_applications(request, "rejected")


def _correction_dicts(app):
    """Corrections with the customer's response file URL (bank must see what was re-sent)."""
    out = []
    for co in app.corrections.order_by('-created_at'):
        try:
            resp_url = co.response_file.url if co.response_file else ''
        except Exception:
            resp_url = ''
        out.append({
            "id": co.id,
            "kind": co.kind,
            "kind_display": co.get_kind_display(),
            "target": co.target,
            "instructions": co.instructions,
            "status": co.status,
            "response_text": co.response_text or '',
            "response_file_url": resp_url,
            "created_at": co.created_at,
            "resolved_at": co.resolved_at,
        })
    return out


def _advance_application(app, stage, user=None, note='', next_stage=''):
    """Bank confirms one step. Updates status + review_stage and logs timeline so customer sees it live.
    After confirming `stage`, review_stage advances to `next_stage` (or next in REVIEW_STEP_ORDER)
    so returning to the app shows stage 2, not stage 1 again.
    """
    from mortgages.models import ApplicationTimelineEvent, REVIEW_STAGE_MESSAGES
    status_map = {
        'document_verification': 'document_verification',
        'crb_check': 'crb_check',
        'valuation': 'valuation',
        'credit_assessment': 'credit_assessment',
        'approval_decision': 'credit_assessment',
        'received': 'pending',
    }
    # Status for the stage just confirmed (customer sees "Bank is now at X" for next, not this)
    # We first set to stage's status, then advance to next_stage for DB.
    app.review_stage = stage
    if stage in status_map:
        app.status = status_map[stage]
    if note:
        app.review_note = note
    # Determine next stage to advance to (so DB reflects "now at next")
    advance_to = ''
    if next_stage and next_stage in REVIEW_STEP_ORDER:
        try:
            cur_idx = REVIEW_STEP_ORDER.index(stage)
            nxt_idx = REVIEW_STEP_ORDER.index(next_stage)
            if nxt_idx > cur_idx:
                advance_to = next_stage
        except ValueError:
            pass
    if not advance_to:
        try:
            cur_idx = REVIEW_STEP_ORDER.index(stage)
            if cur_idx + 1 < len(REVIEW_STEP_ORDER):
                candidate = REVIEW_STEP_ORDER[cur_idx + 1]
                # Only auto-advance if not already beyond candidate
                if (app.review_stage or '') != candidate:
                    advance_to = candidate
        except ValueError:
            pass
    if advance_to:
        # Move review_stage + status to next stage so stepper shows next as active
        app.review_stage = advance_to
        if advance_to in status_map:
            app.status = status_map[advance_to]
        elif advance_to == 'received':
            app.status = 'pending'
    app.save(update_fields=['review_stage', 'status', 'review_note', 'updated_at'])
    msg = REVIEW_STAGE_MESSAGES.get(stage, stage)
    if note:
        msg = f"{msg} — Bank note: {note}"
    ApplicationTimelineEvent.log(app, stage, message=msg, user=user)
    # Also log advancement so customer sees "Bank is now at next stage" if we auto-advanced
    if advance_to and advance_to != stage:
        nxt_msg = REVIEW_STAGE_MESSAGES.get(advance_to, advance_to)
        ApplicationTimelineEvent.log(app, advance_to, message=nxt_msg, user=user)
    try:
        _sync_property_status(app)
    except Exception:
        pass
    return msg


def _real_application_detail(pk):
    """Try loading real MortgageApplication from DB; return None if missing."""
    try:
        from mortgages.models import MortgageApplication
        app = MortgageApplication.objects.select_related('customer', 'property', 'bank').prefetch_related('document_files', 'repayment_schedule', 'timeline_events').get(pk=pk)
        docs = []
        # Map doc_type to friendly title
        DOC_TYPE_TITLES = {
            'id_passport': 'ID / Passport',
            'payslip': 'Pay Slip',
            'bank_statement': 'Bank Statement',
            'tax_clearance': 'Tax Clearance',
            'other': 'Other Document',
        }
        for d in app.document_files.all():
            fname = (d.file.name.split('/')[-1] if d.file else d.get_doc_type_display())
            ext = (fname.rsplit('.', 1)[-1] if '.' in fname else '').lower()
            title = DOC_TYPE_TITLES.get(d.doc_type, d.get_doc_type_display())
            # If still Other but filename hints type, improve
            if d.doc_type == 'other' and fname:
                low = fname.lower()
                if 'payslip' in low or 'pay' in low:
                    title = 'Pay Slip'
                elif 'bank' in low and 'statement' in low:
                    title = 'Bank Statement'
                elif 'nida' in low or 'id' in low or 'passport' in low:
                    title = 'ID / Passport'
                elif 'deed' in low or 'title' in low:
                    title = 'Title Deed'
                elif 'hat' in low:
                    title = 'Property Document'
            docs.append({"name": fname, "title": title, "size": "", "verified": True, "url": d.file.url if d.file else "#",
                         "type": title, "ext": ext,
                         "is_pdf": ext == 'pdf',
                         "is_image": ext in ('jpg', 'jpeg', 'png', 'webp', 'gif')})
        # No mock documents - empty list if none (template shows empty state)
        cust = app.customer
        prop = app.property
        risk = float(app.risk_score or 0)
        try:
            cust_photo = cust.profile_image.url if cust and cust.profile_image else ''
        except Exception:
            cust_photo = ''
        try:
            prop_photo = prop.image.url if prop and prop.image else ''
        except Exception:
            prop_photo = ''
        try:
            gallery = [g.image.url for g in prop.gallery.all() if g.image] if prop else []
        except Exception:
            gallery = []
        if prop_photo and prop_photo not in gallery:
            gallery = [prop_photo] + gallery
        prop_info = None
        if prop:
            prop_info = {
                "title": getattr(prop, 'title', '-'),
                "photo": prop_photo,
                "gallery": gallery,
                "price": float(getattr(prop, 'price', 0) or 0),
                "location": getattr(prop, 'location', '') or '',
                "type": prop.get_property_type_display() if getattr(prop, 'property_type', None) else '-',
                "category": prop.get_property_category_display() if getattr(prop, 'property_category', None) else '',
                "status": prop.get_status_display() if getattr(prop, 'status', None) else '',
                "area": str(getattr(prop, 'area', '') or ''),
                "bedrooms": getattr(prop, 'bedrooms', None),
                "bathrooms": getattr(prop, 'bathrooms', None),
                "description": (getattr(prop, 'description', '') or '')[:500],
                "napa": getattr(prop, 'napa', '') or '',
                "seller": prop.seller.get_full_name() if getattr(prop, 'seller', None) else '',
            }
        # Extract CRB-related extra info from draft_data (has_existing_loan etc)
        crb_info = {}
        try:
            dd = app.draft_data or {}
            crb_info = {
                'has_existing_loan': dd.get('has_existing_loan') or dd.get('has_existing_loan') or '',
                'existing_loan_bank': dd.get('existing_loan_bank') or '',
                'existing_loan_amount': dd.get('existing_loan_amount') or '',
                'existing_loan_repayment': dd.get('existing_loan_repayment') or '',
                'existing_loan_balance': dd.get('existing_loan_balance') or '',
                'dob': dd.get('dob') or '',
                'gender': dd.get('gender') or '',
                'marital_status': dd.get('marital_status') or '',
                'dependents': dd.get('dependents') or '',
                'nida': dd.get('nin') or dd.get('nida') or '',
                'contract_type': dd.get('contract_type') or '',
                'years_employed': dd.get('years_employed') or '',
                'job_title': dd.get('job_title') or '',
                'employer_name': dd.get('employer_name') or '',
                'business_name': dd.get('business_name') or '',
                'business_type': dd.get('business_type') or '',
            }
            # Also try direct fields if draft_data missing
            if not crb_info['has_existing_loan']:
                crb_info['has_existing_loan'] = getattr(app, 'has_existing_loan', '') or '—'
        except Exception:
            crb_info = {}
        # Bank-side timeline: skip the 'received'/'Sent to bank' event - the
        # static "Application Submitted — sent directly to bank" row already
        # covers it, otherwise it shows twice and confuses officers.
        timeline = list(app.timeline_events.exclude(stage='received').order_by('created_at').values('stage', 'title', 'message', 'created_at'))
        # 3-state review steps: done (confirmed earlier) / active (current) / pending.
        confirmed_at = {}
        for ev in app.timeline_events.order_by('created_at').values('stage', 'created_at'):
            confirmed_at[ev['stage']] = ev['created_at']
        cur_stage = getattr(app, 'review_stage', 'received') or 'received'
        try:
            cur_idx = REVIEW_STEP_ORDER.index(cur_stage)
        except ValueError:
            cur_idx = 0
        STAGE_SHORT = {
            'received': 'Receipt',
            'document_verification': 'Documents',
            'crb_check': 'CRB Check',
            'valuation': 'Valuation',
            'credit_assessment': 'Credit Check',
            'approval_decision': 'Decision',
        }
        final = app.status in ('approved', 'rejected', 'disbursed')
        steps = []
        for i, s in enumerate(REVIEW_STEP_ORDER):
            if app.status in ('approved', 'disbursed'):
                state = 'done'
            elif i < cur_idx:
                state = 'done'
            elif i == cur_idx:
                # The stage the bank is currently at - highlighted as active,
                # even though confirming it is what moved the process here.
                state = 'active' if app.status not in ('rejected',) else 'done'
            else:
                # Confirmed out of order (has an event) counts as done.
                state = 'done' if s in confirmed_at else 'pending'
            nxt = REVIEW_STEP_ORDER[i+1] if i+1 < len(REVIEW_STEP_ORDER) else ''
            steps.append({"key": s, "label": REVIEW_STEP_LABELS.get(s, s),
                          "short": STAGE_SHORT.get(s, s),
                          "state": state,
                          "next_key": nxt,
                          "confirmed_at": confirmed_at.get(s, '')})
        return {
            "id": app.id,
            "ref": getattr(app, 'application_number', f"APP-{app.id}"),
            "customer": cust.get_full_name() if cust else "-",
            "full_name": cust.get_full_name() if cust else "-",
            "email": getattr(cust, 'email', '') if cust else '',
            "phone": getattr(cust, 'phone_number', '') if cust else '',
            "nida": getattr(cust, 'national_id', '') if cust else '',
            "employer": app.get_employment_status_display() if app.employment_status else "-",
            "address": getattr(cust, 'address', '') if cust else '',
            "amount": float(app.loan_amount or 0),
            "property_value": float(getattr(prop, 'price', 0) or 0) if prop else 0,
            "property_name": getattr(prop, 'title', '-') if prop else '-',
            "property_location": getattr(prop, 'location', '') if prop else '',
            "type": app.get_mortgage_type_display() if app.mortgage_type else (app.get_loan_type_display() if app.loan_type else "House"),
            "term": app.repayment_period or 0,
            "income": float(app.monthly_income or 0),
            "score": int(app.affordability_score or 0),
            "ai_score": int(app.affordability_score or 0),
            "ai_percent": int(app.affordability_score or 0),
            "ai_risk": "Low" if risk < 40 else ("High" if risk > 70 else "Medium"),
            "risk_score": risk,
            "dti": f"{float(app.dti_ratio or 0):.1f}%",
            "interest": f"{float(app.bank.interest_rate):.1f}%" if getattr(app, 'bank', None) and getattr(app.bank, 'interest_rate', None) else "13%",
            "processing_fee_percent": f"{float(app.bank.processing_fee):.1f}%" if getattr(app, 'bank', None) and getattr(app.bank, 'processing_fee', None) else "2.0%",
            "monthly_payment": float(app.monthly_installment or 0),
            "status": app.status,
            "review_stage": getattr(app, 'review_stage', 'received') or 'received',
            "review_note": getattr(app, 'review_note', '') or '',
            "customer_photo": cust_photo,
            "customer_initials": (getattr(cust, 'initials', '') or (cust.get_full_name()[:1] if cust and cust.get_full_name() else '-')) if cust else '-',
            "customer_since": cust.date_joined.strftime("%b %Y") if cust and getattr(cust, 'date_joined', None) else '',
            "property_info": prop_info,
            "date": app.created_at.strftime("%Y-%m-%d") if app.created_at else "",
            "notes": app.notes or "",
            "documents": docs,
            "timeline": timeline,
            "corrections": _correction_dicts(app),
            "pending_corrections": app.corrections.filter(status='pending').count(),
            "answered_corrections": app.corrections.filter(status='resolved').order_by('-resolved_at')[:3],
            "crb_info": crb_info,
            "next_stage": next((s["key"] for s in steps if s["state"] == 'pending'), ''),
            "next_stage_label": next((s["label"] for s in steps if s["state"] == 'pending'), ''),
            "step_order": REVIEW_STEP_ORDER,
            "step_labels": REVIEW_STEP_LABELS,
            "steps": steps,
            "avatar": "https://i.pravatar.cc/100?img=5",
            "is_real": True,
        }
    except Exception:
        return None


def bank_application_detail(request, pk):
    """
    GET /bank/applications/<id>/
    - Customer details, Loan details, Documents, AI Risk Analysis
    - Data real from DB, mock fallback if missing
    """
    real = _real_application_detail(pk)
    if real:
        return render(request, "bank/bank_application_detail.html", {"application": real})
    from django.http import Http404
    raise Http404("Application not found.")


def bank_application_review(request, pk):
    """
    GET /bank/applications/<id>/review/  -> show documents + staged checklist + form
    POST -> confirm a review stage (action=stage) OR final Approve/Reject.
    Every stage confirmation is logged to timeline so the customer sees it live.
    """
    try:
        from mortgages.models import MortgageApplication as _MA
        _exists = _MA.objects.filter(pk=pk).exists()
        application = {"id": pk, "is_real": bool(_exists)}
    except Exception:
        application = {"id": pk}

    if request.method == "POST":
        from django.contrib import messages
        from django.shortcuts import redirect
        try:
            from mortgages.models import ApplicationTimelineEvent, MortgageApplication
            app = MortgageApplication.objects.get(pk=pk)
            user = request.user if getattr(request.user, 'is_authenticated', False) else None
            action = request.POST.get("action", "") or request.POST.get("decision", "")
            # 1) Bank confirms one intermediate step
            if action in ('document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approval_decision') or request.POST.get("stage"):
                stage = request.POST.get("stage") or action
                note = request.POST.get("note", "") or request.POST.get("notes", "")
                do_exit = request.POST.get("exit") == "1"
                if stage not in REVIEW_STEP_ORDER:
                    messages.error(request, "Unknown stage.")
                    return redirect("bank_application_detail", pk=pk)
                # Allow confirming the active stage; only block if this stage already passed (behind current)
                try:
                    cur_idx_chk = REVIEW_STEP_ORDER.index(app.review_stage or 'received')
                    st_idx_chk = REVIEW_STEP_ORDER.index(stage)
                    if st_idx_chk < cur_idx_chk and not note.strip():
                        messages.info(request, "Stage already confirmed.")
                        return redirect("bank_application_detail", pk=pk) if do_exit else redirect("bank_application_review", pk=pk)
                except ValueError:
                    pass
                nxt_stage = request.POST.get("next_stage") or ""
                msg = _advance_application(app, stage, user=user, note=note, next_stage=nxt_stage)
                messages.success(request, STAGE_SUCCESS_MESSAGES.get(stage, "Stage confirmed successfully."))
                if do_exit:
                    return redirect("bank_dashboard")
                nxt = nxt_stage
                if nxt and nxt in REVIEW_STEP_ORDER:
                    try:
                        idx = REVIEW_STEP_ORDER.index(nxt)
                        return redirect(f"/bank/applications/{pk}/review/#bsSeg{idx}")
                    except: pass
                    return redirect(f"/bank/applications/{pk}/review/#segment-{nxt}")
                elif nxt:
                    return redirect(f"/bank/applications/{pk}/review/#segment-{nxt}")
                return redirect("bank_application_review", pk=pk)
            decision = request.POST.get("decision")  # approve | reject
            reason = request.POST.get("reason", "")
            if decision == "approve":
                app.status = "approved"
                app.review_stage = 'approval_decision'
                # Optional from approval form: amount/interest/term
                amt = request.POST.get("approved_amount") or request.POST.get("amount")
                if amt:
                    try:
                        app.loan_amount = amt
                    except Exception:
                        pass
                notes = request.POST.get("notes", "")
                if notes:
                    app.notes = ((app.notes or "") + f"\n[Bank approval] {notes}").strip()
                    app.review_note = notes
                app.save()
                ApplicationTimelineEvent.log(app, 'approved', user=user)
                try:
                    _sync_property_status(app)
                except Exception:
                    pass
                messages.success(request, "Application approved successfully.")
            else:
                app.status = "rejected"
                app.review_stage = 'approval_decision'
                notes = request.POST.get("notes", reason)
                if notes:
                    app.notes = ((app.notes or "") + f"\n[Bank rejection] {notes}").strip()
                    app.review_note = notes
                app.save()
                ApplicationTimelineEvent.log(
                    app, 'rejected',
                    message=f"The bank has finished review — this application was rejected. Reason: {notes}" if notes else None,
                    user=user,
                )
                try:
                    _sync_property_status(app)
                except Exception:
                    pass
                messages.success(request, "Application rejected successfully.")
        except Exception:
            pass
        return redirect("bank_application_detail", pk=pk)

    real = _real_application_detail(pk)
    return render(request, "bank/bank_application_review.html", {"application": real or application})


def bank_application_correction(request, pk):
    """POST /bank/applications/<id>/correction/ - Bank sends a correction request
    (e.g. re-upload an unclear title deed, or type in the NIDA number).
    The customer sees it on their track page with instructions + input field,
    and gets a notification through the timeline."""
    from django.contrib import messages
    from django.shortcuts import redirect
    if request.method != "POST":
        return redirect("bank_application_detail", pk=pk)
    try:
        from mortgages.models import ApplicationCorrection, ApplicationTimelineEvent, MortgageApplication
        app = MortgageApplication.objects.get(pk=pk)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        kind = request.POST.get("kind", "document")
        if kind not in ('document', 'nida', 'info', 'other'):
            kind = 'document'
        target = request.POST.get("target", "").strip()[:200]
        instructions = request.POST.get("instructions", "").strip()
        if not instructions:
            messages.error(request, "Write instructions first.")
            return redirect("bank_application_review", pk=pk)
        # No duplicates: the same pending request must not be sent twice
        # (e.g. double-click) - it confuses the customer.
        dupe = ApplicationCorrection.objects.filter(
            application=app, kind=kind, target=target,
            instructions=instructions, status='pending').first()
        if dupe:
            messages.info(request, "Correction already sent.")
            return redirect("bank_application_review", pk=pk)
        ApplicationCorrection.objects.create(
            application=app, kind=kind, target=target,
            instructions=instructions, created_by=user)
        try:
            app_no = app.application_number
        except Exception:
            app_no = f"APP-{app.id}"
        ApplicationTimelineEvent.log(
            app, 'note',
            title='Correction requested',
            message=f"Bank requested a correction on {app_no} ({target or kind}): {instructions[:200]}. Open your application to respond.",
            user=user)
        messages.success(request, "Correction request sent successfully.")
    except Exception as e:
        messages.error(request, "Failed to send correction.")
    return redirect("bank_application_review", pk=pk)


def bank_application_stage(request, pk):
    """POST /bank/applications/<id>/stage/ - Bank confirms one review step (CRB etc).
    Supports ?next=detail or form field exit=1 to return to detail page (Confirm & Exit)."""
    from django.contrib import messages
    from django.shortcuts import redirect
    if request.method != "POST":
        return redirect("bank_application_detail", pk=pk)
    do_exit = request.POST.get("exit") == "1" or request.GET.get("next") == "detail"
    try:
        from mortgages.models import MortgageApplication
        app = MortgageApplication.objects.get(pk=pk)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        stage = request.POST.get("stage", "")
        note = request.POST.get("note", "")
        if stage not in REVIEW_STEP_ORDER:
            messages.error(request, "Unknown stage.")
            return redirect("bank_application_detail", pk=pk)
        try:
            cur_idx_chk = REVIEW_STEP_ORDER.index(app.review_stage or 'received')
            st_idx_chk = REVIEW_STEP_ORDER.index(stage)
            if st_idx_chk < cur_idx_chk and not note.strip():
                messages.info(request, "Stage already confirmed.")
                return redirect("bank_application_detail", pk=pk) if do_exit else redirect("bank_application_review", pk=pk)
        except ValueError:
            pass
        nxt_stage = request.POST.get("next_stage") or ""
        msg = _advance_application(app, stage, user=user, note=note, next_stage=nxt_stage)
        messages.success(request, STAGE_SUCCESS_MESSAGES.get(stage, "Stage confirmed successfully."))
    except Exception as e:
        messages.error(request, "Failed to update stage.")
    if do_exit:
        return redirect("bank_dashboard")
    # Stay on review but jump to next stage if provided
    nxt = request.POST.get("next_stage") or ""
    if nxt and nxt in REVIEW_STEP_ORDER:
        try:
            idx = REVIEW_STEP_ORDER.index(nxt)
            return redirect(f"/bank/applications/{pk}/review/#bsSeg{idx}")
        except: pass
        return redirect(f"/bank/applications/{pk}/review/#segment-{nxt}")
    return redirect("bank_application_review", pk=pk)


def bank_application_approve(request, pk):
    """POST /bank/applications/<id>/approve/ - Set status='approved' (real DB)."""
    from django.contrib import messages
    from django.shortcuts import redirect
    if request.method != "POST":
        return redirect("bank_application_detail", pk=pk)
    try:
        from mortgages.models import ApplicationTimelineEvent, MortgageApplication
        app = MortgageApplication.objects.get(pk=pk)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        amt = request.POST.get("approved_amount")
        if amt:
            try:
                app.loan_amount = amt
            except Exception:
                pass
        notes = request.POST.get("notes", "")
        if notes:
            app.notes = ((app.notes or "") + f"\n[Bank approval] {notes}").strip()
            app.review_note = notes
        app.status = "approved"
        app.review_stage = 'approval_decision'
        app.save()
        ApplicationTimelineEvent.log(app, 'approved', user=user)
        try:
            _sync_property_status(app)
        except Exception:
            pass
        messages.success(request, "Application approved successfully.")
    except Exception as e:
        messages.error(request, "Failed to approve.")
    return redirect("bank_application_detail", pk=pk)


def bank_application_reject(request, pk):
    """POST /bank/applications/<id>/reject/ - Set status='rejected' (real DB)."""
    from django.contrib import messages
    from django.shortcuts import redirect
    if request.method != "POST":
        return redirect("bank_application_detail", pk=pk)
    try:
        from mortgages.models import ApplicationTimelineEvent, MortgageApplication
        app = MortgageApplication.objects.get(pk=pk)
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        reason = request.POST.get("reason", "")
        notes = request.POST.get("notes", "")
        extra = f" Reason: {reason}" if reason else ""
        app.notes = ((app.notes or "") + f"\n[Bank rejection]{extra} {notes}").strip()
        app.status = "rejected"
        app.review_stage = 'approval_decision'
        app.review_note = (reason or notes or '')[:500]
        app.save()
        ApplicationTimelineEvent.log(
            app, 'rejected',
            message=f"The bank has finished review — this application was rejected. Reason: {reason or notes}" if (reason or notes) else None,
            user=user,
        )
        try:
            _sync_property_status(app)
        except Exception:
            pass
        messages.success(request, "Application rejected successfully.")
    except Exception as e:
        messages.error(request, "Failed to reject.")
    return redirect("bank_application_detail", pk=pk)


def bank_application_pdf(request, pk):
    """GET /bank/applications/<id>/pdf/ - Full application summary PDF.
    Includes: company logo + bank logo, application code, customer, property,
    loan details, review stages timeline. Nicely designed with reportlab."""
    from django.http import HttpResponse
    detail = _real_application_detail(pk)
    if not detail:
        from django.http import Http404
        raise Http404("Application not found.")
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (Image as RLImage, Paragraph, SimpleDocTemplate,
                                        Spacer, Table, TableStyle)
    except ImportError:
        return HttpResponse("PDF library missing. Install reportlab.", status=500)
    import os
    from django.conf import settings
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="MorgiHome-{detail.get("ref", pk)}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=14*mm, bottomMargin=14*mm,
                            title=f"MorgiHome {detail.get('ref')}")
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0A2B4E'), spaceAfter=2)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#0077B6'), spaceBefore=10, spaceAfter=6)
    normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#222222'))
    footer_style = ParagraphStyle('footer', parent=styles['Normal'], fontSize=11, leading=15, textColor=colors.HexColor('#0A2B4E'))
    sign_style = ParagraphStyle('sign', parent=styles['Normal'], fontSize=11, leading=16, textColor=colors.HexColor('#111111'))
    th_style = ParagraphStyle('th', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.white)
    story = []
    # Header logos: company left, bank right - same size
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'morgihome-official-logo.png')
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.BASE_DIR, 'logo.png')
    header_cells = []
    try:
        if os.path.exists(logo_path):
            header_cells.append(RLImage(logo_path, width=38*mm, height=16*mm))
        else:
            header_cells.append(Paragraph('<b>MorgiHome</b>', h1))
    except Exception:
        header_cells.append(Paragraph('<b>MorgiHome</b>', h1))
    # Bank logo - same size as company logo
    try:
        from mortgages.models import MortgageApplication as _MA2
        _app = _MA2.objects.select_related('bank').get(pk=pk)
        _bank = getattr(_app, 'bank', None)
        _blogo = None
        if _bank and getattr(_bank, 'profile_image', None):
            try:
                _blogo = _bank.profile_image.path
            except Exception:
                _blogo = None
        if _blogo and os.path.exists(_blogo):
            header_cells.append(RLImage(_blogo, width=38*mm, height=16*mm))
        else:
            header_cells.append(Paragraph(f"<b>{(_bank.get_full_name() if _bank else 'Bank')}</b>", normal))
    except Exception:
        header_cells.append(Paragraph('<b>Partner Bank</b>', normal))
    ht = Table([header_cells], colWidths=[85*mm, 85*mm])
    ht.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('ALIGN', (1, 0), (1, 0), 'RIGHT')]))
    story.append(ht)
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Mortgage Application Summary', h1))
    story.append(Paragraph(f"Application Code: <b>{detail.get('ref')}</b> &nbsp;|&nbsp; Status: <b>{str(detail.get('status','')).title()}</b> &nbsp;|&nbsp; Date: {detail.get('date','')}", normal))
    story.append(Spacer(1, 2*mm))

    # Customer profile picture in PDF - MUST show (photo or initials fallback)
    try:
        from reportlab.lib.utils import ImageReader
        cust_photo_path = None
        cust_initials = (detail.get('full_name') or 'C')[:1].upper()
        _app_obj = _MA2.objects.select_related('customer').get(pk=pk)
        _cust = getattr(_app_obj, 'customer', None)
        if _cust and getattr(_cust, 'profile_image', None):
            try:
                cust_photo_path = _cust.profile_image.path
            except Exception:
                cust_photo_path = None
        has_photo = cust_photo_path and os.path.exists(cust_photo_path)
        if has_photo:
            try:
                c_img = RLImage(cust_photo_path, width=22*mm, height=22*mm)
                # Try to make it circular-like via border
                cust_header = [[c_img, Paragraph(f"<b>{detail.get('full_name') or 'Customer'}</b><br/><font size=8 color='#6b7280'>{detail.get('email') or ''} • {detail.get('phone') or ''}</font><br/><font size=7 color='#0077B6'>Customer Profile</font>", normal)]]
                ct = Table(cust_header, colWidths=[24*mm, 146*mm])
                ct.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2), ('BOX', (0,0), (0,0), 0.5, colors.HexColor('#0077B6'))]))
                story.append(ct)
                story.append(Spacer(1, 3*mm))
            except Exception:
                has_photo = False
        if not has_photo:
            # Fallback: show initials in a colored box + customer info - ensures PDF always has profile picture area
            initials_style = ParagraphStyle('initials', parent=normal, fontSize=14, leading=16, textColor=colors.white, alignment=1)
            # Create a table with initials placeholder
            try:
                # Draw initials box using Table with background
                init_para = Paragraph(f"<b>{cust_initials}</b>", initials_style)
                init_table = Table([[init_para]], colWidths=[22*mm], rowHeights=[22*mm])
                init_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0077B6')),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#0077B6')),
                    ('ROUNDEDCORNERS', [4,4,4,4]),
                ]))
                cust_header2 = [[init_table, Paragraph(f"<b>{detail.get('full_name') or 'Customer'}</b><br/><font size=8 color='#6b7280'>{detail.get('email') or ''} • {detail.get('phone') or ''}</font><br/><font size=7 color='#6b7280'>Profile photo: {cust_initials} (no photo uploaded)</font>", normal)]]
                ct2 = Table(cust_header2, colWidths=[24*mm, 146*mm])
                ct2.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2)]))
                story.append(ct2)
                story.append(Spacer(1, 3*mm))
            except Exception:
                # Last fallback: just text
                story.append(Paragraph(f"<b>{detail.get('full_name') or 'Customer'}</b> — {detail.get('email') or ''} • {detail.get('phone') or ''}", normal))
                story.append(Spacer(1, 2*mm))
    except Exception:
        pass

    def _row(k, v):
        return [Paragraph(f"<b>{k}</b>", normal), Paragraph(str(v or '-'), normal)]

    cust_data = [
        _row('Customer', detail.get('full_name')),
        _row('Phone', detail.get('phone')),
        _row('Email', detail.get('email')),
        _row('Employer', detail.get('employer')),
        _row('Monthly Income', f"TZS {float(detail.get('income') or 0):,.0f}"),
    ]
    prop = detail.get('property_info') or {}
    loan_data = [
        _row('Loan Amount', f"TZS {float(detail.get('amount') or 0):,.0f}"),
        _row('Term', f"{detail.get('term')} months"),
        _row('Property', prop.get('title', detail.get('property_name'))),
        _row('Location', prop.get('location', '')),
        _row('Value', f"TZS {float(prop.get('price') or detail.get('property_value') or 0):,.0f}"),
    ]
    story.append(Paragraph('Customer', h2))
    t1 = Table(cust_data, colWidths=[45*mm, 125*mm])
    t1.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFF6FF')),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    story.append(t1)
    story.append(Paragraph('Loan & Property', h2))
    t2 = Table(loan_data, colWidths=[45*mm, 125*mm])
    t2.setStyle(TableStyle([('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#EFF6FF')),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    story.append(t2)
    story.append(Paragraph('Review Stages', h2))
    steps = detail.get('steps') or []
    stage_rows = [[Paragraph('<b><font color="white">Stage</font></b>', th_style), Paragraph('<b><font color="white">State</font></b>', th_style)]]
    for s in steps:
        stage_rows.append([Paragraph(str(s.get('label')), normal), Paragraph(str(s.get('state')).title(), normal)])
    t3 = Table(stage_rows, colWidths=[120*mm, 50*mm])
    t3.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A2B4E')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
    story.append(t3)
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph('Generated by MorgiHome Bank Portal • Brain-Wave Group • 2026', footer_style))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Customer signature: ____________________ &nbsp;&nbsp; Bank officer: ____________________ &nbsp;&nbsp; Date: __________", sign_style))
    doc.build(story)
    return response


def bank_contract_detail(request, pk):
    """GET /bank/contracts/<id>/ - Contract details + signature status + PDF."""
    try:
        from transactions.models import Contract
        c = Contract.objects.select_related('mortgage', 'customer', 'bank').get(pk=pk)
        contract = {
            "id": c.id, "ref": f"CTR-2026-{c.id:04d}",
            "customer": c.customer.get_full_name() if c.customer else "-",
            "property_name": getattr(getattr(c.mortgage, 'property', None), 'title', '-'),
            "amount": float(getattr(c.mortgage, 'loan_amount', 0) or 0),
            "status": c.status, "created": c.created_at,
            "customer_signed": c.customer_signed, "seller_signed": c.seller_signed,
            "bank_signed": c.bank_signed, "file_url": c.contract_file.url if c.contract_file else None,
            "notes": c.notes or "",
        }
    except Exception:
        contract = {"id": pk, "ref": f"CTR-2026-{int(pk):04d}", "customer": "Neema Sanga",
                    "property_name": "House - Tegeta", "amount": 120000000, "status": "pending_signature",
                    "created": None, "customer_signed": True, "seller_signed": False,
                    "bank_signed": False, "file_url": None, "notes": ""}
    if request.method == "POST" and request.POST.get("action") == "sign":
        try:
            from django.contrib import messages
            from django.shortcuts import redirect
            c.bank_signed = True
            if c.is_fully_signed():
                c.status = "signed"
            c.save(update_fields=["bank_signed", "status", "updated_at"])
            messages.success(request, "Contract signed successfully.")
        except Exception:
            pass
        return redirect("bank_contract_detail", pk=pk)
    return render(request, "bank/bank_contract_detail.html", {"contract": contract})


def bank_repayment_detail(request, pk):
    """GET /bank/repayments/<id>/ - Loan details + schedule + history (mortgage pk)."""
    try:
        from mortgages.models import MortgageApplication
        app = MortgageApplication.objects.select_related('customer', 'property').prefetch_related('repayment_schedule').get(pk=pk)
        sched = list(app.repayment_schedule.all().order_by('installment_number'))
        total_due = sum(float(s.amount_due or 0) for s in sched)
        total_paid = sum(float(s.amount_paid or 0) for s in sched)
        detail = {"id": app.id,
                  "customer": app.customer.get_full_name() if app.customer else "-",
                  "amount": float(app.loan_amount or 0), "total_due": total_due,
                  "total_paid": total_paid, "balance": total_due - total_paid,
                  "status": app.status, "schedule": sched}
    except Exception:
        detail = {"id": pk, "customer": "Neema Sanga", "amount": 120000000,
                  "total_due": 120000000, "total_paid": 1580000, "balance": 118420000,
                  "status": "Active", "schedule": []}
    return render(request, "bank/bank_repayment_detail.html", {"detail": detail})


def bank_profile(request):
    """GET /bank/profile/ - Bank profile (name, role, status, stats)."""
    from mortgages.models import MortgageApplication
    from transactions.models import Contract
    from django.db.models import Sum
    user = request.user if request.user.is_authenticated else None
    try:
        qs = MortgageApplication.objects.all()
        if user is not None and getattr(user, 'role', '') == 'bank':
            qs = qs.filter(bank=user)
        total = qs.exclude(status='draft').count()
        approved = qs.filter(status='approved').count()
        cqs = Contract.objects.all()
        if user is not None and getattr(user, 'role', '') == 'bank':
            cqs = cqs.filter(bank=user)
        disbursed_amount = cqs.filter(status='executed').aggregate(total=Sum('mortgage__loan_amount'))['total'] or 0
    except Exception:
        total, approved, disbursed_amount = 0, 0, 0
    context = {
        "bank_name": user.get_full_name() if user and getattr(user, 'role', '') == 'bank' else "CRDB Bank",
        "email": getattr(user, 'email', 'admin@crdb.co.tz') if user else 'admin@crdb.co.tz',
        "role": "Bank",
        "verified": bool(getattr(user, 'is_verified', True)) if user else True,
        "stats": {"total": total, "approved": approved, "disbursed_amount": disbursed_amount},
    }
    return render(request, "bank/bank_profile.html", context)


def _contract_dict(c):
    cust = getattr(c, 'customer', None)
    name = cust.get_full_name() if cust else '-'
    try:
        cphoto = cust.profile_image.url if cust and cust.profile_image else ''
    except Exception:
        cphoto = ''
    mort = getattr(c, 'mortgage', None)
    prop = getattr(mort, 'property', None) if mort else None
    amount = float(getattr(mort, 'loan_amount', 0) or 0) if mort else 0
    monthly = float(getattr(mort, 'monthly_installment', 0) or 0) if mort else 0
    status_map = {'executed': 'Active', 'signed': 'Signed', 'pending_signature': 'Pending Signature', 'draft': 'Draft'}
    return {
        "id": c.id,
        "ref": f"CTR-{c.id:06d}",
        "app_id": mort.id if mort else None,
        "app_ref": getattr(mort, 'application_number', f"APP-{mort.id}") if mort else '-',
        "customer": name,
        "initials": (getattr(cust, 'initials', '') or (name[:1] if name else '-')) if cust else '-',
        "photo": cphoto,
        "property_name": getattr(prop, 'title', '-') if prop else '-',
        "amount": amount,
        "monthly": monthly,
        "date": c.created_at.strftime('%Y-%m-%d') if getattr(c, 'created_at', None) else '',
        "status": c.status,
        "status_display": status_map.get(c.status, c.status),
        "link": f"/bank/contracts/{c.id}/",
    }


def bank_contracts(request):
    """
    GET /bank/contracts/ - REAL DATA from DB (no mock).
    """
    qs = _scoped_contracts(request).order_by('-created_at')
    contracts = [_contract_dict(c) for c in qs[:50]]
    context = {
        "contracts": contracts,
        "total_count": qs.count(),
        "active_count": qs.filter(status__in=['executed', 'signed']).count(),
        "pending_count": qs.filter(status='pending_signature').count(),
        "executed_count": qs.filter(status='executed').count(),
    }
    return render(request, "bank/bank_contracts.html", context)


def _schedule_status(s):
    """Paid / Overdue / Upcoming based on status + due_date."""
    if getattr(s, 'status', '') == 'paid' or float(getattr(s, 'amount_paid', 0) or 0) >= float(getattr(s, 'amount_due', 0) or 0):
        return 'Paid'
    due = getattr(s, 'due_date', None)
    if due and due < timezone.now().date():
        return 'Overdue'
    return 'Upcoming'


def _schedule_dict(s):
    mort = getattr(s, 'mortgage', None)
    cust = getattr(mort, 'customer', None) if mort else None
    name = cust.get_full_name() if cust else '-'
    due = getattr(s, 'due_date', None)
    return {
        "mortgage_id": mort.id if mort else None,
        "customer": name,
        "initials": (getattr(cust, 'initials', '') or (name[:1] if name else '-')) if cust else '-',
        "contract_ref": f"CTR-{mort.id:06d}" if mort else '-',
        "due": due.strftime('%Y-%m-%d') if due else '',
        "amount": float(getattr(s, 'amount_due', 0) or 0),
        "paid": float(getattr(s, 'amount_paid', 0) or 0),
        "status": _schedule_status(s),
        "days": (timezone.now().date() - due).days if due and due < timezone.now().date() else 0,
        "link": f"/bank/repayments/{mort.id}/" if mort else '#',
    }


def bank_repayments(request):
    """
    GET /bank/repayments/ - REAL DATA from RepaymentSchedule (no mock).
    """
    from mortgages.models import RepaymentSchedule
    from django.db.models import Sum
    sqs = RepaymentSchedule.objects.select_related('mortgage__customer', 'mortgage__bank')
    bu = _bank_user(request)
    if bu is not None:
        sqs = sqs.filter(mortgage__bank=bu)
    today = timezone.now().date()
    total_due = sqs.aggregate(t=Sum('amount_due'))['t'] or 0
    total_paid = sqs.aggregate(t=Sum('amount_paid'))['t'] or 0
    overdue_qs = sqs.exclude(status='paid').filter(due_date__lt=today)
    overdue_count = overdue_qs.count()
    overdue_amount = overdue_qs.aggregate(t=Sum('amount_due'))['t'] or 0
    npl_count = overdue_qs.filter(due_date__lt=today - timedelta(days=90)).count()
    done = sqs.filter(status='paid').count()
    total_n = sqs.count()
    on_time = round(done / total_n * 100, 1) if total_n else 0
    rows = [_schedule_dict(s) for s in sqs.order_by('due_date')[:30]]
    defaulters = [_schedule_dict(s) for s in overdue_qs.order_by('due_date')[:5]]
    months = _month_buckets(6)
    chart_labels, chart_paid = [], []
    for b in months:
        chart_labels.append(b['label'])
        chart_paid.append(float(sqs.filter(due_date__year=b['year'], due_date__month=b['month'], status='paid').aggregate(t=Sum('amount_paid'))['t'] or 0))
    context = {
        "stats": {"total_due": total_due, "total_paid": total_paid, "on_time": on_time,
                  "overdue_count": overdue_count, "overdue_amount": overdue_amount, "npl": npl_count,
                  "schedule_count": total_n},
        "repayments": rows,
        "defaulters": defaulters,
        "chart_labels": chart_labels,
        "chart_paid": chart_paid,
    }
    return render(request, "bank/bank_repayments.html", context)


def bank_reports(request):
    """
    GET /bank/reports/ - REAL DATA: summary generated from DB.
    """
    from transactions.models import Contract
    from django.db.models import Sum
    cqs = _scoped_contracts(request)
    aqs = _scoped_apps(request)
    months = _month_buckets(6)
    monthly = []
    for b in months:
        m_apps = aqs.filter(created_at__year=b['year'], created_at__month=b['month'])
        m_exec = cqs.filter(status='executed', executed_date__year=b['year'], executed_date__month=b['month'])
        monthly.append({
            "label": f"{b['label']} {b['year']}",
            "applications": m_apps.count(),
            "approved": m_apps.filter(status__in=['approved', 'disbursed']).count(),
            "disbursed": m_exec.count(),
            "disbursed_amount": float(m_exec.aggregate(t=Sum('mortgage__loan_amount'))['t'] or 0),
        })
    total_apps = aqs.count()
    report_cards = [
        {"name": "Monthly Disbursement", "desc": "Summary of loans disbursed each month",
         "meta": f"{cqs.filter(status='executed').count()} disbursed • TZS {float(cqs.filter(status='executed').aggregate(t=Sum('mortgage__loan_amount'))['t'] or 0):,.0f}"},
        {"name": "Risk & Status Report", "desc": "Applications by status",
         "meta": f"{aqs.filter(status='pending').count()} pending • {aqs.filter(status='approved').count()} approved • {aqs.filter(status='rejected').count()} rejected of {total_apps}"},
        {"name": "Portfolio Summary", "desc": "Total portfolio and concentration",
         "meta": f"{total_apps} applications • {cqs.count()} contracts"},
    ]
    context = {"report_cards": report_cards, "monthly": monthly, "generated_on": timezone.now().strftime('%d %b %Y')}
    return render(request, "bank/bank_reports.html", context)


def bank_verify(request):
    """
    GET/POST /bank/verify/  - Bank verification for Business docs only
    Email/Phone/NIN removed - only business_license, tax_clearance, company_registration remain
    """
    from .forms import BankVerificationForm
    from django.contrib import messages
    form = BankVerificationForm(instance=request.user if request.user.is_authenticated else None)
    if request.method == "POST" and request.user.is_authenticated:
        form = BankVerificationForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Documents saved successfully.")
            return render(request, "bank/bank_verify.html", {"form": form})
    return render(request, "bank/bank_verify.html", {"form": form})

def bank_settings(request):
    """GET/POST /bank/settings/ - Save info + email preference (real functions)."""
    from django.contrib import messages
    from django.shortcuts import redirect
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    if request.method == 'POST' and user is not None:
        action = request.POST.get('action', 'save_profile')
        if action == 'notify':
            user.notify_email = request.POST.get('notify_email') == 'on'
            user.save(update_fields=['notify_email'])
            messages.success(request, 'Notification setting saved.')
            return redirect('bank_settings')
        if action == 'save_terms':
            # Loan terms shown to mortgage applicants on /customer/bank-requirements/ (live from DB)
            def _dec(val):
                val = (val or '').strip()
                return val or None
            def _int(val):
                v=(val or '').strip()
                if not v: return None
                try: return int(float(v))
                except: return None
            user.interest_rate = _dec(request.POST.get('interest_rate'))
            user.processing_fee = _dec(request.POST.get('processing_fee'))
            user.min_loan_amount = _dec(request.POST.get('min_loan_amount'))
            user.max_loan_amount = _dec(request.POST.get('max_loan_amount'))
            user.max_repayment_period = _int(request.POST.get('max_repayment_period'))
            user.bank_requirements = request.POST.get('bank_requirements', '').strip() or None
            try:
                user.save(update_fields=['interest_rate', 'processing_fee', 'min_loan_amount', 'max_loan_amount', 'max_repayment_period', 'bank_requirements'])
                messages.success(request, 'Loan terms saved successfully.')
            except Exception as e:
                messages.error(request, 'Could not save terms.')
            return redirect('bank_settings')
        # save_profile
        name = request.POST.get('bank_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        if email and email != user.email:
            from accounts.models import User as U
            if U.objects.filter(email__iexact=email).exclude(id=user.id).exists():
                messages.error(request, 'Email already in use.')
                return redirect('bank_settings')
            user.email = email
        if name:
            user.first_name = name
        if phone:
            user.phone_number = phone
        try:
            user.save()
            messages.success(request, 'Bank info saved successfully.')
        except Exception as e:
            messages.error(request, 'Could not save.')
        return redirect('bank_settings')
    return render(request, "bank/bank_settings.html", {})


def bank_deactivate(request):
    """POST /bank/settings/deactivate/ - Deactivate bank account (real) + logout."""
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.contrib.auth import logout
    if request.method != 'POST':
        return redirect('bank_settings')
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    if user is None:
        return redirect('/login/')
    if request.POST.get('confirm') != 'DEACTIVATE':
        messages.error(request, 'Type DEACTIVATE to confirm.')
        return redirect('bank_settings')
    user.is_active = False
    user.save(update_fields=['is_active'])
    logout(request)
    messages.warning(request, 'Account deactivated successfully.')
    return redirect('/login/')

def bank_help(request):
    """GET /bank/help/ - Bank help page"""
    return render(request, "bank/bank_help.html", {})

def bank_search(request):
    """GET /bank/search/?q=... - REAL DATA (applications + contracts)."""
    from django.db.models import Q
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        aqs = _scoped_apps(request).filter(
            Q(customer__first_name__icontains=query) | Q(customer__last_name__icontains=query) |
            Q(customer__email__icontains=query) | Q(property__title__icontains=query) |
            Q(mortgage_type__icontains=query) | Q(loan_type__icontains=query))
        try:
            by_id = _scoped_apps(request).filter(id=int(query))
            aqs = (aqs | by_id).distinct()
        except (ValueError, TypeError):
            pass
        for app in aqs.order_by('-created_at')[:20]:
            d = _app_dict(app)
            d['kind'] = 'Application'
            results.append(d)
        cqs = _scoped_contracts(request)
        try:
            cqs = cqs.filter(Q(id=int(query)) | Q(customer__first_name__icontains=query) | Q(customer__last_name__icontains=query))
        except (ValueError, TypeError):
            cqs = cqs.filter(Q(customer__first_name__icontains=query) | Q(customer__last_name__icontains=query))
        for c in cqs.order_by('-created_at')[:10]:
            d = _contract_dict(c)
            results.append({"id": d['id'], "customer": d['customer'], "initials": d['initials'], "amount": d['amount'],
                            "type": 'Contract', "term": '-', "ai_risk": '-', "ai_percent": 0,
                            "status": d['status'], "date": d['date'], "kind": 'Contract', "link": d['link']})
    return render(request, "bank/bank_search.html", {"query": query, "results": results, "total": len(results)})

def _notifications_data(request):
    """Persistent notifications for the logged-in bank (stored in DB - they
    never vanish; read state is stored per row). Guests get a live snapshot."""
    from django.contrib.humanize.templatetags.humanize import naturaltime
    bu = _bank_user(request)
    if bu is not None:
        try:
            from mortgages.models import BankNotification
            rows = BankNotification.objects.filter(recipient=bu).order_by('-created_at')[:30]
            return [{"id": f"bn-{n.id}", "db_id": n.id, "title": n.title, "message": n.message,
                     "time": naturaltime(n.created_at), "read": n.is_read,
                     "icon": n.icon or "file-text", "color": n.color or "blue",
                     "link": n.link or "#"} for n in rows]
        except Exception:
            pass
    # Guest fallback: derived live snapshot (previous behavior).
    from mortgages.models import RepaymentSchedule
    notifications = []
    try:
        aqs = _scoped_apps(request)
        for app in aqs.filter(status__in=PENDING_STATUSES).order_by('-created_at')[:5]:
            d = _app_dict(app)
            notifications.append({"id": f"app-{app.id}", "title": "New Application Received",
                                  "message": f"{d['customer']} submitted {getattr(app, 'application_number', f'APP-{app.id}')} for TZS {d['amount']:,.0f}",
                                  "time": naturaltime(app.created_at) if getattr(app, 'created_at', None) else '',
                                  "read": False, "icon": "file-text", "color": "blue", "link": d['link']})
        for app in aqs.filter(status='approved').order_by('-updated_at')[:2]:
            d = _app_dict(app)
            notifications.append({"id": f"appr-{app.id}", "title": "Application Approved",
                                   "message": f"{d['customer']} {getattr(app, 'application_number', f'APP-{app.id}')} has been approved",
                                   "time": naturaltime(app.updated_at) if getattr(app, 'updated_at', None) else '',
                                   "read": False, "icon": "circle-check", "color": "emerald", "link": d['link']})
        sqs = RepaymentSchedule.objects.select_related('mortgage__customer', 'mortgage__bank')
        if bu is not None:
            sqs = sqs.filter(mortgage__bank=bu)
        for s in sqs.exclude(status='paid').filter(due_date__lt=timezone.now().date()).order_by('due_date')[:3]:
            d = _schedule_dict(s)
            notifications.append({"id": f"od-{s.id}", "title": "Payment Overdue",
                                   "message": f"{d['customer']} contract {d['contract_ref']} is {d['days']} days overdue",
                                   "time": d['due'], "read": True, "icon": "triangle-alert", "color": "amber", "link": d['link']})
    except Exception:
        pass
    return notifications


@csrf_exempt
def bank_notifications_api(request):
    """GET /bank/api/notifications/ - persistent per-bank data."""
    from django.http import JsonResponse
    notifications = _notifications_data(request)
    unread = sum(1 for n in notifications if not n.get('read'))
    return JsonResponse({"notifications": notifications, "unread": unread})


@csrf_exempt
def bank_notifications(request):
    """GET /bank/notifications/ - Notifications page (persistent, stored in DB)."""
    notifications = _notifications_data(request)
    unread = sum(1 for n in notifications if not n.get('read'))
    return render(request, "bank/bank_notifications.html", {"notifications": notifications, "unread": unread})


@csrf_exempt
def bank_notifications_read(request):
    """POST /bank/notifications/read/ - mark one (id) or all as read. Persisted in DB."""
    from django.contrib import messages
    from django.http import JsonResponse
    from django.shortcuts import redirect
    bu = _bank_user(request)
    if request.method == "POST" and bu is not None:
        try:
            from mortgages.models import BankNotification
            nid = request.POST.get('id')
            if nid:
                try:
                    nid = int(str(nid).replace('bn-', ''))
                    BankNotification.objects.filter(recipient=bu, id=nid).update(is_read=True)
                except (ValueError, TypeError):
                    pass
            else:
                BankNotification.objects.filter(recipient=bu, is_read=False).update(is_read=True)
        except Exception:
            pass
    wants_json = request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')
    if wants_json:
        return JsonResponse({"ok": True})
    if bu is not None:
        messages.success(request, "All notifications marked as read.")
    return redirect("bank_notifications")
