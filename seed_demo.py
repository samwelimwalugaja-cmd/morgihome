"""
MorgiHome - Demo data seeder (DEVELOPMENT ONLY).

Inajaza DB na data halisi ya kujaribu bank portal (na portals nyingine):
customers, properties (house/apartment/plot/commercial), applications
(pending/approved/rejected/disbursed), contracts, repayment schedules,
transactions - zote zinaelekezwa kwa benki ya CRDB.

Matumizi:
    venv\\Scripts\\python.exe seed_demo.py
    venv\\Scripts\\python.exe seed_demo.py --bank crdbbank@gmail.com

Kufuta data ya demo:
    venv\\Scripts\\python.exe seed_demo.py --clean

Usikimbize production!
"""
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'morgihome_backend.settings')
django.setup()

from django.db.models import Q  # noqa: E402
from django.utils import timezone  # noqa: E402

from accounts.models import User  # noqa: E402
from mortgages.models import MortgageApplication, RepaymentSchedule  # noqa: E402
from properties.models import Property  # noqa: E402
from transactions.models import Contract, Transaction  # noqa: E402

PASSWORD = 'Demo12345'
CUSTOMER_EMAILS = ['amina.demo@morgihome.test', 'juma.demo@morgihome.test', 'zainab.demo@morgihome.test']


def get_bank(email_hint):
    bank = User.objects.filter(email__iexact=email_hint, role='bank').first()
    if bank is None:
        bank = User.objects.filter(role='bank').first()
    if bank is None:
        raise SystemExit('Hakuna bank account kwenye DB. Fungua bank account kwanza (admin au signup).')
    return bank


def clean_demo():
    """Futa data zote za demo (emails za *.demo@morgihome.test + properties zao)."""
    demo_users = list(User.objects.filter(email__endswith='.demo@morgihome.test'))
    demo_ids = [u.id for u in demo_users]
    MortgageApplication.objects.filter(customer_id__in=demo_ids).delete()
    Contract.objects.filter(customer_id__in=demo_ids).delete()
    Property.objects.filter(title__startswith='[DEMO]').delete()
    User.objects.filter(id__in=demo_ids).delete()
    print(f'Demo data imefutwa ({len(demo_ids)} users).')


def backdate(obj, days_ago):
    """Weka created_at nyuma ili chart ya miezi ionekane (auto_now_add inazungukwa)."""
    dt = timezone.now() - timedelta(days=days_ago)
    type(obj).objects.filter(id=obj.id).update(created_at=dt, updated_at=dt)
    obj.refresh_from_db()


def make_schedules(app, monthly, count=12, start_months_ago=3, paid_first=1, overdue_one=False):
    """Tengeneza ratiba: zamani kidogo ili kuwe na paid/overdue/upcoming."""
    first_due = date.today().replace(day=5) - timedelta(days=30 * start_months_ago)
    # first day of month math (rahisi)
    y, m = first_due.year, first_due.month
    balance = Decimal(app.loan_amount)
    for i in range(1, count + 1):
        due = date(y, m, 5)
        balance -= Decimal(monthly)
        if balance < 0:
            balance = Decimal(0)
        if i <= paid_first:
            st, paid = 'paid', Decimal(monthly)
        elif overdue_one and i == paid_first + 1 and due < date.today():
            st, paid = 'overdue', Decimal(0)
        else:
            st, paid = ('overdue' if due < date.today() else 'pending'), Decimal(0)
        RepaymentSchedule.objects.create(
            mortgage=app, installment_number=i, due_date=due,
            amount_due=Decimal(monthly), amount_paid=paid,
            balance_remaining=balance, status=st,
            payment_date=due if st == 'paid' else None)
        m += 1
        if m == 13:
            m = 1
            y += 1


