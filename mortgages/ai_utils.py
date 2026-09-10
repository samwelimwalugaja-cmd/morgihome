import math
from decimal import Decimal


def calculate_monthly_installment(loan_amount, annual_interest_rate, months):
    """
    Calculate monthly installment using the annuity formula.
    annual_interest_rate: e.g. 0.12 for 12%
    """
    monthly_rate = annual_interest_rate / 12
    if monthly_rate == 0:
        return loan_amount / months
    installment = loan_amount * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return installment


def calculate_affordability(monthly_income, monthly_expenses, monthly_installment):
    """
    Calculate borrower's repayment ability.
    Returns: affordability_score (0-100), dti_ratio
    """
    disposable_income = monthly_income - monthly_expenses
    dti_ratio = (monthly_installment / monthly_income) * 100 if monthly_income > 0 else 100

    if disposable_income <= 0:
        return 0, dti_ratio

    # Affordability = ability to pay installment
    if monthly_installment <= 0:
        return 100, dti_ratio

    ratio = (disposable_income / monthly_installment) * 100
    affordability_score = min(100, ratio)  # Max 100
    return affordability_score, dti_ratio


def calculate_risk_score(affordability_score, employment_status, credit_history='unknown'):
    """
    Calculate borrower risk.
    affordability_score: 0-100 (high = safe)
    employment_status: 'employed', 'self_employed', 'business', 'unemployed'
    """
    risk_score = 100 - affordability_score  # High affordability = low risk

    # Adjust based on employment
    employment_factors = {
        'employed': -10,
        'self_employed': 0,
        'business': 5,
        'business_owner': 5,
        'unemployed': 30,
        None: 0
    }
    risk_score += employment_factors.get(employment_status, 0)

    # Credit history factor (placeholder)
    if credit_history == 'good':
        risk_score -= 15
    elif credit_history == 'bad':
        risk_score += 25

    # Ensure risk_score is between 0 and 100
    risk_score = max(0, min(100, risk_score))
    return risk_score


def generate_repayment_schedule(mortgage):
    """
    Generate repayment schedule after mortgage is approved.
    Use bank interest if available (Step 6).
    """
    if hasattr(mortgage, 'bank') and mortgage.bank and mortgage.bank.interest_rate:
        annual_interest_rate = float(mortgage.bank.interest_rate) / 100.0
    else:
        annual_interest_rate = 0.12  # 12% interest (placeholder - will be replaced later)
    months = mortgage.repayment_period
    loan_amount = float(mortgage.loan_amount)

    monthly_installment = calculate_monthly_installment(loan_amount, annual_interest_rate, months)

    schedules = []
    balance = loan_amount

    for i in range(1, months + 1):
        interest = balance * (annual_interest_rate / 12)
        principal = monthly_installment - interest
        balance -= principal

        if balance < 0:
            balance = 0

        schedule = {
            'installment_number': i,
            'amount_due': monthly_installment,
            'balance_remaining': balance,
        }
        schedules.append(schedule)

    return schedules, monthly_installment
