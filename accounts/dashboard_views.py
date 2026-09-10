"""
Apex Dashboard - Role Views with REAL DATA from DB
- Appearance: Apex Dashboard (Shadcn) + MorgiHome colors #0077B6 / #0A2B4E - UNCHANGED
- Data: Only real DB data - user, properties, applications, contracts, transactions
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect

# Prevent back button after logout - no cache for all dashboards
class NoCacheMixin:
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # Prevent browser cache - back button should not return without login
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

class DashboardRedirectView(NoCacheMixin, TemplateView):
    """ /dashboard/ -> redirect based on role, so customer doesn't see old template (plainadmin) """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            role = getattr(request.user, 'role', 'customer')
            if role == 'customer':
                return redirect('/customer/dashboard/')
            elif role == 'seller':
                return redirect('/seller/dashboard/')
            elif role == 'bank':
                return redirect('/bank/dashboard/')
            elif role == 'realestate':
                return redirect('/realestate/dashboard/')
        return redirect('/login/')

# Helpers
def get_user_stats_placeholder():
    return {}

# ===================== COMMON PROFILE - PER ROLE (each role has its own profile) =====================
class ProfileView(NoCacheMixin, TemplateView):
    # template_name will be chosen per role - each role has its own file (customer/seller/realestate)
    # If user visits /profile/ with a role, redirect to /<role>/profile/ directly
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.path == '/profile/':
            role = getattr(request.user, 'role', '')
            if role == 'customer':
                from django.shortcuts import redirect
                return redirect('/customer/profile/')
            elif role == 'seller':
                from django.shortcuts import redirect
                return redirect('/seller/profile/')
            elif role == 'realestate':
                from django.shortcuts import redirect
                return redirect('/realestate/profile/')
            elif role == 'bank':
                from django.shortcuts import redirect
                return redirect('/bank/settings/')
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        user = self.request.user
        if user.is_authenticated:
            role = getattr(user, 'role', '')
            if role == 'customer':
                return ['customer/customer_profile.html']
            elif role == 'seller':
                return ['seller/seller_profile.html']
            elif role == 'realestate':
                return ['realestate/realestate_profile.html']
            elif role == 'bank':
                return ['bank/bank_settings.html']
        return ['profile.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx

    # Prevent cache so back button doesn't work after logout
    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

# Per-role profile aliases (for URLs /customer/profile/ etc. - each has their own)
class CustomerProfileView(ProfileView):
    def get_template_names(self):
        return ['customer/customer_profile.html']

    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        user = request.user
        if not user.is_authenticated:
            return redirect('/login/')
        # Handle profile image upload
        if 'profile_image' in request.FILES:
            img = request.FILES['profile_image']
            if img.size > 5242880:
                messages.error(request, 'Image too large.')
            else:
                user.profile_image = img
                user.save(update_fields=['profile_image'])
                messages.success(request, 'Photo updated successfully')
                return redirect('/customer/profile/')
        # Handle profile edit (first_name, last_name, phone_number)
        updated = False
        for field in ['first_name', 'last_name', 'phone_number']:
            if field in request.POST:
                val = request.POST.get(field, '').strip()
                if val and getattr(user, field) != val:
                    setattr(user, field, val)
                    updated = True
        if updated:
            user.save()
            messages.success(request, 'Profile updated successfully')
        return redirect('/customer/profile/')

class SellerProfileView(ProfileView):
    def get_template_names(self):
        return ['seller/seller_profile.html']

    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        user = request.user
        if not user.is_authenticated:
            return redirect('/login/')
        # Handle profile image upload (this was returning 405 - post didn't exist)
        if 'profile_image' in request.FILES:
            img = request.FILES['profile_image']
            if img.size > 5242880:
                messages.error(request, 'Image too large.')
            else:
                user.profile_image = img
                user.save(update_fields=['profile_image'])
                messages.success(request, 'Photo updated successfully')
                return redirect('/seller/profile/')
        updated = False
        for field in ['first_name', 'last_name', 'phone_number']:
            if field in request.POST:
                val = request.POST.get(field, '').strip()
                if val and getattr(user, field) != val:
                    setattr(user, field, val)
                    updated = True
        if updated:
            user.save()
            messages.success(request, 'Profile updated successfully')
        return redirect('/seller/profile/')

class RealEstateProfileView(ProfileView):
    def get_template_names(self):
        return ['realestate/realestate_profile.html']

    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        user = request.user
        if not user.is_authenticated:
            return redirect('/login/')
        if 'profile_image' in request.FILES:
            img = request.FILES['profile_image']
            if img.size > 5242880:
                messages.error(request, 'Image too large.')
            else:
                user.profile_image = img
                user.save(update_fields=['profile_image'])
                messages.success(request, 'Photo updated successfully')
                return redirect('/realestate/profile/')
        updated = False
        for field in ['first_name', 'last_name', 'phone_number']:
            if field in request.POST:
                val = request.POST.get(field, '').strip()
                if val and getattr(user, field) != val:
                    setattr(user, field, val)
                    updated = True
        if updated:
            user.save()
            messages.success(request, 'Profile updated successfully')
        return redirect('/realestate/profile/')
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = self.request.user
        if user.is_authenticated and user.role == 'realestate':
            ctx['my_properties_count'] = Property.objects.filter(seller=user).count()
            ctx['my_applications_count'] = MortgageApplication.objects.filter(property__seller=user).count()
            ctx['my_contracts_count'] = Contract.objects.filter(seller=user).count()
            ctx['my_pending_count'] = MortgageApplication.objects.filter(property__seller=user, status='pending').count()
        return ctx

class AdminProfileView(ProfileView):
    def get_template_names(self):
        return ['profile.html']

# ===================== CUSTOMER =====================
class CustomerDashboardView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_dashboard.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication, RepaymentSchedule
        user = self.request.user
        ctx['today'] = timezone.now()

        # Real counts
        try:
            total_props = Property.objects.filter(status='available').count()
        except: total_props = 0

        if user.is_authenticated and getattr(user, 'role', '') == 'customer':
            try:
                apps = MortgageApplication.objects.filter(customer=user).exclude(status='draft')
                drafts = MortgageApplication.objects.filter(customer=user, status='draft')
                pending_qs = apps.filter(status__in=['pending','document_verification','valuation','credit_assessment'])
                # Pending card includes drafts (incomplete) as pending - where user sees his pending drafts
                ctx['stats'] = {
                    'properties': total_props,
                    'applications': apps.count() + drafts.count(),
                    'pending_applications': pending_qs.count() + drafts.count(),
                    'drafts_count': drafts.count(),
                    'pending_only': pending_qs.count(),
                    'active_mortgage': apps.filter(status__in=['approved','disbursed']).first().property.title if apps.filter(status__in=['approved','disbursed']).exists() else None,
                    'payments_paid': RepaymentSchedule.objects.filter(mortgage__customer=user, status='paid').count(),
                    'payments_total': RepaymentSchedule.objects.filter(mortgage__customer=user).count(),
                }
                # Recent includes drafts first so user sees pending drafts on dashboard
                recent_submitted = list(apps.select_related('property')[:5])
                recent_drafts = list(drafts.select_related('property')[:3])
                ctx['recent_applications'] = recent_drafts + recent_submitted
                ctx['recent_applications'] = ctx['recent_applications'][:5]
                ctx['latest_application'] = apps.order_by('-created_at').first() or drafts.order_by('-updated_at').first()
                ctx['applications_count'] = apps.count() + drafts.count()
                ctx['draft_applications'] = drafts.select_related('property')[:5]
            except:
                ctx['stats'] = {'properties': total_props, 'applications': 0, 'pending_applications': 0, 'drafts_count': 0, 'pending_only': 0, 'active_mortgage': None, 'payments_paid': 0, 'payments_total': 0}
                ctx['recent_applications'] = []
                ctx['latest_application'] = None
        else:
            ctx['stats'] = {'properties': total_props, 'applications': 0, 'pending_applications': 0, 'active_mortgage': None, 'payments_paid': 0, 'payments_total': 0}
            ctx['recent_applications'] = []
            ctx['latest_application'] = None

        try:
            ctx['recommended_properties'] = Property.objects.filter(status='available').order_by('-created_at')[:6]
        except:
            ctx['recommended_properties'] = []
        return ctx

class CustomerPropertiesView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_properties.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        q = self.request.GET.get('q','').strip()
        ptype = self.request.GET.get('property_type','')
        location = self.request.GET.get('location','')
        qs = Property.objects.filter(status='available')
        if q:
            qs = qs.filter(Q(title__icontains=q)|Q(location__icontains=q)|Q(description__icontains=q))
        if ptype:
            qs = qs.filter(property_type=ptype)
        if location:
            qs = qs.filter(location__icontains=location)
        ctx['properties'] = qs.order_by('-created_at')[:24]
        ctx['total'] = qs.count()
        ctx['query'] = q
        ctx['property_type'] = ptype
        ctx['location'] = location
        try:
            ctx['locations'] = Property.objects.values_list('location', flat=True).distinct()[:20]
        except:
            ctx['locations'] = []
        return ctx

class CustomerApplyViewApex(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_apply.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from accounts.models import User
        prop_id = self.request.GET.get('property')
        bank_param = self.request.GET.get('bank','').strip()
        mortgage_type_param = self.request.GET.get('type') or self.request.GET.get('mortgage_type')
        ctx['properties'] = Property.objects.filter(status='available').order_by('-created_at')[:100]
        # Deduplicate banks - keep one per canonical bank name (CRDB/NMB/NCBA/NBC/TCB/MWANQA)
        raw_banks = list(User.objects.filter(role='bank', is_active=True).order_by('id'))
        seen = set()
        deduped = []
        for b in raw_banks:
            raw = (b.get_full_name() or b.email).strip().lower()
            # canonical key
            if 'crdb' in raw:
                key='crdb'
            elif 'nmb' in raw:
                key='nmb'
            elif 'ncba' in raw:
                key='ncba'
            elif 'nbc' in raw:
                key='nbc'
            elif 'tcb' in raw:
                key='tcb'
            elif 'mwanqa' in raw:
                key='mwanqa'
            else:
                key=raw
            if key not in seen:
                seen.add(key)
                deduped.append(b)
        # If less than 6, ensure sample banks are included
        ctx['banks'] = deduped
        if prop_id:
            try: ctx['selected_property'] = Property.objects.get(id=prop_id)
            except: ctx['selected_property'] = None
        else:
            ctx['selected_property'] = None
        # Bank preselect - support ?bank=crdb (slug) or id
        ctx['selected_bank'] = None
        ctx['selected_bank_slug'] = bank_param
        if bank_param:
            try:
                if bank_param.isdigit():
                    ctx['selected_bank'] = User.objects.filter(id=int(bank_param), role='bank').first()
                else:
                    # slug -> search by name/email (username field was removed - email is the identifier)
                    slug = bank_param.lower()
                    for b in ctx['banks']:
                        if slug in (b.get_full_name() or '').lower() or slug in (b.email or '').lower():
                            ctx['selected_bank'] = b
                            break
            except:
                pass
        # Mortgage type label for header
        type_labels = {'residential':'Residential Mortgage','construction':'Home Construction Mortgage','renovation':'Renovation Mortgage','land':'Land Purchase Mortgage','commercial':'Commercial Property Mortgage'}
        ctx['selected_mortgage_type'] = mortgage_type_param
        ctx['selected_mortgage_label'] = type_labels.get(mortgage_type_param, mortgage_type_param.title() + ' Mortgage' if mortgage_type_param else 'Mortgage Application')
        return ctx

class CustomerApplicationsView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_applications.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        user = self.request.user
        if user.is_authenticated:
            qs = MortgageApplication.objects.filter(customer=user).exclude(status='draft').select_related('property','bank')
            q = self.request.GET.get('q','').strip()
            status_f = self.request.GET.get('status','')
            if q:
                qs = qs.filter(Q(property__title__icontains=q)|Q(loan_amount__icontains=q))
            if status_f:
                qs = qs.filter(status=status_f)
            qs = qs.order_by('-created_at')
            ctx['applications'] = list(qs)
            # Drafts - incomplete applications staying as pending when user exits
            drafts_qs = MortgageApplication.objects.filter(customer=user, status='draft').select_related('property','bank').order_by('-updated_at')
            ctx['drafts'] = list(drafts_qs)
            ctx['has_drafts'] = drafts_qs.exists()
            ctx['query'] = q
            ctx['status_filter'] = status_f
            all_qs = MortgageApplication.objects.filter(customer=user).exclude(status='draft')
            ctx['total_count'] = all_qs.count() + drafts_qs.count()
            ctx['pending_count'] = all_qs.filter(status__in=['pending','document_verification','valuation','credit_assessment']).count() + drafts_qs.count()
            ctx['approved_count'] = all_qs.filter(status='approved').count()
            ctx['disbursed_count'] = all_qs.filter(status='disbursed').count()
            ctx['status_choices'] = [c for c in MortgageApplication.STATUS_CHOICES if c[0] != 'draft']
        else:
            ctx['applications'] = []
            ctx['drafts'] = []
            ctx['has_drafts'] = False
            ctx['status_choices'] = []
            ctx['total_count'] = 0
            ctx['pending_count'] = 0
            ctx['approved_count'] = 0
            ctx['disbursed_count'] = 0
        return ctx

class CustomerTrackView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_track.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication, REVIEW_STAGE_MESSAGES
        pk = kwargs.get('id') or kwargs.get('application_id') or self.request.GET.get('id')
        if pk:
            try: app = MortgageApplication.objects.select_related('property','bank','customer').prefetch_related('timeline_events').get(id=pk)
            except: app = None
        else:
            # If no id, try to get latest for user
            user = self.request.user
            if user.is_authenticated:
                app = MortgageApplication.objects.filter(customer=user).order_by('-created_at').first()
            else:
                app = None
        ctx['application'] = app
        if app is not None:
            events = list(app.timeline_events.order_by('created_at'))
            ctx['timeline_events'] = events
            if app.status in ('approved', 'rejected', 'disbursed'):
                ctx['review_message'] = REVIEW_STAGE_MESSAGES.get(app.status, '')
            else:
                ctx['review_message'] = REVIEW_STAGE_MESSAGES.get(getattr(app, 'review_stage', 'received') or 'received', '')
            # Also expose latest event for banner
            ctx['latest_event'] = events[-1] if events else None
        else:
            ctx['timeline_events'] = []
            ctx['review_message'] = ''
            ctx['latest_event'] = None
        if app is not None:
            ctx['corrections'] = list(app.corrections.order_by('-created_at'))
            ctx['pending_corrections'] = [c for c in ctx['corrections'] if c.status == 'pending']
        else:
            ctx['corrections'] = []
            ctx['pending_corrections'] = []
        return ctx


class CustomerCorrectionRespondView(NoCacheMixin, TemplateView):
    """POST /customer/corrections/<id>/respond/ - customer answers a bank
    correction request (text and/or re-uploaded file). The bank is notified
    through the timeline and sees the response on the review page."""
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        from django.utils import timezone
        from mortgages.models import ApplicationCorrection, ApplicationTimelineEvent
        cid = kwargs.get('id')
        try:
            corr = ApplicationCorrection.objects.select_related('application').get(id=cid, application__customer=request.user)
        except ApplicationCorrection.DoesNotExist:
            messages.error(request, 'Correction request not found.')
            return redirect('/customer/applications/')
        if corr.status != 'pending':
            messages.info(request, 'Already answered.')
            return redirect(f'/customer/track/{corr.application_id}/')
        corr.response_text = request.POST.get('response_text', '').strip()[:2000]
        f = request.FILES.get('response_file')
        if f:
            if f.size > 5242880:
                messages.error(request, 'File too large.')
                return redirect(f'/customer/track/{corr.application_id}/')
            corr.response_file = f
        if not corr.response_text and not corr.response_file:
            messages.error(request, 'Write an answer first.')
            return redirect(f'/customer/track/{corr.application_id}/')
        corr.status = 'resolved'
        corr.resolved_at = timezone.now()
        corr.save()
        # DB change: new document replaces/adds to mortgage documents so bank sees it
        try:
            if corr.response_file:
                from mortgages.models import MortgageDocument
                kind_map = {'document': 'other', 'nida': 'id_passport', 'info': 'other', 'other': 'other'}
                MortgageDocument.objects.create(
                    mortgage=corr.application,
                    file=corr.response_file,
                    doc_type=kind_map.get(corr.kind, 'other'))
        except Exception:
            pass
        try:
            app_no = corr.application.application_number
        except Exception:
            app_no = f"APP-{corr.application_id}"
        ApplicationTimelineEvent.log(
            corr.application, 'note',
            title='Correction submitted',
            message=f"You answered the bank's correction request on {app_no} ({corr.target or corr.kind}). The bank will continue review.",
            user=request.user)
        try:
            from mortgages.models import BankNotification
            BankNotification.notify(
                corr.application.bank, 'Correction Submitted',
                f"{request.user.get_full_name()} answered your correction request on {app_no} ({corr.target or corr.kind}).",
                link=f"/bank/applications/{corr.application_id}/review/", icon='file-text', color='emerald')
        except Exception:
            pass
        messages.success(request, 'Response sent successfully.')
        return redirect(f'/customer/track/{corr.application_id}/')


class CustomerContractsView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_contracts.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from transactions.models import Contract
        user = self.request.user
        if user.is_authenticated:
            qs = Contract.objects.filter(customer=user).select_related('mortgage__property','seller','bank')
            ctx['contracts'] = qs.order_by('-created_at')
            ctx['executed_count'] = qs.filter(status='executed').count()
            ctx['pending_count'] = qs.filter(status='pending_signature').count()
        else:
            ctx['contracts'] = []
            ctx['executed_count'] = 0
            ctx['pending_count'] = 0
        return ctx

class CustomerVerifyPropertyView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_verify_property.html'

class CustomerBankRequirementsView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_bank_requirements.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounts.models import User
        # REAL DATA from DB - banks registered in the system (interest/fees/limits edited in bank settings)
        # Support ?bank=crdb/nmb/... (slug matched against bank name/email) or ?bank=<id>
        bank_filter = self.request.GET.get('bank','').strip()
        slug = bank_filter.lower()
        qs = User.objects.filter(role='bank', is_active=True).order_by('id')
        banks = list(qs)
        if slug:
            if slug.isdigit():
                banks = [b for b in banks if str(b.id) == slug]
            else:
                banks = [b for b in banks if slug in (b.get_full_name() or '').lower() or slug in (b.email or '').lower()]
        # Split comma/newline-separated requirements into a clean bullet list
        # so they render as points, not one cramped paragraph.
        import re as _re
        for b in banks:
            raw = (b.bank_requirements or '')
            b.req_list = [p.strip(' .') for p in _re.split(r'[,\n;]+', raw) if p.strip(' .')]
        ctx['banks'] = banks
        ctx['all_banks'] = list(qs)
        ctx['bank_filter'] = slug
        ctx['bank_filter_name'] = bank_filter
        return ctx

class CustomerNotificationsView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_notifications.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import ApplicationTimelineEvent
        from django.contrib.humanize.templatetags.humanize import naturaltime
        user = self.request.user
        items = []
        if user.is_authenticated:
            evs = ApplicationTimelineEvent.objects.filter(application__customer=user).select_related('application').order_by('-created_at')[:50]
            for ev in evs:
                try:
                    app_no = ev.application.application_number
                except Exception:
                    app_no = f"APP-{ev.application_id}"
                items.append({
                    'id': f"ev-{ev.id}",
                    'title': f"{ev.title} — {app_no}",
                    'message': ev.message,
                    'time': naturaltime(ev.created_at),
                    'read': False,
                    'icon': 'mdi-bank',
                    'app_id': ev.application_id,
                })
        ctx['notifications'] = items
        ctx['page_obj'] = None
        ctx['paginator'] = None
        ctx['is_paginated'] = False
        ctx['has_notifications'] = bool(items)
        return ctx

class CustomerSearchView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_search.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get('q', '').strip()
        ctx['query'] = q
        if not q:
            ctx['results'] = []
            ctx['total'] = 0
            return ctx
        from properties.models import Property
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        results = []
        # Properties
        for p in Property.objects.filter(Q(title__icontains=q)|Q(location__icontains=q)|Q(description__icontains=q)).order_by('-created_at')[:10]:
            results.append({'type':'Property','title':p.title,'desc':p.location + ' • TZS ' + str(p.price),'url':f'/properties/{p.id}/','icon':'mdi-home','badged':'Property'})
        # Applications (only for this user)
        if self.request.user.is_authenticated:
            for a in MortgageApplication.objects.filter(customer=self.request.user).filter(Q(property__title__icontains=q)|Q(loan_amount__icontains=q)).select_related('property')[:10]:
                results.append({'type':'Application','title':f'Application #{a.id} - {a.property.title}','desc':a.get_status_display() + ' • TZS ' + str(a.loan_amount),'url':f'/customer/track/{a.id}/','icon':'mdi-file-document','badged':'Application'})
            for c in Contract.objects.filter(customer=self.request.user).select_related('mortgage__property')[:10]:
                if q.lower() in c.mortgage.property.title.lower() or q.lower() in str(c.id):
                    results.append({'type':'Contract','title':f'Contract #CTR-{c.id} - {c.mortgage.property.title}','desc':c.get_status_display(),'url':'/customer/contracts/','icon':'mdi-file-document-box','badged':'Contract'})
        # Bank requirements static
        banks = ['CRDB Bank','NMB Bank','NCBA Bank','NBC Bank','TCB Bank','Mwanqa Hakika Bank']
        for b in banks:
            if q.lower() in b.lower():
                results.append({'type':'Bank','title':b,'desc':'Bank Requirements • Interest & fees','url':'/customer/bank-requirements/','icon':'mdi-bank','badged':'Bank'})
        # Static pages
        pages = [
            ('Dashboard','/customer/dashboard/','mdi-speedometer'),
            ('Properties','/customer/properties/','mdi-home'),
            ('Apply Mortgage','/customer/apply/','mdi-plus-circle'),
            ('My Applications','/customer/applications/','mdi-file-document'),
            ('My Contracts','/customer/contracts/','mdi-file-document-box'),
            ('Repayment Schedule','/customer/repayment/','mdi-calendar-clock'),
            ('Property Verification','/customer/verify-property/','mdi-home-search'),
            ('Bank Requirements','/customer/bank-requirements/','mdi-bank'),
            ('Profile','/customer/profile/','mdi-account'),
            ('Notifications','/customer/notifications/','mdi-bell'),
        ]
        for title, url, icon in pages:
            if q.lower() in title.lower():
                # avoid duplicates
                if not any(r['title']==title for r in results):
                    results.append({'type':'Page','title':title,'desc':url,'url':url,'icon':icon,'badged':'Page'})
        ctx['results'] = results
        ctx['total'] = len(results)
        return ctx

class CustomerRepaymentView(NoCacheMixin, TemplateView):
    template_name = 'customer/customer_repayment.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication, RepaymentSchedule
        user = self.request.user
        mortgage = None
        schedules = []
        if user.is_authenticated:
            mortgage = MortgageApplication.objects.filter(customer=user, status__in=['approved','disbursed']).select_related('property').order_by('-created_at').first()
            if mortgage:
                schedules = RepaymentSchedule.objects.filter(mortgage=mortgage).order_by('installment_number')
        ctx['mortgage'] = mortgage
        ctx['schedules'] = schedules
        if schedules:
            ctx['total_installments'] = schedules.count()
            ctx['paid_count'] = schedules.filter(status='paid').count()
            ctx['total_paid'] = schedules.filter(status='paid').aggregate(s=Sum('amount_paid'))['s'] or 0
            ctx['remaining'] = schedules.filter(status__in=['pending','overdue']).aggregate(s=Sum('amount_due'))['s'] or 0
            ctx['remaining_installments'] = schedules.filter(status__in=['pending','overdue']).count()
            ctx['next_due'] = schedules.filter(status__in=['pending','overdue']).order_by('due_date').first()
            total = schedules.count()
            paid = schedules.filter(status='paid').count()
            ctx['on_time_rate'] = round((paid/total*100) if total else 0, 1)
        else:
            ctx['total_installments'] = 0
            ctx['paid_count'] = 0
            ctx['total_paid'] = 0
            ctx['remaining'] = 0
            ctx['remaining_installments'] = 0
            ctx['next_due'] = None
            ctx['on_time_rate'] = 0
        return ctx

# ===================== SELLER =====================
class SellerDashboardView(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_dashboard.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication
        user = self.request.user
        ctx['today'] = timezone.now()
        if user.is_authenticated and user.role in ['seller','realestate']:
            qs = Property.objects.filter(seller=user)
            ctx['stats'] = {
                'total': qs.count(),
                'available': qs.filter(status='available').count(),
                'sold': qs.filter(status='sold').count(),
                'buyers': MortgageApplication.objects.filter(property__seller=user).count(),
            }
            ctx['recent_properties'] = qs.order_by('-created_at')[:4]
            ctx['interested_buyers'] = MortgageApplication.objects.filter(property__seller=user).select_related('customer','property').order_by('-created_at')[:5]
            ctx['my_properties_count'] = qs.count()
        else:
            ctx['stats'] = {'total':0,'available':0,'sold':0,'buyers':0}
            ctx['recent_properties'] = []
            ctx['interested_buyers'] = []
        return ctx

class SellerPropertiesView(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_properties.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        user = self.request.user
        if user.is_authenticated and user.role in ['seller','realestate']:
            qs = Property.objects.filter(seller=user).order_by('-created_at')
            q = self.request.GET.get('q', '').strip()
            if q:
                qs = qs.filter(Q(title__icontains=q) | Q(location__icontains=q))
            ctx['properties'] = qs
            ctx['stats'] = {
                'total': qs.count(),
                'available': qs.filter(status='available').count(),
                'sold': qs.filter(status='sold').count(),
                'pending': qs.filter(status='pending').count(),
            }
        else:
            ctx['properties'] = []
            ctx['stats'] = {'total':0,'available':0,'sold':0,'pending':0}
        return ctx

SELLER_PROPERTY_CATEGORIES = ['house', 'apartment', 'commercial', 'plot']
SELLER_BUILDING_TYPES = ['house', 'apartment', 'townhouse', 'villa', 'bungalow', 'duplex', 'commercial']

MAX_PROPERTY_IMAGES = 5
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB each


def _validate_property_images(files_list, existing_count=0):
    """Returns (ok, error_msg). Max 5 total, each <=2MB."""
    total = existing_count + len(files_list)
    if total > MAX_PROPERTY_IMAGES:
        return False, "Maximum 5 photos allowed."
    for f in files_list:
        if getattr(f, 'size', 0) > MAX_IMAGE_SIZE:
            return False, f"Photo '{getattr(f, 'name', 'file')}' exceeds 2MB."
    return True, ""

class SellerAddPropertyViewApex(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_add_property.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # category from query param ?category=house/apartment/commercial/plot, default house
        cat = self.request.GET.get('category', 'house')
        ctx['category'] = cat if cat in SELLER_PROPERTY_CATEGORIES else 'house'
        return ctx

    def post(self, request, *args, **kwargs):
        from properties.models import Property, PropertyImage
        from django.shortcuts import redirect
        from django.contrib import messages
        user = request.user
        if not user.is_authenticated or user.role not in ['seller', 'realestate']:
            messages.error(request, "Login as seller first.")
            return redirect('/login/')
        data = request.POST
        files = request.FILES
        category = data.get('property_category', 'house')
        if category not in ['house', 'plot']:
            category = 'house'
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        price = data.get('price') or 0
        location = data.get('location', '').strip()
        area = data.get('area') or 0
        if not title or not description or not location:
            messages.error(request, "Title, description and location required.")
            return redirect(f'/seller/properties/add/?category={category}')
        # Validate photos: max 5, each <=2MB
        new_images = list(files.getlist('images'))
        ok, err = _validate_property_images(new_images, existing_count=0)
        if not ok:
            messages.error(request, err)
            return redirect(f'/seller/properties/add/?category={category}')
        try:
            prop = Property.objects.create(
                title=title,
                description=description,
                price=price,
                location=location,
                area=area or 0,
                property_category=category,
                property_type=(data.get('property_type') if data.get('property_type') in SELLER_BUILDING_TYPES else 'house') if category == 'house' else 'land',
                status=data.get('status', 'available'),
                seller=user,
                # House
                bedrooms=data.get('bedrooms') or 0,
                bathrooms=data.get('bathrooms') or 0,
                floor_number=data.get('floor_number') or None,
                total_floors=data.get('total_floors') or None,
                parking=data.get('parking') or 0,
                furnished=data.get('furnished', ''),
                security=bool(data.get('security')),
                swimming_pool=bool(data.get('swimming_pool')),
                garden=bool(data.get('garden')),
                balcony=bool(data.get('balcony')),
                elevator=bool(data.get('elevator')),
                air_conditioning=bool(data.get('air_conditioning')),
                backup_generator=bool(data.get('backup_generator')),
                year_built=data.get('year_built') or None,
                property_condition=data.get('property_condition', ''),
                property_size=data.get('property_size') or None,
                land_size=data.get('land_size') or None,
                # Plot
                land_type=data.get('land_type', ''),
                plot_dimensions=data.get('plot_dimensions', ''),
                land_use=data.get('land_use', ''),
                infrastructure_road=bool(data.get('infrastructure_road')),
                infrastructure_electricity=bool(data.get('infrastructure_electricity')),
                infrastructure_water=bool(data.get('infrastructure_water')),
                infrastructure_sewage=bool(data.get('infrastructure_sewage')),
                infrastructure_internet=bool(data.get('infrastructure_internet')),
                infrastructure_fenced=bool(data.get('infrastructure_fenced')),
                title_deed_available=data.get('title_deed_available', ''),
                survey_plan_available=data.get('survey_plan_available', ''),
                zoning=data.get('zoning', ''),
                napa=data.get('napa', ''),
            )
            if 'image' in files:
                prop.image = files['image']
                prop.save()
            try:
                cover_idx = int(data.get('cover_index', '0') or 0)
            except (ValueError, TypeError):
                cover_idx = 0
            for i, f in enumerate(new_images):
                PropertyImage.objects.create(property=prop, image=f, is_cover=(i == cover_idx))
            for field in ['title_deed_file', 'survey_plan_file', 'tax_clearance_file', 'land_certificate_file', 'building_permit_file']:
                if field in files:
                    setattr(prop, field, files[field])
            prop.save()
            messages.success(request, "Property added successfully.")
            return redirect('/seller/properties/')
        except Exception as e:
            import traceback; traceback.print_exc()
            messages.error(request, "Failed to save property.")
            return redirect(f'/seller/properties/add/?category={category}')

class SellerEditPropertyView(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_edit_property.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        pk = kwargs.get('id')
        prop = get_object_or_404(Property, id=pk)
        ctx['property'] = prop
        # Default display: plot -> plot; building -> apartment/commercial/house based on property_type
        if (prop.property_category or 'house') == 'plot':
            default_cat = 'plot'
        elif (prop.property_type or '') == 'apartment':
            default_cat = 'apartment'
        elif (prop.property_type or '') == 'commercial':
            default_cat = 'commercial'
        else:
            default_cat = 'house'
        # Allow switching form view via ?category=
        cat = self.request.GET.get('category', default_cat)
        ctx['category'] = cat if cat in SELLER_PROPERTY_CATEGORIES else default_cat
        return ctx

    def post(self, request, *args, **kwargs):
        from properties.models import PropertyImage
        from django.shortcuts import redirect
        from django.contrib import messages
        from properties.models import Property
        user = request.user
        prop = get_object_or_404(Property, id=kwargs.get('id'))
        if not user.is_authenticated or prop.seller != user:
            messages.error(request, "You can only edit your properties.")
            return redirect('/seller/properties/')
        data = request.POST
        files = request.FILES
        category = data.get('property_category', prop.property_category or 'house')
        if category not in ['house', 'plot']:
            category = 'house'
        new_images = list(files.getlist('images'))
        try:
            existing_count = prop.gallery.count()
        except Exception:
            existing_count = 0
        ok, err = _validate_property_images(new_images, existing_count=existing_count)
        if not ok:
            messages.error(request, err)
            return redirect(f'/seller/properties/edit/{prop.id}/?category={category}')
        try:
            # Common
            prop.title = data.get('title', prop.title).strip() or prop.title
            prop.description = data.get('description', prop.description).strip() or prop.description
            prop.price = data.get('price') or prop.price
            prop.location = data.get('location', prop.location).strip() or prop.location
            prop.area = data.get('area') or prop.area
            prop.property_category = category
            if category == 'house':
                if data.get('property_type') in SELLER_BUILDING_TYPES:
                    prop.property_type = data.get('property_type')
            else:
                prop.property_type = 'land'
            prop.status = data.get('status', prop.status)
            prop.napa = data.get('napa', prop.napa or '')
            if category == 'house':
                prop.bedrooms = data.get('bedrooms') or 0
                prop.bathrooms = data.get('bathrooms') or 0
                prop.floor_number = data.get('floor_number') or None
                prop.total_floors = data.get('total_floors') or None
                prop.parking = data.get('parking') or 0
                prop.furnished = data.get('furnished', '')
                prop.security = bool(data.get('security'))
                prop.swimming_pool = bool(data.get('swimming_pool'))
                prop.garden = bool(data.get('garden'))
                prop.balcony = bool(data.get('balcony'))
                prop.elevator = bool(data.get('elevator'))
                prop.air_conditioning = bool(data.get('air_conditioning'))
                prop.backup_generator = bool(data.get('backup_generator'))
                prop.year_built = data.get('year_built') or None
                prop.property_condition = data.get('property_condition', '')
                prop.property_size = data.get('property_size') or None
                prop.land_size = data.get('land_size') or None
            else:
                prop.land_type = data.get('land_type', '')
                prop.plot_dimensions = data.get('plot_dimensions', '')
                prop.land_use = data.get('land_use', '')
                prop.infrastructure_road = bool(data.get('infrastructure_road'))
                prop.infrastructure_electricity = bool(data.get('infrastructure_electricity'))
                prop.infrastructure_water = bool(data.get('infrastructure_water'))
                prop.infrastructure_sewage = bool(data.get('infrastructure_sewage'))
                prop.infrastructure_internet = bool(data.get('infrastructure_internet'))
                prop.infrastructure_fenced = bool(data.get('infrastructure_fenced'))
                prop.title_deed_available = data.get('title_deed_available', '')
                prop.survey_plan_available = data.get('survey_plan_available', '')
                prop.zoning = data.get('zoning', '')
            if 'image' in files:
                prop.image = files['image']
            cover_id = data.get('cover_image_id', '')
            try:
                cover_new_idx = int(data.get('cover_new_index', '-1') or -1)
            except (ValueError, TypeError):
                cover_new_idx = -1
            created_imgs = []
            for f in new_images:
                created_imgs.append(PropertyImage.objects.create(property=prop, image=f))
            try:
                if cover_id:
                    prop.gallery.exclude(id=cover_id).update(is_cover=False)
                    prop.gallery.filter(id=cover_id).update(is_cover=True)
                elif cover_new_idx >= 0 and cover_new_idx < len(created_imgs):
                    prop.gallery.update(is_cover=False)
                    created_imgs[cover_new_idx].is_cover = True
                    created_imgs[cover_new_idx].save(update_fields=['is_cover'])
            except Exception:
                pass
            for field in ['title_deed_file', 'survey_plan_file', 'tax_clearance_file', 'land_certificate_file', 'building_permit_file']:
                if field in files:
                    setattr(prop, field, files[field])
            prop.save()
            messages.success(request, "Property updated successfully.")
            return redirect('/seller/properties/')
        except Exception as e:
            import traceback; traceback.print_exc()
            messages.error(request, "Failed to update property.")
            return redirect(f'/seller/properties/edit/{prop.id}/?category={category}')

class SellerBuyersViewApex(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_buyers.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        user = self.request.user
        if user.is_authenticated:
            ctx['buyers'] = MortgageApplication.objects.filter(property__seller=user).select_related('customer','property').order_by('-created_at')
        else:
            ctx['buyers'] = []
        return ctx

class SellerContractsViewApex(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_contracts.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from transactions.models import Contract
        user = self.request.user
        if user.is_authenticated:
            ctx['contracts'] = Contract.objects.filter(seller=user).select_related('mortgage__property','customer','bank').order_by('-created_at')
        else:
            ctx['contracts'] = []
        return ctx

class SellerSalesView(NoCacheMixin, TemplateView):
    template_name = 'seller/seller_sales.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from transactions.models import Contract
        user = self.request.user
        if user.is_authenticated:
            qs = Contract.objects.filter(seller=user, status='executed').select_related('mortgage__property','customer')
            ctx['sales'] = qs.order_by('-executed_date','-created_at')
            total = qs.aggregate(s=Sum('mortgage__loan_amount'))['s'] or 0
            ctx['total_revenue'] = total
            ctx['avg_price'] = round(total / qs.count(), 2) if qs.count() else 0
        else:
            ctx['sales'] = []
            ctx['total_revenue'] = 0
            ctx['avg_price'] = 0
        return ctx

# ===================== REAL ESTATE =====================
class RealEstateDashboardView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_dashboard.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = self.request.user
        ctx['today'] = timezone.now()
        # RealEstate sees only its houses (My Properties), Customer sees all
        if user.is_authenticated and user.role == 'realestate':
            qs_props = Property.objects.filter(seller=user)
            qs_apps = MortgageApplication.objects.filter(property__seller=user)
            qs_contracts = Contract.objects.filter(seller=user)
            ctx['stats'] = {
                'total_properties': qs_props.count(),
                'total_applications': qs_apps.count(),
                'pending_applications': qs_apps.filter(status='pending').count(),
                'total_contracts': qs_contracts.count(),
            }
            ctx['recent_properties'] = qs_props.select_related('seller').order_by('-created_at')[:4]
            ctx['recent_applications'] = qs_apps.select_related('customer','property').order_by('-created_at')[:5]
            ctx['all_properties_count'] = qs_props.count()
        else:
            ctx['stats'] = {
                'total_properties': Property.objects.count(),
                'total_applications': MortgageApplication.objects.count(),
                'pending_applications': MortgageApplication.objects.filter(status='pending').count(),
                'total_contracts': Contract.objects.count(),
            }
            ctx['recent_properties'] = Property.objects.select_related('seller').order_by('-created_at')[:4]
            ctx['recent_applications'] = MortgageApplication.objects.select_related('customer','property').order_by('-created_at')[:5]
            ctx['all_properties_count'] = Property.objects.count()
        return ctx

class RealEstatePropertiesView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_properties.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        user = self.request.user
        q = self.request.GET.get('q','').strip()
        status_f = self.request.GET.get('status','')
        # RealEstate sees My Properties only, Customer sees all (as requested)
        if user.is_authenticated and user.role == 'realestate':
            qs = Property.objects.filter(seller=user).select_related('seller')
        else:
            qs = Property.objects.all().select_related('seller')
        if q:
            qs = qs.filter(Q(title__icontains=q)|Q(location__icontains=q))
        if status_f:
            qs = qs.filter(status=status_f)
        ctx['properties'] = qs.order_by('-created_at')[:24]
        ctx['query'] = q
        ctx['is_my_properties'] = user.is_authenticated and user.role == 'realestate'
        return ctx

class RealEstateAddPropertyView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_add_property.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounts.models import User
        ctx['sellers'] = User.objects.filter(role='seller')
        # category from query param ?category=house/plot, default house
        ctx['category'] = self.request.GET.get('category', 'house')
        return ctx

    def post(self, request, *args, **kwargs):
        from properties.models import Property, PropertyImage
        from django.shortcuts import redirect
        from django.contrib import messages
        user = request.user
        if not user.is_authenticated or user.role not in ['realestate', 'seller']:
            messages.error(request, "Login as real estate first.")
            return redirect('/realestate/properties/add/')
        data = request.POST
        files = request.FILES
        category = data.get('property_category', 'house')
        # Common
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        price = data.get('price') or 0
        location = data.get('location', '').strip()
        area = data.get('area') or 0
        # Seller selection for plot
        seller_id = data.get('seller')
        seller = user
        if seller_id and seller_id != 'self':
            from accounts.models import User
            try:
                seller = User.objects.get(id=seller_id, role='seller')
            except:
                seller = user
        new_images_re = list(files.getlist('images'))
        ok, err = _validate_property_images(new_images_re, existing_count=0)
        if not ok:
            messages.error(request, err)
            return redirect(f'/realestate/properties/add/?category={category}')
        try:
            prop = Property.objects.create(
                title=title,
                description=description,
                price=price,
                location=location,
                area=area or 0,
                property_category=category,
                property_type=data.get('property_type', 'house') if category == 'house' else 'land',
                status=data.get('status', 'available'),
                seller=seller,
                # House
                bedrooms=data.get('bedrooms') or 0,
                bathrooms=data.get('bathrooms') or 0,
                floor_number=data.get('floor_number') or None,
                total_floors=data.get('total_floors') or None,
                parking=data.get('parking') or 0,
                furnished=data.get('furnished', ''),
                security=bool(data.get('security')),
                swimming_pool=bool(data.get('swimming_pool')),
                garden=bool(data.get('garden')),
                balcony=bool(data.get('balcony')),
                elevator=bool(data.get('elevator')),
                air_conditioning=bool(data.get('air_conditioning')),
                backup_generator=bool(data.get('backup_generator')),
                year_built=data.get('year_built') or None,
                property_condition=data.get('property_condition', ''),
                property_size=data.get('property_size') or None,
                land_size=data.get('land_size') or None,
                # Plot
                land_type=data.get('land_type', ''),
                plot_dimensions=data.get('plot_dimensions', ''),
                land_use=data.get('land_use', ''),
                infrastructure_road=bool(data.get('infrastructure_road')),
                infrastructure_electricity=bool(data.get('infrastructure_electricity')),
                infrastructure_water=bool(data.get('infrastructure_water')),
                infrastructure_sewage=bool(data.get('infrastructure_sewage')),
                infrastructure_internet=bool(data.get('infrastructure_internet')),
                infrastructure_fenced=bool(data.get('infrastructure_fenced')),
                title_deed_available=data.get('title_deed_available', ''),
                survey_plan_available=data.get('survey_plan_available', ''),
                zoning=data.get('zoning', ''),
                napa=data.get('napa', ''),
            )
            # Handle cover image
            if 'image' in files:
                prop.image = files['image']
                prop.save()
            # Handle gallery images (max 5, cover selectable)
            try:
                cover_idx_re = int(data.get('cover_index', '0') or 0)
            except (ValueError, TypeError):
                cover_idx_re = 0
            for i, f in enumerate(new_images_re):
                PropertyImage.objects.create(property=prop, image=f, is_cover=(i == cover_idx_re))
            # Handle documents
            for field in ['title_deed_file','survey_plan_file','tax_clearance_file','land_certificate_file','building_permit_file']:
                if field in files:
                    setattr(prop, field, files[field])
            prop.save()
            messages.success(request, "Property added successfully.")
            return redirect('/realestate/properties/')
        except Exception as e:
            import traceback; traceback.print_exc()
            messages.error(request, "Failed to save property.")
            return redirect(f'/realestate/properties/add/?category={category}')

class RealEstateApplicationsView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_applications.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        user = self.request.user
        if user.is_authenticated and user.role == 'realestate':
            ctx['applications'] = MortgageApplication.objects.filter(property__seller=user).select_related('customer','property','bank').order_by('-created_at')[:50]
        else:
            ctx['applications'] = MortgageApplication.objects.select_related('customer','property','bank').order_by('-created_at')[:50]
        return ctx

class RealEstateContractsView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_contracts.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from transactions.models import Contract
        user = self.request.user
        if user.is_authenticated and user.role == 'realestate':
            ctx['contracts'] = Contract.objects.filter(seller=user).select_related('mortgage__property','customer','seller').order_by('-created_at')[:50]
        else:
            ctx['contracts'] = Contract.objects.select_related('mortgage__property','customer','seller').order_by('-created_at')[:50]
        return ctx

class RealEstateBuyersView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_buyers.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        user = self.request.user
        filter_type = self.request.GET.get('filter', 'all')
        if user.is_authenticated and user.role == 'realestate':
            qs = MortgageApplication.objects.filter(property__seller=user).select_related('customer','property','bank')
        else:
            qs = MortgageApplication.objects.select_related('customer','property','bank')
        if filter_type == 'interested':
            qs = qs.filter(status__in=['pending','document_verification','valuation','credit_assessment'])
        ctx['buyers'] = qs.order_by('-created_at')[:50]
        ctx['all_count'] = MortgageApplication.objects.filter(property__seller=user).count() if user.is_authenticated and user.role=='realestate' else MortgageApplication.objects.count()
        ctx['interested_count'] = MortgageApplication.objects.filter(property__seller=user, status__in=['pending','document_verification','valuation','credit_assessment']).count() if user.is_authenticated and user.role=='realestate' else 0
        ctx['filter'] = filter_type
        return ctx

class RealEstateBuyerDetailView(NoCacheMixin, TemplateView):
    """Buyer details for real-estate/seller: buyer basics (photo, name) +
    property + the bank the buyer applied through. No secret contacts
    (email/phone are never shown)."""
    template_name = 'realestate/realestate_buyer_detail.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        user = self.request.user
        pk = kwargs.get('id')
        try:
            app = MortgageApplication.objects.select_related('customer', 'property', 'bank').get(id=pk)
        except MortgageApplication.DoesNotExist:
            app = None
        if app is not None and user.is_authenticated and getattr(user, 'role', '') == 'realestate':
            if not app.property or app.property.seller_id != user.id:
                app = None
        ctx['buyer'] = app
        return ctx


class RealEstateBanksView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_banks.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from accounts.models import User
        from mortgages.models import MortgageApplication
        import re as _re
        banks = list(User.objects.filter(role='bank', is_active=True).order_by('first_name'))
        for b in banks:
            raw = (b.bank_requirements or '')
            b.req_list = [p.strip(' .') for p in _re.split(r'[,\n;]+', raw) if p.strip(' .')][:6]
            try:
                b.apps_count = MortgageApplication.objects.filter(bank=b).count()
            except Exception:
                b.apps_count = 0
        ctx['banks'] = banks
        ctx['stats'] = {
            'total': User.objects.filter(role='bank').count(),
            'active': User.objects.filter(role='bank', is_verified=True).count(),
            'applications': MortgageApplication.objects.filter(bank__role='bank').count(),
        }
        return ctx

class RealEstateReportsView(NoCacheMixin, TemplateView):
    template_name = 'realestate/realestate_reports.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        from django.db.models import Count
        user = self.request.user
        if user.is_authenticated and user.role == 'realestate':
            props = Property.objects.filter(seller=user)
            apps = MortgageApplication.objects.filter(property__seller=user)
            contracts = Contract.objects.filter(seller=user)
        else:
            props = Property.objects.all()
            apps = MortgageApplication.objects.all()
            contracts = Contract.objects.all()
        ctx['stats'] = {
            'total_properties': props.count(),
            'available': props.filter(status='available').count(),
            'sold': props.filter(status='sold').count(),
            'total_applications': apps.count(),
            'pending': apps.filter(status='pending').count(),
            'approved': apps.filter(status='approved').count(),
            'total_contracts': contracts.count(),
            'executed': contracts.filter(status='executed').count(),
        }
        # Monthly data for chart (real labels + counts)
        from django.db.models.functions import TruncMonth
        import json as _json
        try:
            monthly = list(apps.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')[:6])
            ctx['monthly_apps'] = monthly
            ctx['monthly_labels'] = _json.dumps([m['month'].strftime('%b') if m.get('month') else '' for m in monthly] or ['No data'])
            ctx['monthly_counts'] = _json.dumps([m['count'] for m in monthly] or [0])
        except Exception:
            ctx['monthly_apps'] = []
            ctx['monthly_labels'] = '["No data"]'
            ctx['monthly_counts'] = '[0]'
        return ctx

class RealEstateNotificationsView(NoCacheMixin, TemplateView):
    """Notifications za real estate - matukio halisi (tupu kama hakuna)."""
    template_name = 'realestate/realestate_notifications.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = self.request.user
        items = []
        if user.is_authenticated:
            for a in MortgageApplication.objects.filter(property__seller=user).select_related('customer', 'property').order_by('-created_at')[:5]:
                items.append({
                    'icon': 'mdi-account-plus', 'color': '#0077B6',
                    'title': 'New Application',
                    'text': f"{a.customer.get_full_name() if a.customer else '-'} applied for {a.property.title if a.property else '-'} • TZS {a.loan_amount}",
                    'date': a.created_at, 'link': '/realestate/applications/',
                })
            for c in Contract.objects.filter(seller=user).select_related('mortgage__property').order_by('-created_at')[:3]:
                items.append({
                    'icon': 'mdi-file-sign', 'color': '#00d25b',
                    'title': f"Contract #{c.id} • {c.get_status_display()}",
                    'text': f"{c.mortgage.property.title if c.mortgage and c.mortgage.property else '-'}",
                    'date': c.created_at, 'link': '/realestate/contracts/',
                })
        items.sort(key=lambda x: x['date'] or timezone.now(), reverse=True)
        ctx['notifications'] = items[:8]
        ctx['unread'] = len([i for i in MortgageApplication.objects.filter(property__seller=user, status='pending')]) if user.is_authenticated else 0
        return ctx

class RealEstateSearchView(NoCacheMixin, TemplateView):
    """Search yenye majibu halisi - properties, buyers, contracts (kila moja na link yake)."""
    template_name = 'realestate/realestate_search.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        q = self.request.GET.get('q', '').strip()
        ctx['query'] = q
        ctx['properties'] = []
        ctx['buyers'] = []
        ctx['contracts'] = []
        ctx['total'] = 0
        if not q:
            return ctx
        user = self.request.user
        is_re = user.is_authenticated and user.role == 'realestate'
        props = Property.objects.filter(seller=user) if is_re else Property.objects.all()
        ctx['properties'] = list(props.filter(Q(title__icontains=q) | Q(location__icontains=q) | Q(description__icontains=q)).order_by('-created_at')[:10])
        apps = MortgageApplication.objects.filter(property__seller=user) if is_re else MortgageApplication.objects.all()
        ctx['buyers'] = list(apps.filter(
            Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q) |
            Q(customer__email__icontains=q) | Q(property__title__icontains=q)
        ).select_related('customer', 'property').order_by('-created_at')[:10])
        cons = Contract.objects.filter(seller=user) if is_re else Contract.objects.all()
        try:
            con_q = cons.filter(Q(id=int(q)) | Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q))
        except (ValueError, TypeError):
            con_q = cons.filter(Q(customer__first_name__icontains=q) | Q(customer__last_name__icontains=q))
        ctx['contracts'] = list(con_q.select_related('mortgage__property', 'customer').order_by('-created_at')[:10])
        ctx['total'] = len(ctx['properties']) + len(ctx['buyers']) + len(ctx['contracts'])
        return ctx

class PublicPropertyDetailView(NoCacheMixin, TemplateView):
    """Public website - a visitor who isn't logged in views here /properties/<id>/ - website header/footer (not dashboard)"""
    template_name = 'property_detail_website.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        prop_id = kwargs.get('id')
        prop = get_object_or_404(Property, id=prop_id)
        user = self.request.user
        # RealEstate sees only its own, Customer sees all
        if user.is_authenticated and user.role == 'realestate' and prop.seller != user:
            ctx['not_owned'] = True
        ctx['property'] = prop
        ctx['is_owner'] = user.is_authenticated and prop.seller == user
        ctx['is_customer'] = user.is_authenticated and user.role == 'customer'
        # Choose base based on role - so sidebar displays correctly
        # Public view has no base_template (website header/footer static) - but keep for compat
        ctx['base_template'] = 'corona_base.html'
        return ctx

class PropertyDetailCoronaView(PublicPropertyDetailView):
    """Alias for backward compat - legacy /properties/<id>/ for dashboard users (seller/realestate) - corona"""
    template_name = 'property_detail_corona.html'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect(f'/login/?next={request.path}')
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'realestate':
                ctx['base_template'] = 'realestate/realestate_base.html'
            elif user.role == 'customer':
                ctx['base_template'] = 'customer/customer_base.html'
            elif user.role == 'seller':
                ctx['base_template'] = 'seller/seller_base.html'
            else:
                ctx['base_template'] = 'corona_base.html'
        return ctx

class CustomerPropertyDetailView(NoCacheMixin, TemplateView):
    """Logged-in buyer - /customer/properties/<id>/ - Corona dashboard with customer sidebar"""
    template_name = 'property_detail_corona.html'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect(f'/login/?next={request.path}')
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        from django.shortcuts import get_object_or_404
        prop_id = kwargs.get('id')
        prop = get_object_or_404(Property, id=prop_id)
        user = self.request.user
        ctx['property'] = prop
        ctx['is_owner'] = prop.seller == user
        ctx['is_customer'] = getattr(user, 'role', '') == 'customer'
        ctx['base_template'] = 'customer/customer_base.html'
        ctx['not_owned'] = False
        return ctx


class RealEstateEditPropertyView(NoCacheMixin, TemplateView):
    """Real estate edits own property with Corona template (not old template)."""
    template_name = 'realestate/realestate_edit_property.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        pk = kwargs.get('id')
        prop = get_object_or_404(Property, id=pk)
        ctx['property'] = prop
        if (prop.property_category or 'house') == 'plot':
            default_cat = 'plot'
        elif (prop.property_type or '') == 'apartment':
            default_cat = 'apartment'
        elif (prop.property_type or '') == 'commercial':
            default_cat = 'commercial'
        else:
            default_cat = 'house'
        cat = self.request.GET.get('category', default_cat)
        ctx['category'] = cat if cat in ['house', 'apartment', 'commercial', 'plot'] else default_cat
        return ctx
    def post(self, request, *args, **kwargs):
        from properties.models import Property, PropertyImage
        from django.shortcuts import redirect
        from django.contrib import messages
        user = request.user
        prop = get_object_or_404(Property, id=kwargs.get('id'))
        if not user.is_authenticated or prop.seller_id != user.id:
            messages.error(request, "You can only edit your properties.")
            return redirect('/realestate/properties/')
        data = request.POST
        files = request.FILES
        category = data.get('property_category', prop.property_category or 'house')
        if category not in ['house', 'plot']:
            category = 'house'
        new_images_re2 = list(files.getlist('images'))
        try:
            existing_count_re2 = prop.gallery.count()
        except Exception:
            existing_count_re2 = 0
        ok, err = _validate_property_images(new_images_re2, existing_count=existing_count_re2)
        if not ok:
            messages.error(request, err)
            return redirect(f'/realestate/properties/edit/{prop.id}/')
        try:
            prop.title = data.get('title', prop.title).strip() or prop.title
            prop.description = data.get('description', prop.description).strip() or prop.description
            prop.price = data.get('price') or prop.price
            prop.location = data.get('location', prop.location).strip() or prop.location
            prop.area = data.get('area') or prop.area
            prop.property_category = category
            if category == 'house':
                if data.get('property_type') in ['house', 'apartment', 'townhouse', 'villa', 'bungalow', 'duplex', 'commercial']:
                    prop.property_type = data.get('property_type')
            else:
                prop.property_type = 'land'
            if data.get('status') in [c[0] for c in Property.STATUS_CHOICES]:
                prop.status = data.get('status')
            prop.napa = data.get('napa', prop.napa or '')
            if category == 'house':
                prop.bedrooms = data.get('bedrooms') or 0
                prop.bathrooms = data.get('bathrooms') or 0
                prop.parking = data.get('parking') or 0
                prop.furnished = data.get('furnished', '')
            else:
                prop.land_type = data.get('land_type', '')
                prop.plot_dimensions = data.get('plot_dimensions', '')
            if 'image' in files:
                prop.image = files['image']
            cover_id_re = data.get('cover_image_id', '')
            try:
                cover_new_idx_re = int(data.get('cover_new_index', '-1') or -1)
            except (ValueError, TypeError):
                cover_new_idx_re = -1
            created_re = []
            for f in new_images_re2:
                created_re.append(PropertyImage.objects.create(property=prop, image=f))
            try:
                if cover_id_re:
                    prop.gallery.exclude(id=cover_id_re).update(is_cover=False)
                    prop.gallery.filter(id=cover_id_re).update(is_cover=True)
                elif cover_new_idx_re >= 0 and cover_new_idx_re < len(created_re):
                    prop.gallery.update(is_cover=False)
                    created_re[cover_new_idx_re].is_cover = True
                    created_re[cover_new_idx_re].save(update_fields=['is_cover'])
            except Exception:
                pass
            prop.save()
            messages.success(request, "Property updated successfully.")
            return redirect('/realestate/properties/')
        except Exception:
            messages.error(request, "Failed to update property.")
            return redirect(f'/realestate/properties/edit/{prop.id}/')


class SellerPropertyDetailView(NoCacheMixin, TemplateView):
    """Seller views own property inside dashboard (Corona + seller sidebar), not website."""
    template_name = 'property_detail_corona.html'
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect(f'/login/?next={request.path}')
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from properties.models import Property
        prop = get_object_or_404(Property, id=kwargs.get('id'))
        user = self.request.user
        ctx['property'] = prop
        ctx['is_owner'] = prop.seller_id == getattr(user, 'id', None)
        ctx['is_customer'] = False
        ctx['base_template'] = 'seller/seller_base.html'
        ctx['not_owned'] = False
        return ctx


class SellerNotificationsView(NoCacheMixin, TemplateView):
    """Seller notifications page - real data + mark as read."""
    template_name = 'seller/seller_notifications.html'
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = self.request.user
        items = []
        if user.is_authenticated:
            for a in MortgageApplication.objects.filter(property__seller=user).select_related('customer', 'property', 'bank').order_by('-created_at')[:20]:
                cname = a.customer.get_full_name() if a.customer else '-'
                ptitle = a.property.title if a.property else '-'
                items.append({
                    'id': f"app-{a.id}",
                    'icon': 'mdi-account-plus', 'color': '#0077B6',
                    'title': 'New Application',
                    'text': f"{cname} applied for {ptitle} • TZS {a.loan_amount}",
                    'date': a.created_at, 'link': '/seller/buyers/',
                    'read': a.status != 'pending',
                })
            for c in Contract.objects.filter(seller=user).order_by('-created_at')[:10]:
                ptitle = '-'
                try:
                    ptitle = c.mortgage.property.title if c.mortgage and c.mortgage.property else '-'
                except Exception:
                    pass
                items.append({
                    'id': f"con-{c.id}",
                    'icon': 'mdi-file-sign', 'color': '#00d25b',
                    'title': f"Contract #{c.id} • {c.get_status_display()}",
                    'text': ptitle,
                    'date': c.created_at, 'link': '/seller/contracts/',
                    'read': c.status == 'executed',
                })
            items.sort(key=lambda x: x['date'] or timezone.now(), reverse=True)
        # read state via notifications_seen_at (persisted)
        seen = getattr(user, 'notifications_seen_at', None) if user.is_authenticated else None
        if seen:
            for it in items:
                try:
                    if it['date'] and it['date'] <= seen:
                        it['read'] = True
                except Exception:
                    pass
        ctx['notifications'] = items[:30]
        ctx['unread'] = len([i for i in items if not i.get('read')])
        return ctx
    def post(self, request, *args, **kwargs):
        from django.contrib import messages
        from django.shortcuts import redirect
        user = request.user
        if user.is_authenticated:
            user.notifications_seen_at = timezone.now()
            user.save(update_fields=['notifications_seen_at'])
            messages.success(request, "All notifications marked as read.")
        return redirect('/seller/notifications/')


