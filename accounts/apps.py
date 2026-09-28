from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'
    default_auto_field = 'django.db.models.AutoField'
    verbose_name = 'Accounts'

    def ready(self):
        # Import social-account signal handlers so they are registered.
        import accounts.allauth_adapter  # noqa: F401
