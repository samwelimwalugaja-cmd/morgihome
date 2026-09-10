# Generated for Customer email auth - Futa username, tumia email kama USERNAME_FIELD
import accounts.managers
import django.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_nin_verification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='username',
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True, verbose_name='email address'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='last name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(max_length=15),
        ),
        migrations.AddField(
            model_name='user',
            name='interest_rate',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Interest rate % kwa bank (e.g. 12.50)', max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='processing_fee',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Processing fee TZS', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='min_loan_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Minimum loan amount TZS', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='max_loan_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Maximum loan amount TZS', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='bank_requirements',
            field=models.TextField(blank=True, help_text='Mahitaji ya bank (comma separated)', null=True),
        ),
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', accounts.managers.CustomUserManager()),
            ],
        ),
    ]
