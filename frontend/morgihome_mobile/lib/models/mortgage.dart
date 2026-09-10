class MortgageApplication {
  final int id;
  final int propertyId;
  final String propertyTitle;
  final double loanAmount;
  final double downPayment;
  final int repaymentPeriod;
  final double monthlyIncome;
  final double monthlyExpenses;
  final String status;
  final double? affordabilityScore;
  final double? riskScore;
  final double? monthlyInstallment;
  final double? dtiRatio;
  final DateTime createdAt;

  MortgageApplication({
    required this.id,
    required this.propertyId,
    required this.propertyTitle,
    required this.loanAmount,
    required this.downPayment,
    required this.repaymentPeriod,
    required this.monthlyIncome,
    required this.monthlyExpenses,
    required this.status,
    this.affordabilityScore,
    this.riskScore,
    this.monthlyInstallment,
    this.dtiRatio,
    required this.createdAt,
  });

  factory MortgageApplication.fromJson(Map<String, dynamic> json) {
    return MortgageApplication(
      id: json['id'],
      propertyId: json['property'] ?? 0,
      propertyTitle: json['property_details']?['title'] ?? '',
      loanAmount: (json['loan_amount'] ?? 0).toDouble(),
      downPayment: (json['down_payment'] ?? 0).toDouble(),
      repaymentPeriod: json['repayment_period'] ?? 0,
      monthlyIncome: (json['monthly_income'] ?? 0).toDouble(),
      monthlyExpenses: (json['monthly_expenses'] ?? 0).toDouble(),
      status: json['status'] ?? 'pending',
      affordabilityScore: json['affordability_score']?.toDouble(),
      riskScore: json['risk_score']?.toDouble(),
      monthlyInstallment: json['monthly_installment']?.toDouble(),
      dtiRatio: json['dti_ratio']?.toDouble(),
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
