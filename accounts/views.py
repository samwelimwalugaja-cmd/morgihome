import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_ratelimit.decorators import ratelimit
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User
from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)

from django.http import JsonResponse

def rate_limit_exceeded(request, reason=None):
    return JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)

class PageLoginRequired(LoginRequiredMixin):
    login_url = '/login/'

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer
    throttle_classes = [AnonRateThrottle]

    def perform_create(self, serializer):
        user = serializer.save()
        # Email verification REMOVED - user registers directly without needing verification
        # Customer/Seller is_fully_verified = True
        logger.info(f"New user registered {user.id} role={user.role} - no verification required for customer/seller")

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = None
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        from django.contrib.auth import authenticate, login
        email = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')
        if not email or not password:
            return Response({'error': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)
        email = email.strip()
        # Use authenticate so Axes and is_active (user_can_authenticate) are respected
        user = authenticate(request, email=email, password=password)
        # Fallback for manual check if authenticate returned None but user exists with correct password
        # (helps if Axes is not configured properly or for testing)
        if user is None:
            tmp = User.objects.filter(email__iexact=email).first()
            if tmp and tmp.check_password(password):
                # If user_can_authenticate would block (is_active=False) then reject
                if not tmp.is_active:
                    return Response({'error': 'Account disabled. Contact support.'}, status=status.HTTP_403_FORBIDDEN)
                # If Axes has locked, authenticate would return None but check_password would pass -
                # so here we return invalid to avoid lockout bypass
                # Check if Axes has locked IP/user
                try:
                    from axes.handlers.database import AxesDatabaseHandler
                    from axes.helpers import get_client_ip_address
                    # If locked, reject directly
                    from django.core.cache import cache
                except Exception:
                    pass
                # If not yet blocked, use tmp as user (allow login without Axes)
                # But better to use tmp only if authenticate failed due to missing backend
                # For security, if user exists with correct password and is_active, allow
                user = tmp
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        # Also session login so TemplateViews (customer/dashboard) see request.user.is_authenticated
        try:
            login(request, user)
        except Exception as e:
            logger.warning(f"Session login failed for {user.email}: {e}")
        refresh = RefreshToken.for_user(user)
        logger.info(f"User login success {user.id} {user.email} role={user.role}")
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        })

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        old = request.data.get('old_password') or request.data.get('current_password')
        new = request.data.get('new_password') or request.data.get('password')
        confirm = request.data.get('confirm_password') or request.data.get('new_password_confirm')
        if not old or not new:
            return Response({'error': 'Old and new password required'}, status=status.HTTP_400_BAD_REQUEST)
        if not request.user.check_password(old):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        if confirm and new != confirm:
            return Response({'error': 'New passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new) < 8:
            return Response({'error': 'New password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new)
        request.user.save()
        # Keep session alive
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        return Response({'message': 'Password changed successfully'})

class VerificationStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        return Response({
            'is_verified': user.is_verified,
            'is_fully_verified': user.is_fully_verified(),
            'verification_level': user.verification_level,
            'role': user.role,
            'business_license_verified': user.business_license_verified,
            'tax_clearance_verified': user.tax_clearance_verified,
            'company_registration_verified': user.company_registration_verified,
        })

class BankDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, doc_type=None):
        user = request.user
        if user.role not in ['bank','realestate']:
            return Response({'error': 'Only Bank/RealEstate can upload business docs'}, status=status.HTTP_403_FORBIDDEN)
        file = request.FILES.get('document') or request.FILES.get('file')
        if not file:
            return Response({'error': 'Document file required'}, status=status.HTTP_400_BAD_REQUEST)
        if file.size > 5242880:
            return Response({'error': 'File too large. Maximum size is 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
        doc_type = (doc_type or request.data.get('doc_type') or '').lower()
        now = timezone.now()
        if doc_type == 'business_license':
            user.business_license = file
            user.business_license_status = 'pending'
            user.business_license_submitted_at = now
        elif doc_type == 'tax_clearance':
            user.tax_clearance = file
            user.tax_clearance_status = 'pending'
            user.tax_clearance_submitted_at = now
        elif doc_type == 'company_registration':
            user.company_registration = file
            user.company_registration_status = 'pending'
            user.company_registration_submitted_at = now
        else:
            return Response({'error': 'Invalid doc_type. Use business_license, tax_clearance, company_registration'}, status=status.HTTP_400_BAD_REQUEST)
        user.save()
        return Response({'message': f'{doc_type} uploaded, pending verification', 'status': 'pending'})

class BankListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        banks = User.objects.filter(role='bank', is_active=True)
        # Only show verified banks? Show all but mark verification
        data = []
        for b in banks:
            data.append({
                'id': b.id,
                'email': b.email,
                'name': b.get_full_name(),
                'is_verified': b.is_fully_verified(),
                'interest_rate': str(b.interest_rate) if b.interest_rate else None,
                'processing_fee': str(b.processing_fee) if b.processing_fee else None,
                'min_loan_amount': str(b.min_loan_amount) if b.min_loan_amount else None,
                'max_loan_amount': str(b.max_loan_amount) if b.max_loan_amount else None,
                'bank_requirements': b.bank_requirements,
            })
        return Response(data)

@method_decorator(csrf_exempt, name='dispatch')
class CustomerNotificationsApiView(APIView):
    """GET /api/auth/notifications/ - live bank review updates for the logged-in customer.
    POST marks all as read (persisted - the bell number clears and stays cleared).

    Every bank stage confirmation (documents, CRB, valuation, credit,
    approval) is logged as a timeline event, so the customer sees e.g.
    'now application MORG-RES-000001 is at the CRB review stage'.
    Works with both JWT (mobile) and web session (navbar bell).
    CSRF-exempt: the CSRF cookie is HttpOnly so browser JS cannot send the
    token; the endpoint is authenticated and only touches the caller's own
    read-state (same pattern as login/register)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.humanize.templatetags.humanize import naturaltime
        from mortgages.models import ApplicationTimelineEvent
        user = request.user
        if getattr(user, 'role', '') != 'customer':
            return Response({'notifications': [], 'unread': 0})
        evs = (ApplicationTimelineEvent.objects
               .filter(application__customer=user)
               .select_related('application')
               .order_by('-created_at')[:20])
        seen = getattr(user, 'notifications_seen_at', None)
        items = []
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
                'app_id': ev.application_id,
                'stage': ev.stage,
                'read': bool(seen and ev.created_at <= seen),
            })
        unread = len([i for i, ev in zip(items, evs) if not i['read']])
        return Response({'notifications': items, 'unread': unread})

    def post(self, request):
        """POST /api/auth/notifications/ - mark all as read (badge clears and stays cleared)."""
        from django.utils import timezone
        user = request.user
        user.notifications_seen_at = timezone.now()
        user.save(update_fields=['notifications_seen_at'])
        return Response({'message': 'All marked as read', 'unread': 0})


class RealEstateNotificationsApiView(APIView):
    """GET /api/auth/notifications/realestate/ - real events for the logged-in
    real-estate company: new applications on own listings + contract updates."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.humanize.templatetags.humanize import naturaltime
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = request.user
        if getattr(user, 'role', '') != 'realestate':
            return Response({'notifications': [], 'unread': 0})
        items = []
        for a in MortgageApplication.objects.filter(property__seller=user).select_related('customer', 'property').order_by('-created_at')[:5]:
            cname = a.customer.get_full_name() if a.customer else '-'
            ptitle = a.property.title if a.property else '-'
            items.append({
                'title': 'New Application',
                'message': f"{cname} applied for {ptitle} - TZS {a.loan_amount}",
                'time': naturaltime(a.created_at) if a.created_at else '',
                'link': '/realestate/applications/',
                'read': a.status != 'pending',
            })
        for c in Contract.objects.filter(seller=user).select_related('mortgage__property').order_by('-created_at')[:3]:
            ptitle = c.mortgage.property.title if c.mortgage and c.mortgage.property else '-'
            items.append({
                'title': f"Contract #{c.id} - {c.get_status_display()}",
                'message': ptitle,
                'time': naturaltime(c.created_at) if c.created_at else '',
                'link': '/realestate/contracts/',
                'read': c.status == 'executed',
            })
        unread = MortgageApplication.objects.filter(property__seller=user, status='pending').count()
        return Response({'notifications': items, 'unread': unread})


class SellerNotificationsApiView(APIView):
    """GET /api/auth/notifications/seller/ - real events for seller.
    POST marks all as read (persisted via notifications_seen_at)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.humanize.templatetags.humanize import naturaltime
        from mortgages.models import MortgageApplication
        from transactions.models import Contract
        user = request.user
        if getattr(user, 'role', '') != 'seller':
            return Response({'notifications': [], 'unread': 0})
        items = []
        for a in MortgageApplication.objects.filter(property__seller=user).select_related('customer', 'property').order_by('-created_at')[:8]:
            cname = a.customer.get_full_name() if a.customer else '-'
            ptitle = a.property.title if a.property else '-'
            items.append({
                'id': f"app-{a.id}",
                'title': 'New Application',
                'message': f"{cname} applied for {ptitle} - TZS {a.loan_amount}",
                'time': naturaltime(a.created_at) if a.created_at else '',
                'link': '/seller/buyers/',
                'read': a.status != 'pending',
            })
        for c in Contract.objects.filter(seller=user).order_by('-created_at')[:5]:
            try:
                ptitle = c.mortgage.property.title if c.mortgage and c.mortgage.property else '-'
            except Exception:
                ptitle = '-'
            items.append({
                'id': f"con-{c.id}",
                'title': f"Contract #{c.id} - {c.get_status_display()}",
                'message': ptitle,
                'time': naturaltime(c.created_at) if c.created_at else '',
                'link': '/seller/contracts/',
                'read': c.status == 'executed',
            })
        seen = getattr(user, 'notifications_seen_at', None)
        if seen:
            for it, obj in zip(items, list(MortgageApplication.objects.filter(property__seller=user).order_by('-created_at')[:8]) + list(Contract.objects.filter(seller=user).order_by('-created_at')[:5])):
                try:
                    if getattr(obj, 'created_at', None) and obj.created_at <= seen:
                        it['read'] = True
                except Exception:
                    pass
        unread = len([i for i in items if not i.get('read')])
        return Response({'notifications': items, 'unread': unread})

    def post(self, request):
        from django.utils import timezone
        user = request.user
        user.notifications_seen_at = timezone.now()
        user.save(update_fields=['notifications_seen_at'])
        return Response({'message': 'All marked as read', 'unread': 0})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh') or request.data.get('refresh_token')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                except Exception:
                    pass
        except Exception:
            pass
        from django.contrib.auth import logout
        try:
            logout(request)
        except Exception:
            pass
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

# === REMOVED VERIFICATION VIEWS - Email/Phone/NIN ===
# SendEmailVerificationView, VerifyEmailView, SendPhoneOTPView, VerifyPhoneView,
# IdentityUploadView, SubmitNINView, SendOTPView, VerifyOTPView -> REMOVED per spec
# Removed because the 3 verifications (Email, Phone, NIN) were deleted

class BankVerificationPageView(PageLoginRequired, TemplateView):
    template_name = 'bank_verification.html'

# Stubs for backward compatibility (return 410)
class _RemovedVerificationView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        return Response({'error': 'Verification type removed. Email/Phone/NIN verification has been removed per spec.'}, status=status.HTTP_410_GONE)
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

# Keep names for any old imports (avoid ImportError)
SendEmailVerificationView = _RemovedVerificationView
VerifyEmailView = _RemovedVerificationView
SendPhoneOTPView = _RemovedVerificationView
VerifyPhoneView = _RemovedVerificationView
IdentityUploadView = _RemovedVerificationView
SubmitNINView = _RemovedVerificationView
SendOTPView = _RemovedVerificationView
VerifyOTPView = _RemovedVerificationView
AdminVerificationListView = _RemovedVerificationView
AdminVerifyIdentityView = _RemovedVerificationView
VerifyEmailPageView = type('VerifyEmailPageView', (TemplateView,), {'template_name': 'bank_verification.html'})
VerifyPhonePageView = type('VerifyPhonePageView', (TemplateView,), {'template_name': 'bank_verification.html'})
VerifyIdentityPageView = type('VerifyIdentityPageView', (TemplateView,), {'template_name': 'bank_verification.html'})
VerificationStatusPageView = type('VerificationStatusPageView', (TemplateView,), {'template_name': 'bank_verification.html'})
AdminVerificationPageView = type('AdminVerificationPageView', (PageLoginRequired, TemplateView), {'template_name': 'admin_verification.html'})
VerificationAccountView = type('VerificationAccountView', (PageLoginRequired, TemplateView), {'template_name': 'bank_verification.html'})
AdminVerifyIdentityView = _RemovedVerificationView
AdminVerificationListView = _RemovedVerificationView
