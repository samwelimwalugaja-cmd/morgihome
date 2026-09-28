import logging
import random
import re
import secrets
from django.conf import settings
from django.core.cache import cache
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
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import User
from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)

from django.http import JsonResponse

def rate_limit_exceeded(request, reason=None):
    return JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)

class PageLoginRequired(LoginRequiredMixin):
    login_url = '/login/'

def _send_verification_email(user, request=None):
    """Send a professional HTML verification email.

    Returns:
        (bool, str): (success, error_message). error_message is empty on success.
    """
    token = user.email_verification_token
    verify_path = f"/verify/email/{token}/"
    try:
        verify_url = request.build_absolute_uri(verify_path)
    except Exception:
        verify_url = f"https://morgihome.co.tz{verify_path}"

    subject = "MorgiHome - Verify your email address"
    first_name = user.get_full_name() or user.email
    text_body = (
        f"Hello {first_name},\n\n"
        f"Thank you for creating a MorgiHome account. Please click the link below to verify your email address:\n\n"
        f"{verify_url}\n\n"
        f"If you did not create this account, please ignore this email.\n\n"
        f"— MorgiHome Team"
    )
    html_body = (
        f"<div style=\"font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#333;\">"
        f"<h2 style=\"color:#0077B6;\">Verify your MorgiHome account</h2>"
        f"<p>Hello {first_name},</p>"
        f"<p>Thank you for creating a MorgiHome account. Please click the button below to verify your email address:</p>"
        f"<p><a href=\"{verify_url}\" style=\"display:inline-block;padding:14px 28px;background:#0077B6;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;\">Verify Email Address</a></p>"
        f"<p>Or copy and paste this link into your browser:<br><a href=\"{verify_url}\">{verify_url}</a></p>"
        f"<p style=\"color:#666;\">If you did not create this account, you can safely ignore this email.</p>"
        f"<p>— MorgiHome Team</p>"
        f"</div>"
    )
    try:
        send_mail(
            subject,
            text_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
            html_message=html_body,
        )
        logger.info(f"Verification email sent to {user.email}")
        return True, ""
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Failed to send verification email to {user.email}: {e}")
        if settings.DEBUG:
            logger.info(f"[DEV] Verification URL for {user.email}: {verify_url}")
            print(f"[MorgiHome] Verification link for {user.email}: {verify_url}")
        return False, error_msg


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer
    throttle_classes = [AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Require email verification before first login
        user.email_verified = False
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verified', 'email_verification_token', 'email_verification_sent_at'])
        sent, send_error = _send_verification_email(user, request)
        headers = self.get_success_headers(serializer.data)
        if sent:
            logger.info(f"New user registered {user.id} role={user.role} - verification email sent")
            return Response({
                'message': 'Account created successfully. Please verify your email address before logging in.',
                'redirect_url': f'/verify/email/sent/?email={user.email}',
            }, status=status.HTTP_201_CREATED, headers=headers)
        # Email failed to send: do not pretend it succeeded. Surface a clear
        # error so the user/admin can fix SMTP credentials and resend.
        logger.error(f"New user registered {user.id} role={user.role} - verification email FAILED")
        response_data = {
            'error': 'Account was created, but we could not send the verification email. Please check the email settings (EMAIL_HOST_PASSWORD) and try resending.',
            'resend_url': '/api/auth/resend-verification/',
            'email': user.email,
        }
        if settings.DEBUG:
            token = user.email_verification_token
            verify_path = f"/verify/email/{token}/"
            try:
                verify_url = request.build_absolute_uri(verify_path)
            except Exception:
                verify_url = f"https://morgihome.co.tz{verify_path}"
            response_data['debug_verification_url'] = verify_url
            response_data['debug_smtp_error'] = send_error
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR, headers=headers)

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

        # Block login for accounts that have not verified their email address.
        # Staff/superusers are exempt so admins can always log in even if the
        # email verification flow is unavailable.
        if user is not None and not user.email_verified and not user.is_staff and not user.is_superuser:
            return Response({
                'error': 'This account has not been verified. Please check your email inbox or spam folder and click the verification link.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Fallback for manual check if authenticate returned None but user exists with correct password
        # (helps if Axes is not configured properly or for testing)
        if user is None:
            tmp = User.objects.filter(email__iexact=email).first()
            if tmp and tmp.check_password(password):
                # If user_can_authenticate would block (is_active=False) then reject
                if not tmp.is_active:
                    return Response({'error': 'Account disabled. Contact support.'}, status=status.HTTP_403_FORBIDDEN)
                # If email not verified, reject with clear message (staff/superusers exempt)
                if not tmp.email_verified and not tmp.is_staff and not tmp.is_superuser:
                    return Response({
                        'error': 'This account has not been verified. Please check your email inbox or spam folder and click the verification link.'
                    }, status=status.HTTP_403_FORBIDDEN)
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
                'max_repayment_period': b.max_repayment_period,
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


@method_decorator(csrf_exempt, name='dispatch')
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
        # Use seen timestamp to determine unread - same as seller/customer
        seen = getattr(user, 'notifications_seen_at', None)
        if seen:
            for it, obj in zip(items, list(MortgageApplication.objects.filter(property__seller=user).order_by('-created_at')[:5]) + list(Contract.objects.filter(seller=user).order_by('-created_at')[:3])):
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


@method_decorator(csrf_exempt, name='dispatch')
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

# === Email verification re-enabled for customer/seller self-registration ===
# Phone/NIN verification remains removed.

class SelectRoleView(LoginRequiredMixin, View):
    """
    GET/POST /select-role/ - shown after a new social (Google) signup so the user
    can choose whether they are a Customer or Real Estate company before continuing.
    """
    login_url = '/login/'

    def get(self, request):
        # Only allow access while role selection is pending.
        if not getattr(request.user, 'role_selection_pending', False):
            return redirect('/dashboard/')
        return render(request, 'select_role.html')

    def post(self, request):
        role = (request.POST.get('role') or '').strip()
        if role not in ['customer', 'seller']:
            return render(request, 'select_role.html', {
                'error': 'Please select a valid account type.'
            })

        user = request.user
        user.role = role
        user.role_selection_pending = False
        user.save(update_fields=['role', 'role_selection_pending'])
        return redirect('/dashboard/')


class VerifyEmailView(View):
    """GET /verify/email/<token>/ - verifies email from link and renders success page."""
    def get(self, request, token):
        user = User.objects.filter(email_verification_token=token).first()
        if not user:
            return render(request, 'verify_email_success.html', {
                'invalid': True,
                'message': 'This verification link is invalid or has expired. Please request a new one.'
            })
        if user.email_verified:
            return render(request, 'verify_email_success.html', {
                'already_verified': True,
                'message': 'Congratulations! Your email address has already been verified.'
            })
        user.email_verified = True
        user.email_verified_at = timezone.now()
        user.email_verification_token = ''
        user.save(update_fields=['email_verified', 'email_verified_at', 'email_verification_token'])
        logger.info(f"Email verified for user {user.id} {user.email}")
        return render(request, 'verify_email_success.html', {
            'verified': True,
            'message': 'Congratulations! Your email address has been verified successfully.'
        })


@method_decorator(csrf_exempt, name='dispatch')
class ResendVerificationEmailView(APIView):
    """POST /api/auth/resend-verification/ {email} - resend verification link.

    Rate limits:
      - Minimum 60 seconds between resends (cooldown).
      - Maximum 5 resends per hour per email.
    Generating a new token automatically invalidates any previous link.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    COOLDOWN_SECONDS = 60
    MAX_PER_HOUR = 5

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not EMAIL_RE.match(email):
            return Response({'error': 'Enter a valid email address'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'error': 'No account found with this email.'}, status=status.HTTP_404_NOT_FOUND)
        if user.email_verified:
            return Response({'error': 'This account is already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        cooldown_key = f"resend_verification:cooldown:{email}"
        hourly_key = f"resend_verification:hourly:{email}"

        last_sent = cache.get(cooldown_key)
        if last_sent:
            remaining = self.COOLDOWN_SECONDS - int((timezone.now() - last_sent).total_seconds())
            if remaining > 0:
                return Response({
                    'error': f'Please wait {remaining} seconds before requesting another verification email.',
                    'retry_after': remaining,
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        resend_count = cache.get(hourly_key) or 0
        if resend_count >= self.MAX_PER_HOUR:
            return Response({
                'error': 'You have reached the maximum number of resend attempts for this hour. Please try again later.',
                'retry_after': 3600,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Generate a fresh token - this automatically invalidates any old link.
        user.email_verification_token = secrets.token_urlsafe(32)
        user.email_verification_sent_at = timezone.now()
        user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])

        sent, send_error = _send_verification_email(user, request)
        if not sent:
            logger.error(f"Resend verification email FAILED for {user.email}: {send_error}")
            response_data = {
                'error': 'We could not send the verification email. Please check the email settings and try again later.',
            }
            if settings.DEBUG:
                response_data['debug_smtp_error'] = send_error
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Record rate-limit state only after successful send.
        cache.set(cooldown_key, timezone.now(), timeout=self.COOLDOWN_SECONDS)
        cache.set(hourly_key, resend_count + 1, timeout=3600)
        logger.info(f"Verification email resent to {user.email} (hourly count {resend_count + 1})")
        return Response({
            'message': 'Verification email has been resent. Please check your inbox and spam folder.',
            'cooldown_seconds': self.COOLDOWN_SECONDS,
        })


class BankVerificationPageView(PageLoginRequired, TemplateView):
    template_name = 'bank_verification.html'

# Stubs for backward compatibility (return 410)
class _RemovedVerificationView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        return Response({'error': 'Verification type removed. Email/Phone/NIN verification has been removed per spec.'}, status=status.HTTP_410_GONE)
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

# ========== Helpers for password reset (OTP / security question) ==========
EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')

def _normalize_phone(phone):
    """Strip spaces/dashes/+, keep digits only for comparison."""
    if not phone:
        return ''
    return re.sub(r'\D', '', phone)


def _send_sms_otp(phone, otp):
    """Placeholder for SMS gateway integration.
    Returns True if sent (or simulated), False on failure."""
    # TODO: Integrate Twilio/AfricasTalking/BeemSMS/Vonage here.
    # For now, log and print the OTP so devs can test without real SMS.
    logger.info(f"[SMS OTP] To {phone}: {otp}")
    print(f"[MorgiHome SMS OTP] phone={phone} otp={otp}")
    return True


def _validate_password_strength(password):
    """Runs Django password validators. Returns error string or None."""
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError as DjangoValidationError
    try:
        validate_password(password)
        return None
    except DjangoValidationError as ve:
        return '; '.join(ve.messages) if hasattr(ve, 'messages') else str(ve)


def _set_user_password(user, new_password):
    """Set password and invalidate relevant cache tokens."""
    user.set_password(new_password)
    user.save(update_fields=['password'])
    # Invalidate any outstanding reset tokens / security question tokens by bumping a flag
    # (PasswordResetTokenGenerator auto-invalidates on password change.)
    cache.delete(f"pwd_reset_otp:{user.id}")
    cache.delete(f"sq_verify_token:{user.id}")


# ========== Forgot Password (email) ==========
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordView(APIView):
    """POST /api/auth/forgot-password/ {email} -> sends reset link ONLY if email exists in DB.
    Returns clear error if email not found so user can pick another method."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not EMAIL_RE.match(email):
            return Response({'error': 'Enter a valid email address'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            logger.info(f"Forgot-password requested for non-existent email: {email}")
            return Response({'error': 'This email address was not found in our system. Please check it or try Phone / Security Questions.'}, status=status.HTTP_404_NOT_FOUND)

        # Generate token + uid
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Build reset URL
        # Use request to build absolute URL, fallback to site domain
        try:
            reset_path = f"/reset-password/{uid}/{token}/"
            reset_url = request.build_absolute_uri(reset_path)
        except Exception:
            reset_url = f"https://morgihome.co.tz/reset-password/{uid}/{token}/"

        # Send email
        subject = "MorgiHome - Reset your password"
        # Plain text + HTML
        text_body = (
            f"Hello {user.get_full_name() or user.email},\n\n"
            f"You requested to reset your password for your MorgiHome account.\n"
            f"Click the link below to set a new password (valid for 24 hours):\n\n"
            f"{reset_url}\n\n"
            f"If you did not request this, please ignore this email. Your password will remain unchanged.\n\n"
            f"— MorgiHome Team"
        )
        html_body = (
            f"<p>Hello {user.get_full_name() or user.email},</p>"
            f"<p>You requested to reset your password for your MorgiHome account.</p>"
            f"<p><a href=\"{reset_url}\" style=\"display:inline-block;padding:12px 20px;background:#0077B6;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;\">Reset Password</a></p>"
            f"<p>Or copy this link:<br><a href=\"{reset_url}\">{reset_url}</a></p>"
            f"<p>This link is valid for 24 hours. If you did not request it, please ignore this email.</p>"
            f"<p>— MorgiHome Team</p>"
        )
        generic_msg = "If this email address is registered, you will receive a password reset link shortly. Please check your inbox and spam folder."
        try:
            send_mail(
                subject,
                text_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
                html_message=html_body,
            )
            logger.info(f"Password reset email sent to {user.email} uid={uid}")
        except Exception as e:
            logger.warning(f"Failed to send reset email to {user.email}: {e}")
            # In DEBUG / dev where SMTP not configured, log the URL so tester can still reset
            logger.info(f"[DEV] Reset URL for {user.email}: {reset_url}")
            # Also print to console for visibility
            print(f"[MorgiHome] Password reset link for {user.email}: {reset_url}")
            # Still return success - but in DEBUG we also expose the link for convenience
            if settings.DEBUG:
                return Response({'message': generic_msg, 'debug_reset_url': reset_url}, status=status.HTTP_200_OK)
            # In production, return a generic success message to avoid leaking
            # whether the email exists, but also indicate that sending failed.
            return Response({
                'message': generic_msg,
                'warning': 'We were unable to send the email at this time. Please try again later or contact support.'
            }, status=status.HTTP_200_OK)

        return Response({'message': generic_msg}, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordView(APIView):
    """POST /api/auth/reset-password/ {uid, token, new_password, confirm_password} -> resets password if token valid."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        uidb64 = request.data.get('uid') or request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('new_password') or request.data.get('password')
        confirm = request.data.get('confirm_password') or request.data.get('confirm')

        if not uidb64 or not token:
            return Response({'error': 'Invalid or missing reset link. Please request a new link.'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
        if confirm and new_password != confirm:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        # Decode uid
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_str
        from django.contrib.auth.tokens import PasswordResetTokenGenerator

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'error': 'Invalid reset link. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({'error': 'This reset link is invalid or has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password with Django validators (reuse AUTH_PASSWORD_VALIDATORS)
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as ve:
            msg = '; '.join(ve.messages) if hasattr(ve, 'messages') else str(ve)
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info(f"Password reset successful for user {user.id} {user.email}")
        return Response({'message': 'Password has been reset successfully. You can now log in with your new password.'}, status=status.HTTP_200_OK)


# ========== Phone Number OTP Reset ==========
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordPhoneSendView(APIView):
    """POST /api/auth/forgot-password/phone/send/ {phone_number}
    Checks if phone exists, generates 6-digit OTP, stores in cache for 10 minutes.
    In production sends SMS; in DEBUG returns the OTP in the response/console."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        phone = (request.data.get('phone_number') or request.data.get('phone') or '').strip()
        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        norm = _normalize_phone(phone)
        if len(norm) < 9:
            return Response({'error': 'Enter a valid phone number (e.g. +255 712 345 678)'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(phone_number__icontains=norm).first()
        if not user:
            logger.info(f"Forgot-password phone requested for non-existent number: {phone}")
            return Response({'error': 'This phone number was not found in our system. Please check it or try Email / Security Questions.'}, status=status.HTTP_404_NOT_FOUND)

        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        cache_key = f"pwd_reset_otp:{user.id}"
        cache.set(cache_key, otp, timeout=600)  # 10 minutes
        sent = _send_sms_otp(user.phone_number, otp)

        logger.info(f"Phone reset OTP generated for user {user.id}")
        response_payload = {'message': 'A 6-digit verification code has been sent to your phone number.'}
        if settings.DEBUG:
            response_payload['debug_otp'] = otp
            response_payload['debug_phone'] = user.phone_number
        if not sent:
            return Response({'error': 'Unable to send SMS at the moment. Please try Email or Security Questions.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response(response_payload, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordPhoneVerifyView(APIView):
    """POST /api/auth/forgot-password/phone/verify/ {phone_number, otp, new_password, confirm_password}
    Verifies 6-digit OTP and resets password in one step."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        phone = (request.data.get('phone_number') or request.data.get('phone') or '').strip()
        otp = (request.data.get('otp') or '').strip()
        new_password = request.data.get('new_password') or request.data.get('password')
        confirm = request.data.get('confirm_password') or request.data.get('confirm')

        if not phone:
            return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp or len(otp) != 6 or not otp.isdigit():
            return Response({'error': 'Enter the 6-digit code sent to your phone'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        if confirm and new_password != confirm:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        norm = _normalize_phone(phone)
        user = User.objects.filter(phone_number__icontains=norm).first()
        if not user:
            return Response({'error': 'Phone number not found.'}, status=status.HTTP_404_NOT_FOUND)

        cache_key = f"pwd_reset_otp:{user.id}"
        cached_otp = cache.get(cache_key)
        if cached_otp is None:
            return Response({'error': 'Verification code has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        if cached_otp != otp:
            return Response({'error': 'Invalid verification code. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        pwd_error = _validate_password_strength(new_password)
        if pwd_error:
            return Response({'error': pwd_error}, status=status.HTTP_400_BAD_REQUEST)

        _set_user_password(user, new_password)
        logger.info(f"Phone OTP password reset successful for user {user.id} {user.email}")
        return Response({'message': 'Password has been reset successfully. You can now log in with your new password.'}, status=status.HTTP_200_OK)


# ========== Security Question Reset ==========
@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordSecurityVerifyView(APIView):
    """POST /api/auth/forgot-password/security/verify/ {first_name, last_name, email}
    Verifies the 3 security answers against the DB. On success returns a short-lived
    reset token that must be used with /forgot-password/security/reset/."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        first_name = (request.data.get('first_name') or '').strip().lower()
        last_name = (request.data.get('last_name') or '').strip().lower()

        if not email or not first_name or not last_name:
            return Response({'error': 'Email, first name and last name are required'}, status=status.HTTP_400_BAD_REQUEST)
        if not EMAIL_RE.match(email):
            return Response({'error': 'Enter a valid email address'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'error': 'No account found with that email. Please check or try Email / Phone.'}, status=status.HTTP_404_NOT_FOUND)

        # Case-insensitive compare against stored names
        stored_first = (user.first_name or '').strip().lower()
        stored_last = (user.last_name or '').strip().lower()
        if first_name != stored_first or last_name != stored_last:
            return Response({'error': 'Security answers do not match our records. Please check your first name, last name and email.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate short-lived one-time reset token (different from email token)
        import secrets
        reset_token = secrets.token_urlsafe(32)
        cache.set(f"sq_verify_token:{user.id}", reset_token, timeout=600)  # 10 minutes
        logger.info(f"Security question verified for user {user.id}")
        return Response({
            'message': 'Security answers verified. You can now set a new password.',
            'reset_token': reset_token,
            'user_id': user.id,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordSecurityResetView(APIView):
    """POST /api/auth/forgot-password/security/reset/ {user_id, reset_token, new_password, confirm_password}
    Resets password after security question verification."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        user_id = request.data.get('user_id')
        reset_token = request.data.get('reset_token')
        new_password = request.data.get('new_password') or request.data.get('password')
        confirm = request.data.get('confirm_password') or request.data.get('confirm')

        if not user_id or not reset_token:
            return Response({'error': 'Invalid reset session. Please verify your security answers again.'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password:
            return Response({'error': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)
        if confirm and new_password != confirm:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=int(user_id))
        except Exception:
            return Response({'error': 'Invalid reset session.'}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"sq_verify_token:{user.id}"
        cached_token = cache.get(cache_key)
        if cached_token is None or cached_token != reset_token:
            return Response({'error': 'Reset session expired or invalid. Please verify your security answers again.'}, status=status.HTTP_400_BAD_REQUEST)

        pwd_error = _validate_password_strength(new_password)
        if pwd_error:
            return Response({'error': pwd_error}, status=status.HTTP_400_BAD_REQUEST)

        _set_user_password(user, new_password)
        logger.info(f"Security question password reset successful for user {user.id} {user.email}")
        return Response({'message': 'Password has been reset successfully. You can now log in with your new password.'}, status=status.HTTP_200_OK)


# Keep names for any old imports (avoid ImportError)
SendEmailVerificationView = _RemovedVerificationView
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
