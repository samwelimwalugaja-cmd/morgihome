from django.urls import path

from .views import (
    ChangePasswordView, CustomerNotificationsApiView,
    ForgotPasswordView, ForgotPasswordPhoneSendView, ForgotPasswordPhoneVerifyView,
    ForgotPasswordSecurityResetView, ForgotPasswordSecurityVerifyView,
    LoginView, LogoutView, ProfileView, RealEstateNotificationsApiView,
    RegisterView, ResendVerificationEmailView, ResetPasswordView, SellerNotificationsApiView,
)

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('forgot-password/phone/send/', ForgotPasswordPhoneSendView.as_view(), name='forgot_password_phone_send'),
    path('forgot-password/phone/verify/', ForgotPasswordPhoneVerifyView.as_view(), name='forgot_password_phone_verify'),
    path('forgot-password/security/verify/', ForgotPasswordSecurityVerifyView.as_view(), name='forgot_password_security_verify'),
    path('forgot-password/security/reset/', ForgotPasswordSecurityResetView.as_view(), name='forgot_password_security_reset'),
    path('notifications/', CustomerNotificationsApiView.as_view(), name='customer_notifications_api'),
    path('notifications/realestate/', RealEstateNotificationsApiView.as_view(), name='realestate_notifications_api'),
    path('notifications/seller/', SellerNotificationsApiView.as_view(), name='seller_notifications_api'),
]
