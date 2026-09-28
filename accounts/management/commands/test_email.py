from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP settings.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['email']
        self.stdout.write('Current email settings:')
        self.stdout.write(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  EMAIL_HOST_PASSWORD set: {'Yes' if settings.EMAIL_HOST_PASSWORD else 'NO'}")
        self.stdout.write('')

        if not settings.EMAIL_HOST_PASSWORD:
            self.stdout.write(self.style.ERROR(
                'EMAIL_HOST_PASSWORD is empty. Add your Gmail App Password to .env and restart the server.'
            ))
            return

        self.stdout.write(f'Attempting to send test email to {recipient}...')
        try:
            send_mail(
                subject='MorgiHome - Test Email',
                message='This is a test email from MorgiHome. If you received it, your SMTP settings are correct.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Test email sent successfully to {recipient}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send test email: {e}'))
            self.stdout.write(self.style.WARNING(
                'Common causes:\n'
                '  - EMAIL_HOST_PASSWORD is missing or wrong\n'
                '  - You are using your normal Gmail password instead of an App Password\n'
                '  - 2-Step Verification is not enabled on the Google account\n'
                '  - Less secure app access is disabled (use App Passwords instead)\n'
                'Generate an App Password at: https://myaccount.google.com/apppasswords'
            ))
