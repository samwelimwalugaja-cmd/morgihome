/// Contract (house loans) - like web: customer/seller sees theirs, can sign.
class Contract {
  final int id;
  final String status;
  final bool customerSigned;
  final bool sellerSigned;
  final bool bankSigned;
  final String? customerName;
  final String? sellerName;
  final String? bankName;
  final String? propertyTitle;
  final String? loanAmount;
  final String? contractFile;
  final String createdAt;
  final String? signedDate;
  final String? executedDate;

  Contract({
    required this.id,
    required this.status,
    this.customerSigned = false,
    this.sellerSigned = false,
    this.bankSigned = false,
    this.customerName,
    this.sellerName,
    this.bankName,
    this.propertyTitle,
    this.loanAmount,
    this.contractFile,
    required this.createdAt,
    this.signedDate,
    this.executedDate,
  });

  String get statusDisplay {
    switch (status) {
      case 'draft':
        return 'Draft';
      case 'pending_signature':
        return 'Pending Signature';
      case 'signed':
        return 'Signed';
      case 'executed':
        return 'Executed';
      default:
        return status;
    }
  }

  static bool _b(dynamic v) => v == true || v == 1 || v == '1';

  factory Contract.fromJson(Map<String, dynamic> json) {
    String? propTitle = json['property_title']?.toString();
    String? loan;
    final mort = json['mortgage_details'] ?? json['mortgage'];
    if (mort is Map<String, dynamic>) {
      loan = mort['loan_amount']?.toString();
      final pd = mort['property_details'] ?? mort['property'];
      if (pd is Map<String, dynamic>) propTitle ??= pd['title']?.toString();
    }
    return Contract(
      id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
      status: json['status']?.toString() ?? 'draft',
      customerSigned: _b(json['customer_signed']),
      sellerSigned: _b(json['seller_signed']),
      bankSigned: _b(json['bank_signed']),
      customerName: json['customer_name']?.toString(),
      sellerName: json['seller_name']?.toString(),
      bankName: json['bank_name']?.toString(),
      propertyTitle: propTitle,
      loanAmount: loan,
      contractFile: json['contract_file']?.toString(),
      createdAt: json['created_at']?.toString() ?? '',
      signedDate: json['signed_date']?.toString(),
      executedDate: json['executed_date']?.toString(),
    );
  }
}

/// Repayment schedule entry.
class RepaymentEntry {
  final int installmentNumber;
  final String dueDate;
  final String amountDue;
  final String balanceRemaining;
  final bool isPaid;

  RepaymentEntry({
    required this.installmentNumber,
    required this.dueDate,
    required this.amountDue,
    required this.balanceRemaining,
    this.isPaid = false,
  });

  factory RepaymentEntry.fromJson(Map<String, dynamic> json) => RepaymentEntry(
        installmentNumber: json['installment_number'] is int
            ? json['installment_number']
            : int.tryParse(json['installment_number']?.toString() ?? '0') ?? 0,
        dueDate: json['due_date']?.toString() ?? '',
        amountDue: json['amount_due']?.toString() ?? '0',
        balanceRemaining: json['balance_remaining']?.toString() ?? '0',
        isPaid: json['is_paid'] == true,
      );
}

/// Bank (partner bank) - list of banks like web.
class Bank {
  final int id;
  final String name;
  final String email;
  final bool isVerified;
  final String? interestRate;
  final String? processingFee;
  final String? minLoan;
  final String? maxLoan;
  final String? requirements;

  Bank({
    required this.id,
    required this.name,
    required this.email,
    this.isVerified = false,
    this.interestRate,
    this.processingFee,
    this.minLoan,
    this.maxLoan,
    this.requirements,
  });

  factory Bank.fromJson(Map<String, dynamic> json) => Bank(
        id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
        name: json['name']?.toString() ?? json['full_name']?.toString() ?? json['email']?.toString() ?? 'Bank',
        email: json['email']?.toString() ?? '',
        isVerified: json['is_verified'] == true,
        interestRate: json['interest_rate']?.toString(),
        processingFee: json['processing_fee']?.toString(),
        minLoan: (json['min_loan_amount'] ?? json['min_loan'])?.toString(),
        maxLoan: (json['max_loan_amount'] ?? json['max_loan'])?.toString(),
        requirements: json['bank_requirements']?.toString(),
      );
}

/// Transaction - like web transactions list.
class AppTransaction {
  final int id;
  final String? referenceNumber;
  final String? amount;
  final String? status;
  final String? type;
  final String createdAt;

  AppTransaction({
    required this.id,
    this.referenceNumber,
    this.amount,
    this.status,
    this.type,
    required this.createdAt,
  });

  factory AppTransaction.fromJson(Map<String, dynamic> json) => AppTransaction(
        id: json['id'] is int ? json['id'] : int.tryParse(json['id'].toString()) ?? 0,
        referenceNumber: json['reference_number']?.toString(),
        amount: json['amount']?.toString(),
        status: json['status']?.toString(),
        type: json['transaction_type']?.toString() ?? json['type']?.toString(),
        createdAt: json['created_at']?.toString() ?? '',
      );
}