def seed(bank_email):
    from django.contrib.auth import get_user_model
    UserModel = get_user_model()
    bank = get_bank(bank_email)
    print(f'Bank: {bank.email} ({bank.get_full_name()})')

    seller = User.objects.filter(role='seller').first()
    if seller is None:
        seller = UserModel.objects.create_user(
            email='seller.demo@morgihome.test', password=PASSWORD,
            first_name='Demo', last_name='Seller', phone_number='+255700000010', role='seller')
    customers = []
    names = [('Amina', 'Juma', '+255711000001'), ('Juma', 'Mwinyi', '+255711000002'), ('Zainab', 'Said', '+255711000003')]
    for email, (fn, ln, ph) in zip(CUSTOMER_EMAILS, names):
        u, _ = UserModel.objects.get_or_create(
            email=email, defaults={'first_name': fn, 'last_name': ln, 'phone_number': ph, 'role': 'customer'})
        if not u.check_password(PASSWORD):
            u.set_password(PASSWORD)
            u.save()
        customers.append(u)

    props = []
    props.append(Property.objects.create(
        title='[DEMO] Modern Villa Mikocheni', description='Villa ya kisasa vyumba 4, bustani na parking.',
        price=250000000, location='Mikocheni, Dar es Salaam', area=400, property_category='house',
        property_type='villa', status='available', seller=seller, bedrooms=4, bathrooms=3, parking=2,
        furnished='partially', security=True, garden=True, year_built=2021, property_condition='good',
        property_size=280, land_size=600, napa='DEMO/MK/001'))
    props.append(Property.objects.create(
        title='[DEMO] Apartment Upanga Block C', description='Apartment ghorofa ya 3, lifti na security.',
        price=145000000, location='Upanga, Dar es Salaam', area=120, property_category='house',
        property_type='apartment', status='available', seller=seller, bedrooms=3, bathrooms=2,
        floor_number=3, total_floors=8, elevator=True, security=True, furnished='yes',
        year_built=2022, property_condition='new', property_size=120))
    props.append(Property.objects.create(
        title='[DEMO] Plot Kigamboni 20x30', description='Kiwanja safi na hati, maji na umeme jirani.',
        price=80000000, location='Kigamboni, Dar es Salaam', area=600, property_category='plot',
        property_type='land', status='available', seller=seller, napa='DEMO/KIG/009',
        land_type='residential', plot_dimensions='20m x 30m', land_use='residential',
        infrastructure_road=True, infrastructure_water=True, infrastructure_electricity=True,
        title_deed_available='yes', survey_plan_available='yes', zoning='residential'))

    def make_app(cust, prop, mtype, loan, months, income, expenses, emp, status, days_ago, down=0):
        from mortgages.ai_utils import calculate_affordability, calculate_monthly_installment, calculate_risk_score
        rate = float(bank.interest_rate or 15) / 100.0
        inst = calculate_monthly_installment(float(loan), rate, months)
        aff, dti = calculate_affordability(float(income), float(expenses), inst)
        risk = calculate_risk_score(aff, emp)
        app = MortgageApplication.objects.create(
            customer=cust, property=prop, bank=bank, loan_amount=loan, down_payment=down,
            repayment_period=months, monthly_income=income, monthly_expenses=expenses,
            employment_status=emp, status=status, mortgage_type=mtype, loan_type='purchase',
            current_step=8, monthly_installment=round(inst, 2),
            affordability_score=round(aff, 2), risk_score=round(risk, 2), dti_ratio=round(dti, 2))
        backdate(app, days_ago)
        return app

    # 1) Pending (mwezi huu)
    a1 = make_app(customers[0], props[0], 'residential', 200000000, 240, 6500000, 2200000, 'employed', 'pending', 6)
    # 2) Pending (wiki iliyopita)
    a2 = make_app(customers[1], props[2], 'land', 60000000, 120, 3200000, 1100000, 'self_employed', 'pending', 12)
    # 3) Approved + schedule (miezi 2 iliyopita)
    a3 = make_app(customers[2], props[1], 'residential', 120000000, 180, 5800000, 1900000, 'employed', 'approved', 65)
    make_schedules(a3, monthly=round(float(a3.monthly_installment)), count=12, start_months_ago=2, paid_first=2)
    # 4) Rejected (mwezi uliopita)
    make_app(customers[1], props[0], 'residential', 230000000, 240, 2500000, 2100000, 'unemployed', 'rejected', 40)
    # 5) Disbursed + executed contract + transactions (miezi 3 iliyopita)
    a5 = make_app(customers[0], props[1], 'residential', 110000000, 180, 7200000, 2400000, 'business_owner', 'disbursed', 95)
    make_schedules(a5, monthly=round(float(a5.monthly_installment)), count=12, start_months_ago=3, paid_first=2, overdue_one=True)
    c5 = Contract.objects.create(mortgage=a5, customer=customers[0], seller=seller, bank=bank,
                                 status='executed', customer_signed=True, seller_signed=True, bank_signed=True,
                                 signed_date=date.today() - timedelta(days=80),
                                 executed_date=date.today() - timedelta(days=75))
    backdate(c5, 80)
    Transaction.objects.create(contract=c5, amount=round(float(a5.monthly_installment)),
                               transaction_type='installment', status='completed',
                               notes='Demo installment 1')
    Transaction.objects.create(contract=c5, amount=round(float(a5.monthly_installment)),
                               transaction_type='installment', status='completed',
                               notes='Demo installment 2')
    # 6) Pending signature contract (wiki hii)
    c6 = Contract.objects.create(mortgage=a3, customer=customers[2], seller=seller, bank=bank,
                                 status='pending_signature', customer_signed=True)
    backdate(c6, 4)

    print('Demo data imewekwa:')
    print(f'  customers: {len(customers)} (password: {PASSWORD})')
    print(f'  properties: {len(props)}')
    print(f'  applications: pending=2, approved=1, rejected=1, disbursed=1')
    print(f'  contracts: executed=1, pending_signature=1')
    print('Fungua /bank/dashboard/ ukiwa umeingia kama:', bank.email)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--bank', default='crdbbank@gmail.com')
    ap.add_argument('--clean', action='store_true')
    args = ap.parse_args()
    if args.clean:
        clean_demo()
    else:
        clean_demo()  # futa za zamani kwanza ili kuepuka duplicates
        seed(args.bank)
