from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticate using email instead of username.
    Allows login with email (case-insensitive).
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        # DRF SimpleJWT and axes may send username, we map it to email
        if email is None:
            email = kwargs.get("email") or username or kwargs.get("username")
        if email is None or password is None:
            return None
        try:
            user = UserModel.objects.get(email__iexact=email.strip())
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
