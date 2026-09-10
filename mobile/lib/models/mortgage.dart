class MortgageApplication {
  final int id;
  final String applicationNumber;
  final String loanAmount;
  final String? downPayment;
  final int repaymentPeriod;
  final String monthlyIncome;
  final String monthlyExpenses;
  final String employmentStatus;
  final String status;
  final String? mortgageType;
  final String? loanType;
  final String? affordabilityScore;
  final String? riskScore;
  final String? dtiRatio;
  final String? monthlyInstallment;
  final String? propertyTitle;
  final int? propertyId;
  final String? bankName;
  final int? bankId;
  final String createdAt;
  final String? propertyDetails;
  final String? reviewStage;
  final String? reviewMessage;
  final String? reviewNote;
  final List<TimelineEntry> timeline;

  MortgageApplication({
    required this.id,
    required this.applicationNumber,
    required this.loanAmount,
    this.downPayment,
    required this.repaymentPeriod,
    required this.monthlyIncome,
    required this.monthlyExpenses,
    required this.employmentStatus,
    required this.status,
    this.mortgageType,
    this.loanType,
    this.affordabilityScore,
    this.riskScore,
    this.dtiRatio,
    this.monthlyInstallment,
    this.propertyTitle,
    this.propertyId,
    this.bankName,
    this.bankId,
    required this.createdAt,
    this.propertyDetails,
    this.reviewStage,
    this.reviewMessage,
    this.reviewNote,
    this.timeline = const [],
  });

  factory MortgageApplication.fromJson(Map<String, dynamic> json) {
    // Handle both list and detail serializers
    final propDetails = json['property_details'] ?? json['propertyDetails'];
    String? propTitle;
    int? propId;
    if (propDetails is Map) {
      propTitle = propDetails['title'];
      propId = propDetails['id'] is int ? propDetails['id'] : int.tryParse(propDetails['id']?.toString() ?? '');
    } else {
      propTitle = json['property_title'] ?? json['propertyTitle'];
      propId = json['property'] is int ? json['property'] : int.tryParse(json['property']?.toString() ?? '');
    }

    // bank_name may be in bank_details
    String? bankName = json['bank_name'] ?? json['bankName'];
    final bankDetails = json['bank_details'];
    if (bankDetails is Map && bankDetails['name'] != null) {
      bankName = bankDetails['name'];
    }

    List<TimelineEntry> timeline = [];
    final rawTimeline = json['timeline'];
    if (rawTimeline is List) {
      timeline = rawTimeline.whereType<Map>().map((e) => TimelineEntry.fromJson(Map<String, dynamic>.from(e))).toList();
    }

    return MortgageApplication(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      applicationNumber: json['application_number'] ?? json['applicationNumber'] ?? 'APP-${json['id']}',
      loanAmount: json['loan_amount']?.toString() ?? json['loanAmount']?.toString() ?? '0',
      downPayment: json['down_payment']?.toString(),
      repaymentPeriod: json['repayment_period'] is int ? json['repayment_period'] : int.tryParse(json['repayment_period']?.toString() ?? '0') ?? 0,
      monthlyIncome: json['monthly_income']?.toString() ?? '0',
      monthlyExpenses: json['monthly_expenses']?.toString() ?? '0',
      employmentStatus: json['employment_status'] ?? '',
      status: json['status'] ?? 'pending',
      mortgageType: json['mortgage_type'],
      loanType: json['loan_type'],
      affordabilityScore: json['affordability_score']?.toString(),
      riskScore: json['risk_score']?.toString(),
      dtiRatio: json['dti_ratio']?.toString(),
      monthlyInstallment: json['monthly_installment']?.toString(),
      propertyTitle: propTitle,
      propertyId: propId,
      bankName: bankName,
      bankId: json['bank'] is int ? json['bank'] : int.tryParse(json['bank']?.toString() ?? ''),
      createdAt: json['created_at'] ?? json['createdAt'] ?? '',
      propertyDetails: propTitle,
      reviewStage: json['review_stage']?.toString(),
      reviewMessage: json['review_message']?.toString(),
      reviewNote: json['review_note']?.toString(),
      timeline: timeline,
    );
  }

  String get statusDisplay {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'document_verification':
        return 'Document Verification';
      case 'crb_check':
        return 'CRB Check';
      case 'valuation':
        return 'Valuation';
      case 'credit_assessment':
        return 'Credit Assessment';
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      case 'disbursed':
        return 'Disbursed';
      case 'draft':
        return 'Draft';
      default:
        return status;
    }
  }

  /// Live customer-facing message, same as web track page.
  String get liveReviewMessage {
    if (reviewMessage != null && reviewMessage!.isNotEmpty) return reviewMessage!;
    switch (reviewStage) {
      case 'crb_check':
        return 'Your application is under review — the bank is now at the CRB stage, checking your credit history with the Credit Reference Bureau.';
      case 'document_verification':
        return 'Your application is under review — the bank is now verifying your documents.';
      case 'valuation':
        return 'Your application is under review — the bank is now valuing the property.';
      case 'credit_assessment':
        return 'Your application is under review — the bank is now doing the final credit assessment.';
      default:
        return 'Your application has been sent directly to the bank. The bank has received it and review is starting.';
    }
  }
}

class TimelineEntry {
  final String stage;
  final String title;
  final String message;
  final String createdAt;

  TimelineEntry({required this.stage, required this.title, required this.message, required this.createdAt});

  factory TimelineEntry.fromJson(Map<String, dynamic> json) => TimelineEntry(
        stage: json['stage']?.toString() ?? '',
        title: json['title']?.toString() ?? json['stage']?.toString() ?? '',
        message: json['message']?.toString() ?? '',
        createdAt: json['created_at']?.toString() ?? '',
      );

  String get stageDisplay {
    switch (stage) {
      case 'received':
        return 'Received by Bank';
      case 'document_verification':
        return 'Document Verification';
      case 'crb_check':
        return 'CRB Check';
      case 'valuation':
        return 'Valuation';
      case 'credit_assessment':
        return 'Credit Assessment';
      case 'approval_decision':
        return 'Approval Decision';
      case 'approved':
        return 'Approved';
      case 'rejected':
        return 'Rejected';
      default:
        return stage;
    }
  }
}
