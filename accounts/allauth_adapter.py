from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.signals import pre_social_login
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.dispatch import receiver


class MorgiHomeSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter that ensures Google/social signups work with the custom
    User model (email as username, required first_name/last_name/phone_number).
    Social emails are considered verified by the provider, so we mark
    email_verified=True automatically.
    """

    def pre_social_login(self, request, sociallogin):
        """
        If a user clicks 'Sign up with Google' but an account with that email
        already exists, do not auto-connect/log them in. We detect the signup
        intent by the `next=/select-role/` parameter stored in OAuth state.
        Log out any current session and send them to the login page.
        """
        next_url = sociallogin.state.get("next") or ""
        is_signup_intent = "/select-role/" in next_url
        if is_signup_intent and sociallogin.is_existing:
            logout(request)
            response = redirect("/login/")
            response["Location"] = "/login/?social_exists=1"
            raise ImmediateHttpResponse(response)
        super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.email_verified = True
        # Fill names from Google profile data if present
        extra = sociallogin.account.extra_data
        if not user.first_name:
            user.first_name = extra.get('given_name', '')
        if not user.last_name:
            user.last_name = extra.get('family_name', '')
        if not user.phone_number:
            user.phone_number = ''
        if not user.role:
            user.role = 'customer'
        return user

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        user.email_verified = True
        if not user.phone_number:
            user.phone_number = ''
        # Default new Google users to customer; they will pick customer/realestate
        # on the /select-role/ page right after signup.
        if not user.role:
            user.role = 'customer'
        # Ensure names are persisted
        extra = sociallogin.account.extra_data
        if not user.first_name:
            user.first_name = extra.get('given_name', '')
        if not user.last_name:
            user.last_name = extra.get('family_name', '')
        user.role_selection_pending = True
        user.save(update_fields=['email_verified', 'phone_number', 'role', 'first_name', 'last_name', 'role_selection_pending'])
        return user


@receiver(pre_social_login)
def set_email_verified_on_social_login(request, sociallogin, **kwargs):
    """If an existing user logs in via Google, mark their email verified."""
    user = sociallogin.user
    if user.pk and not getattr(user, 'email_verified', False):
        user.email_verified = True
        user.save(update_fields=['email_verified'])
