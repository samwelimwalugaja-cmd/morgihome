import os
from django.db import migrations


def create_google_social_app(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    SocialApp = apps.get_model('socialaccount', 'SocialApp')

    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

    if not client_id or not secret:
        return

    # Update the default site domain/name
    site, _ = Site.objects.update_or_create(
        pk=1,
        defaults={
            'domain': os.getenv('SITE_DOMAIN', 'morgihome.co.tz'),
            'name': os.getenv('SITE_NAME', 'MorgiHome'),
        },
    )

    app, created = SocialApp.objects.update_or_create(
        provider='google',
        defaults={
            'name': 'MorgiHome Google',
            'client_id': client_id,
            'secret': secret,
            'key': '',
        },
    )
    app.sites.add(site)


def remove_google_social_app(apps, schema_editor):
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    SocialApp.objects.filter(provider='google', name='MorgiHome Google').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('socialaccount', '0006_alter_socialaccount_extra_data'),
        ('accounts', '0013_user_email_verification_sent_at_and_more'),
    ]

    operations = [
        migrations.RunPython(create_google_social_app, remove_google_social_app),
    ]
