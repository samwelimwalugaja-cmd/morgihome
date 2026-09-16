# Generated for deductions (PSSSF 5%, HESLB 15%, PAYE 0-30%) and other loan consolidation
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mortgages', '0008_add_customer_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mortgageapplication',
            name='employment_sector',
            field=models.CharField(blank=True, choices=[('public', 'Sekta ya Umma (Public)'), ('private', 'Sekta Binafsi (Private)')], help_text='Public vs Private sector - PSSSF 5% applies only to public', max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='deduction_psssf',
            field=models.BooleanField(default=False, help_text='PSSSF 5% ya mshahara - kwa wafanyakazi wa sekta ya umma tu'),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='deduction_heslb',
            field=models.BooleanField(default=False, help_text='HESLB 15% ya mshahara - kwa mwenye deni la elimu'),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='deduction_paye',
            field=models.BooleanField(default=False, help_text='PAYE 0-30% kulingana na kipato'),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='psssf_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Computed PSSSF 5%', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='heslb_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Computed HESLB 15%', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='paye_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Computed PAYE per bracket', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='total_deductions',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Jumla ya makato', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='net_monthly_income',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Kipato halisi baada ya makato', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='has_other_loan',
            field=models.CharField(blank=True, choices=[('yes', 'Yes - Ndiyo'), ('no', 'No - Hapana')], help_text='Je, una mkopo mwingine benki nyingine?', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='other_loan_bank',
            field=models.CharField(blank=True, help_text='Jina la benki ya mkopo wa zamani', max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='other_loan_amount',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Kiasi cha mkopo wa zamani', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='other_loan_balance',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Deni lililobaki', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='other_loan_monthly_payment',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Malipo ya kila mwezi ya mkopo wa zamani', max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='other_loan_consolidate',
            field=models.CharField(blank=True, choices=[('yes', 'Yes - Ijumuishwe'), ('no', 'No - Tofauti')], help_text='Je, ujumuishe mkopo wa zamani kwenye mkopo huu? (Takeover/Consolidation)', max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='has_existing_loan',
            field=models.CharField(blank=True, choices=[('yes', 'Yes'), ('no', 'No')], max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='existing_loan_bank',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='existing_loan_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='existing_loan_repayment',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
        migrations.AddField(
            model_name='mortgageapplication',
            name='existing_loan_balance',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True),
        ),
    ]
