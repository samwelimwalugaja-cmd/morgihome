import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class MortgageApplicationScreen extends StatefulWidget {
  final Property property;
  final String? initialMortgageType;
  final int? initialBankId;

  const MortgageApplicationScreen({super.key, required this.property, this.initialMortgageType, this.initialBankId});

  @override
  State<MortgageApplicationScreen> createState() => _MortgageApplicationScreenState();
}

class _MortgageApplicationScreenState extends State<MortgageApplicationScreen> {
  int _current = 0; // 0-7
  String _customerType = '';
  String _mortgageType = 'residential';
  bool _isLoading = false;
  bool _hasAttemptedNext = false;
  Map<String, dynamic>? _aiResult;
  List<Map<String, dynamic>> _banks = [];
  int? _selectedBankId;

  // Controllers
  final _dobCtrl = TextEditingController();
  String _gender = '';
  String _marital = '';
  final _dependentsCtrl = TextEditingController();
  String _employmentStatus = 'employed';
  final _employerCtrl = TextEditingController();
  final _jobCtrl = TextEditingController();
  final _yearsEmployedCtrl = TextEditingController();
  final _monthlyIncomeCtrl = TextEditingController();
  final _monthlyExpensesCtrl = TextEditingController();
  // business
  final _bizNameCtrl = TextEditingController();
  final _bizRegCtrl = TextEditingController();
  String _bizType = '';
  final _bizYearsCtrl = TextEditingController();
  final _bizIncomeCtrl = TextEditingController();
  final _bizExpensesCtrl = TextEditingController();
  // loan
  String _loanType = 'purchase';
  final _loanAmountCtrl = TextEditingController();
  final _downPaymentCtrl = TextEditingController();
  String _repaymentPeriod = '180';
  String get _mortgageTypeLabel {
    const m = {
      'residential': 'Residential Mortgage',
      'construction': 'Home Construction',
      'renovation': 'Renovation Mortgage',
      'land': 'Land Purchase',
      'commercial': 'Commercial Property',
    };
    return m[_mortgageType] ?? _mortgageType;
  }

  @override
  void initState() {
    super.initState();
    _mortgageType = widget.initialMortgageType ?? 'residential';
    _selectedBankId = widget.initialBankId;
    _loadBanks();
    _loadDraft();
  }

  Future<void> _loadBanks() async {
    try {
      final banks = await ApiService().getBanks();
      if (!mounted) return;
      setState(() => _banks = banks);
      if (_selectedBankId != null && _banks.isEmpty) {}
    } catch (_) {}
  }

  String _draftKey() {
    return 'mobile_draft_${_mortgageType}_${widget.property.id}';
  }

  Future<void> _saveDraftLocal() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final data = {
        'customer_type': _customerType,
        'mortgage_type': _mortgageType,
        'dob': _dobCtrl.text,
        'gender': _gender,
        'marital': _marital,
        'dependents': _dependentsCtrl.text,
        'employment_status': _employmentStatus,
        'employer': _employerCtrl.text,
        'job': _jobCtrl.text,
        'years_employed': _yearsEmployedCtrl.text,
        'monthly_income': _monthlyIncomeCtrl.text,
        'monthly_expenses': _monthlyExpensesCtrl.text,
        'biz_name': _bizNameCtrl.text,
        'biz_reg': _bizRegCtrl.text,
        'biz_type': _bizType,
        'biz_years': _bizYearsCtrl.text,
        'biz_income': _bizIncomeCtrl.text,
        'biz_expenses': _bizExpensesCtrl.text,
        'loan_type': _loanType,
        'loan_amount': _loanAmountCtrl.text,
        'down_payment': _downPaymentCtrl.text,
        'repayment_period': _repaymentPeriod,
        'bank': _selectedBankId,
        'current_step': _current,
      };
      await prefs.setString(_draftKey(), jsonEncode(data));
    } catch (_) {}
  }

  Future<void> _saveDraftBackend() async {
    try {
      await ApiService().saveDraft({
        'mortgage_type': _mortgageType,
        'type': _mortgageType,
        'loan_type': _loanType,
        'current_step': _current + 1,
        'property': widget.property.id.toString(),
        'customer_type': _customerType,
        'dob': _dobCtrl.text,
        'gender': _gender,
        'employment_status': _employmentStatus,
        'monthly_income': _monthlyIncomeCtrl.text,
        'monthly_expenses': _monthlyExpensesCtrl.text,
        'loan_amount': _loanAmountCtrl.text,
        'down_payment': _downPaymentCtrl.text,
        'repayment_period': _repaymentPeriod,
        'bank': _selectedBankId?.toString() ?? '',
      });
    } catch (_) {}
  }

  Future<void> _saveDraft() async {
    await _saveDraftLocal();
    await _saveDraftBackend();
  }

  Future<void> _loadDraft() async {
    // try backend first
    try {
      final drafts = await ApiService().getDrafts(mortgageType: _mortgageType);
      // find draft for same property
      var found;
      for (var d in drafts) {
        final pid = d['property'];
        if (pid == widget.property.id || pid.toString() == widget.property.id.toString()) {
          found = d;
          break;
        }
      }
      found ??= drafts.isNotEmpty ? drafts.first : null;
      if (found != null && found['current_step'] != null && found['current_step'] > 1) {
        final dd = found['draft_data'] as Map<String, dynamic>? ?? {};
        _applyDraftData(dd, found['current_step']);
        // auto-resume
        if (mounted) {
          setState(() {});
          showAppSnackBar(context, 'Auto-resumed to step ${found['current_step']} of 8 • $_mortgageType', type: SnackBarType.success, title: 'Resumed');
        }
        return;
      }
    } catch (_) {}
    // local fallback
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_draftKey());
      if (raw != null) {
        final data = jsonDecode(raw) as Map<String, dynamic>;
        final step = data['current_step'] is int ? data['current_step'] as int : int.tryParse(data['current_step'].toString()) ?? 0;
        if (step > 1) {
          _applyDraftData(data, step + 1);
          if (mounted) {
            setState(() {});
            showAppSnackBar(context, 'Auto-resumed to step ${step + 1} of 8', type: SnackBarType.success);
          }
        }
      }
    } catch (_) {}
  }

  void _applyDraftData(Map<String, dynamic> d, int step) {
    _customerType = d['customer_type']?.toString() ?? _customerType;
    _dobCtrl.text = d['dob']?.toString() ?? _dobCtrl.text;
    _gender = d['gender']?.toString() ?? _gender;
    _marital = d['marital']?.toString() ?? _marital;
    _dependentsCtrl.text = d['dependents']?.toString() ?? _dependentsCtrl.text;
    _employmentStatus = d['employment_status']?.toString() ?? _employmentStatus;
    _employerCtrl.text = d['employer']?.toString() ?? _employerCtrl.text;
    _jobCtrl.text = d['job']?.toString() ?? _jobCtrl.text;
    _yearsEmployedCtrl.text = d['years_employed']?.toString() ?? _yearsEmployedCtrl.text;
    _monthlyIncomeCtrl.text = d['monthly_income']?.toString() ?? _monthlyIncomeCtrl.text;
    _monthlyExpensesCtrl.text = d['monthly_expenses']?.toString() ?? _monthlyExpensesCtrl.text;
    _bizNameCtrl.text = d['biz_name']?.toString() ?? _bizNameCtrl.text;
    _bizRegCtrl.text = d['biz_reg']?.toString() ?? _bizRegCtrl.text;
    _bizType = d['biz_type']?.toString() ?? _bizType;
    _bizYearsCtrl.text = d['biz_years']?.toString() ?? _bizYearsCtrl.text;
    _bizIncomeCtrl.text = d['biz_income']?.toString() ?? _bizIncomeCtrl.text;
    _bizExpensesCtrl.text = d['biz_expenses']?.toString() ?? _bizExpensesCtrl.text;
    _loanType = d['loan_type']?.toString() ?? _loanType;
    _loanAmountCtrl.text = d['loan_amount']?.toString() ?? _loanAmountCtrl.text;
    _downPaymentCtrl.text = d['down_payment']?.toString() ?? _downPaymentCtrl.text;
    _repaymentPeriod = d['repayment_period']?.toString() ?? _repaymentPeriod;
    if (d['bank'] != null && d['bank'].toString().isNotEmpty) {
      _selectedBankId = int.tryParse(d['bank'].toString());
    }
    _current = (step - 1).clamp(0, 7);
    if (_current == 3 && _customerType == 'employed') _current = 4;
  }

  bool _validateCurrent() {
    bool ok = true;
    if (_current == 0) {
      if (_customerType.isEmpty) ok = false;
    } else if (_current == 1) {
      if (_dobCtrl.text.trim().isEmpty) ok = false;
    } else if (_current == 2) {
      if (_employmentStatus.isEmpty || _monthlyIncomeCtrl.text.trim().isEmpty || _monthlyExpensesCtrl.text.trim().isEmpty) ok = false;
      if (_monthlyIncomeCtrl.text.isNotEmpty && double.tryParse(_monthlyIncomeCtrl.text) == null) ok = false;
    } else if (_current == 3) {
      if (_customerType == 'business') {
        if (_bizNameCtrl.text.trim().isEmpty) ok = false;
      }
    } else if (_current == 4) {
      if (_loanAmountCtrl.text.trim().isEmpty || _downPaymentCtrl.text.trim().isEmpty) ok = false;
      final loan = double.tryParse(_loanAmountCtrl.text);
      if (loan != null && loan < 10000000) ok = false;
    } else if (_current == 5) {
      if (_selectedBankId == null) ok = false;
    }
    return ok;
  }

  Future<void> _next() async {
    if (!_validateCurrent()) {
      setState(() => _hasAttemptedNext = true);
      showAppSnackBar(context, 'Please complete required fields (marked in red) before continuing', type: SnackBarType.error, title: 'Validation');
      return;
    }
    setState(() => _hasAttemptedNext = false);
    // save draft
    await _saveDraft();
    showAppSnackBar(context, 'Step ${_current + 1} saved successfully • Now step ${_current + 2}/8', type: SnackBarType.success, title: 'Saved');
    setState(() {
      _current++;
      if (_current == 3 && _customerType == 'employed') _current = 4;
      if (_current > 7) _current = 7;
    });
    if (_current == 7) _recalc();
  }

  void _prev() {
    setState(() {
      _hasAttemptedNext = false;
      _current--;
      if (_current == 3 && _customerType == 'employed') _current = 2;
      if (_current < 0) _current = 0;
    });
  }

  void _goTo(int idx) {
    if (idx == _current) return;
    if (idx < _current) {
      setState(() {
        _hasAttemptedNext = false;
        _current = idx;
        if (_current == 3 && _customerType == 'employed') _current = 2;
      });
      return;
    }
    // forward: allow but mark red if intermediate invalid
    bool hasInvalid = false;
    for (int i = _current; i < idx; i++) {
      if (i == 3 && _customerType == 'employed') continue;
      // temporary set current to i to validate
      final prev = _current;
      _current = i;
      if (!_validateCurrent()) hasInvalid = true;
      _current = prev;
    }
    if (!_validateCurrent()) hasInvalid = true;
    setState(() {
      _current = idx;
      if (_current == 3 && _customerType == 'employed') _current = 4;
    });
    _saveDraft();
    if (hasInvalid) {
      showAppSnackBar(context, 'Some previous steps have missing fields - marked with red. Please complete them.', type: SnackBarType.error, title: 'Incomplete steps');
    }
  }

  Future<void> _recalc() async {
    if (_loanAmountCtrl.text.isEmpty || _monthlyIncomeCtrl.text.isEmpty) return;
    try {
      final data = await ApiService().calculateAffordability({
        'loan_amount': double.tryParse(_loanAmountCtrl.text) ?? 0,
        'down_payment': double.tryParse(_downPaymentCtrl.text) ?? 0,
        'repayment_period': int.tryParse(_repaymentPeriod) ?? 0,
        'monthly_income': double.tryParse(_monthlyIncomeCtrl.text) ?? 0,
        'monthly_expenses': double.tryParse(_monthlyExpensesCtrl.text) ?? 0,
        'employment_status': _employmentStatus,
        'bank': _selectedBankId,
      });
      if (!mounted) return;
      setState(() => _aiResult = data);
    } catch (_) {}
  }

  Future<void> _submit() async {
    if (!_validateCurrent()) {
      showAppSnackBar(context, 'Please complete all required fields', type: SnackBarType.error);
      return;
    }
    setState(() => _isLoading = true);
    try {
      final data = {
        'property': widget.property.id,
        'loan_amount': double.parse(_loanAmountCtrl.text),
        'down_payment': _downPaymentCtrl.text.isEmpty ? 0 : double.parse(_downPaymentCtrl.text),
        'repayment_period': int.parse(_repaymentPeriod),
        'monthly_income': double.parse(_monthlyIncomeCtrl.text),
        'monthly_expenses': double.parse(_monthlyExpensesCtrl.text),
        'employment_status': _employmentStatus,
        'mortgage_type': _mortgageType,
        'loan_type': _loanType,
        'bank': _selectedBankId,
        'customer_type': _customerType,
      };
      final res = await ApiService().applyMortgage(data);
      // clear draft
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_draftKey());
      if (!mounted) return;
      showAppSnackBar(context, 'Application submitted successfully!', type: SnackBarType.success, title: 'Success');
      // show AI result
      try {
        final aff = await ApiService().getAffordability(res['id']);
        if (!mounted) return;
        setState(() => _aiResult = aff);
      } catch (_) {}
    } catch (e) {
      if (!mounted) return;
      showAppSnackBar(context, e.toString().replaceAll('Exception: ', ''), type: SnackBarType.error, title: 'Failed');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  InputDecoration _dec(String label, bool required, bool showError) {
    return InputDecoration(
      labelText: required ? '$label *' : label,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      errorBorder: OutlineInputBorder(borderSide: const BorderSide(color: Colors.red), borderRadius: BorderRadius.circular(10)),
      focusedErrorBorder: OutlineInputBorder(borderSide: const BorderSide(color: Colors.red, width: 2), borderRadius: BorderRadius.circular(10)),
    );
  }

  Widget _stepper() {
    const labels = ['Type', 'Personal', 'Employment', 'Business', 'Loan', 'Bank', 'Docs', 'Review'];
    return Column(
      children: [
        Row(
          children: List.generate(8, (i) {
            final isActive = i == _current;
            final isDone = i < _current;
            // check if step has error when attempting forward
            bool hasError = false;
            if (_hasAttemptedNext && i == _current && !_validateCurrent()) hasError = true;
            Color bg;
            Color border;
            Color txt;
            if (hasError) {
              bg = Colors.red;
              border = Colors.red;
              txt = Colors.white;
            } else if (isActive) {
              bg = const Color(0xFF0077B6);
              border = const Color(0xFF0077B6);
              txt = Colors.white;
            } else if (isDone) {
              bg = Colors.green;
              border = Colors.green;
              txt = Colors.white;
            } else {
              bg = Colors.grey[300]!;
              border = Colors.grey[400]!;
              txt = Colors.grey[600]!;
            }
            return Expanded(
              child: GestureDetector(
                onTap: () => _goTo(i),
                child: Column(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(color: bg, shape: BoxShape.circle, border: Border.all(color: border, width: 2)),
                      child: Center(child: isDone && !hasError ? const Icon(Icons.check, size: 16, color: Colors.white) : Text('${i + 1}', style: TextStyle(color: txt, fontWeight: FontWeight.bold, fontSize: 12))),
                    ),
                    const SizedBox(height: 4),
                    Text(labels[i], style: TextStyle(fontSize: 9, fontWeight: FontWeight.w600, color: hasError ? Colors.red : isActive ? const Color(0xFF0077B6) : isDone ? Colors.green : Colors.grey), textAlign: TextAlign.center),
                  ],
                ),
              ),
            );
          }),
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(value: (_current + 1) / 8, backgroundColor: Colors.grey[300], color: _hasAttemptedNext && !_validateCurrent() ? Colors.red : const Color(0xFF0077B6)),
      ],
    );
  }

  Widget _buildStep() {
    switch (_current) {
      case 0:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Customer Type', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            const Text('Are you employed or a business owner?', style: TextStyle(color: Colors.grey, fontSize: 13)),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: _typeCard('employed', Icons.work, 'Employed', 'Permanent / contract employment')),
                const SizedBox(width: 12),
                Expanded(child: _typeCard('business', Icons.store, 'Business Owner', 'Own business / entrepreneur')),
              ],
            ),
            if (_hasAttemptedNext && _customerType.isEmpty) const Padding(padding: EdgeInsets.only(top: 8), child: Text('Please select customer type', style: TextStyle(color: Colors.red, fontSize: 12))),
          ],
        );
      case 1:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Personal Information', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            TextFormField(controller: _dobCtrl, decoration: _dec('Date of Birth', true, _hasAttemptedNext && _dobCtrl.text.isEmpty), readOnly: true, onTap: () async { final d = await showDatePicker(context: context, initialDate: DateTime(1990), firstDate: DateTime(1950), lastDate: DateTime.now()); if (d != null) setState(() => _dobCtrl.text = d.toIso8601String().split('T').first); }),
            if (_hasAttemptedNext && _dobCtrl.text.isEmpty) const Text('Date of Birth is required', style: TextStyle(color: Colors.red, fontSize: 11)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _gender.isEmpty ? null : _gender, decoration: _dec('Gender', false, false), items: const [DropdownMenuItem(value: 'male', child: Text('Male')), DropdownMenuItem(value: 'female', child: Text('Female'))], onChanged: (v) => setState(() => _gender = v ?? '')),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _marital.isEmpty ? null : _marital, decoration: _dec('Marital Status', false, false), items: const [DropdownMenuItem(value: 'single', child: Text('Single')), DropdownMenuItem(value: 'married', child: Text('Married')), DropdownMenuItem(value: 'divorced', child: Text('Divorced'))], onChanged: (v) => setState(() => _marital = v ?? '')),
            const SizedBox(height: 12),
            TextFormField(controller: _dependentsCtrl, decoration: _dec('Dependents', false, false), keyboardType: TextInputType.number),
          ],
        );
      case 2:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Employment Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _employmentStatus, decoration: _dec('Employment Status', true, _hasAttemptedNext && _employmentStatus.isEmpty), items: const [DropdownMenuItem(value: 'employed', child: Text('Employed')), DropdownMenuItem(value: 'self_employed', child: Text('Self-Employed')), DropdownMenuItem(value: 'business_owner', child: Text('Business Owner')), DropdownMenuItem(value: 'unemployed', child: Text('Unemployed'))], onChanged: (v) => setState(() => _employmentStatus = v ?? 'employed')),
            if (_hasAttemptedNext && _employmentStatus.isEmpty) const Text('Employment status is required', style: TextStyle(color: Colors.red, fontSize: 11)),
            const SizedBox(height: 12),
            TextFormField(controller: _employerCtrl, decoration: _dec('Employer Name', false, false)),
            const SizedBox(height: 12),
            TextFormField(controller: _jobCtrl, decoration: _dec('Job Title', false, false)),
            const SizedBox(height: 12),
            TextFormField(controller: _monthlyIncomeCtrl, decoration: _dec('Monthly Income (TZS)', true, _hasAttemptedNext && _monthlyIncomeCtrl.text.isEmpty), keyboardType: TextInputType.number),
            if (_hasAttemptedNext && _monthlyIncomeCtrl.text.isEmpty) const Text('Monthly income is required', style: TextStyle(color: Colors.red, fontSize: 11)),
            const SizedBox(height: 12),
            TextFormField(controller: _monthlyExpensesCtrl, decoration: _dec('Monthly Expenses (TZS)', true, _hasAttemptedNext && _monthlyExpensesCtrl.text.isEmpty), keyboardType: TextInputType.number),
            if (_hasAttemptedNext && _monthlyExpensesCtrl.text.isEmpty) const Text('Monthly expenses is required', style: TextStyle(color: Colors.red, fontSize: 11)),
          ],
        );
      case 3:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Business Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const Text('For Business Owners only - will be skipped if Employed', style: TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 12),
            TextFormField(controller: _bizNameCtrl, decoration: _dec('Business Name', _customerType == 'business', _hasAttemptedNext && _customerType == 'business' && _bizNameCtrl.text.isEmpty)),
            if (_hasAttemptedNext && _customerType == 'business' && _bizNameCtrl.text.isEmpty) const Text('Business name is required', style: TextStyle(color: Colors.red, fontSize: 11)),
            const SizedBox(height: 12),
            TextFormField(controller: _bizRegCtrl, decoration: _dec('Registration Number (BRELA)', false, false)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _bizType.isEmpty ? null : _bizType, decoration: _dec('Business Type', _customerType == 'business', false), items: const [DropdownMenuItem(value: 'retail', child: Text('Retail')), DropdownMenuItem(value: 'wholesale', child: Text('Wholesale')), DropdownMenuItem(value: 'services', child: Text('Services')), DropdownMenuItem(value: 'manufacturing', child: Text('Manufacturing'))], onChanged: (v) => setState(() => _bizType = v ?? '')),
          ],
        );
      case 4:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Loan Details', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 12),
            TextFormField(controller: TextEditingController(text: widget.property.title), decoration: _dec('Property', true, false), readOnly: true),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _mortgageType, decoration: _dec('Mortgage Type', true, false), items: const [DropdownMenuItem(value: 'residential', child: Text('Residential')), DropdownMenuItem(value: 'construction', child: Text('Construction')), DropdownMenuItem(value: 'renovation', child: Text('Renovation')), DropdownMenuItem(value: 'land', child: Text('Land Purchase')), DropdownMenuItem(value: 'commercial', child: Text('Commercial'))], onChanged: (v) => setState(() => _mortgageType = v ?? 'residential')),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _loanType, decoration: _dec('Loan Type', true, false), items: const [DropdownMenuItem(value: 'purchase', child: Text('Purchase')), DropdownMenuItem(value: 'construction', child: Text('Construction')), DropdownMenuItem(value: 'semi_finish', child: Text('Semi Finish')), DropdownMenuItem(value: 'refinance', child: Text('Refinance'))], onChanged: (v) => setState(() => _loanType = v ?? 'purchase')),
            const SizedBox(height: 12),
            TextFormField(controller: _loanAmountCtrl, decoration: _dec('Loan Amount (TZS)', true, _hasAttemptedNext && _loanAmountCtrl.text.isEmpty), keyboardType: TextInputType.number),
            if (_hasAttemptedNext && _loanAmountCtrl.text.isEmpty) const Text('Loan amount is required', style: TextStyle(color: Colors.red, fontSize: 11)),
            if (_hasAttemptedNext && _loanAmountCtrl.text.isNotEmpty && (double.tryParse(_loanAmountCtrl.text) ?? 0) < 10000000) const Text('Minimum is 10,000,000 TZS', style: TextStyle(color: Colors.red, fontSize: 11)),
            const SizedBox(height: 12),
            TextFormField(controller: _downPaymentCtrl, decoration: _dec('Down Payment (TZS)', false, false), keyboardType: TextInputType.number),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(value: _repaymentPeriod, decoration: _dec('Repayment Period (Months)', true, false), items: const [DropdownMenuItem(value: '12', child: Text('12 months')), DropdownMenuItem(value: '60', child: Text('60 months')), DropdownMenuItem(value: '120', child: Text('120 months')), DropdownMenuItem(value: '180', child: Text('180 months')), DropdownMenuItem(value: '240', child: Text('240 months')), DropdownMenuItem(value: '360', child: Text('360 months'))], onChanged: (v) => setState(() => _repaymentPeriod = v ?? '180')),
          ],
        );
      case 5:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [const Text('Select Bank', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)), const SizedBox(width: 8), if (_selectedBankId != null) Chip(label: Text(_banks.firstWhere((b) => b['id'] == _selectedBankId, orElse: () => {'name': ''})['name'] ?? '', style: const TextStyle(fontSize: 10)), backgroundColor: Colors.blue.shade100)]),
            const SizedBox(height: 4),
            Text('Bank: ${_banks.firstWhere((b) => b['id'] == _selectedBankId, orElse: () => {'name': 'Not selected'})['name'] ?? 'Not selected'} • Mortgage: $_mortgageTypeLabel', style: const TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 12),
            if (_hasAttemptedNext && _selectedBankId == null) const Text('Please select a bank', style: TextStyle(color: Colors.red, fontSize: 11)),
            ..._banks.map((b) => Card(
                  color: _selectedBankId == b['id'] ? Colors.blue.shade50 : null,
                  shape: RoundedRectangleBorder(side: BorderSide(color: _selectedBankId == b['id'] ? const Color(0xFF0077B6) : Colors.grey.shade300, width: _selectedBankId == b['id'] ? 2 : 1), borderRadius: BorderRadius.circular(10)),
                  child: ListTile(
                    title: Text(b['name'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    subtitle: Text(b['email'] ?? '', style: const TextStyle(fontSize: 12)),
                    trailing: Text('${b['interest_rate'] ?? '12'}% p.a.', style: const TextStyle(color: Color(0xFF0077B6), fontWeight: FontWeight.bold)),
                    onTap: () => setState(() => _selectedBankId = b['id'] as int),
                  ),
                )),
            if (_banks.isEmpty) const Text('No banks available - default will be used', style: TextStyle(color: Colors.grey)),
          ],
        );
      case 6:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Upload Documents', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 8),
            const Text('Each file max 5MB. Allowed: PDF, JPG, PNG. (ID, Pay slips, Bank statements, Title deed)', style: TextStyle(color: Colors.grey, fontSize: 12)),
            const SizedBox(height: 16),
            Container(padding: const EdgeInsets.all(16), decoration: BoxDecoration(border: Border.all(color: Colors.grey.shade300, style: BorderStyle.solid), borderRadius: BorderRadius.circular(10)), child: const Row(children: [Icon(Icons.upload_file, color: Colors.grey), SizedBox(width: 8), Text('Documents upload will be added - currently optional', style: TextStyle(color: Colors.grey))])),
          ],
        );
      case 7:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [const Icon(Icons.check_circle, color: Colors.green), const SizedBox(width: 8), const Text('Review & Submit', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16))]),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text('Property: ${widget.property.title}', style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('Mortgage: $_mortgageTypeLabel via ${_banks.firstWhere((b) => b['id'] == _selectedBankId, orElse: () => {'name': 'Not selected'})['name'] ?? 'Not selected'}'),
                  Text('Loan: ${_loanAmountCtrl.text} TZS'),
                  Text('Period: $_repaymentPeriod months'),
                  Text('Income: ${_monthlyIncomeCtrl.text} TZS'),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            if (_aiResult != null)
              Card(
                color: const Color(0xFF0A2B4E),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('AI Assessment', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    Text('Monthly Installment: ${_aiResult!['monthly_installment'] ?? 'N/A'} TZS', style: const TextStyle(color: Colors.white)),
                    Text('Affordability: ${_aiResult!['affordability_score'] ?? 'N/A'}/100', style: const TextStyle(color: Colors.white)),
                    Text('Risk: ${_aiResult!['risk_score'] ?? 'N/A'}/100', style: const TextStyle(color: Colors.white)),
                    Text('DTI: ${_aiResult!['dti_ratio'] ?? 'N/A'}%', style: const TextStyle(color: Colors.white)),
                    if (_aiResult!['recommendation'] != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(_aiResult!['recommendation'], style: const TextStyle(color: Colors.white70, fontSize: 12))),
                  ]),
                ),
              ),
          ],
        );
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _typeCard(String value, IconData icon, String title, String subtitle) {
    final selected = _customerType == value;
    return GestureDetector(
      onTap: () => setState(() => _customerType = value),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: selected ? Colors.blue.shade50 : Colors.white, border: Border.all(color: selected ? const Color(0xFF0077B6) : Colors.grey.shade300, width: selected ? 2 : 1), borderRadius: BorderRadius.circular(10)),
        child: Column(children: [Icon(icon, color: const Color(0xFF0077B6), size: 32), const SizedBox(height: 8), Text(title, style: const TextStyle(fontWeight: FontWeight.bold)), Text(subtitle, style: const TextStyle(fontSize: 11, color: Colors.grey), textAlign: TextAlign.center)]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Apply: $_mortgageTypeLabel'), backgroundColor: const Color(0xFF0077B6)),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header bank + mortgage
            if (_selectedBankId != null)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(10), border: Border.all(color: Colors.blue.shade200)),
                child: Row(children: [const Icon(Icons.account_balance, color: Color(0xFF0077B6)), const SizedBox(width: 8), Expanded(child: Text('Applying via ${_banks.firstWhere((b) => b['id'] == _selectedBankId, orElse: () => {'name': 'Selected Bank'})['name'] ?? 'Bank'} • $_mortgageTypeLabel', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)))]),
              ),
            if (_selectedBankId != null) const SizedBox(height: 12),
            _stepper(),
            const SizedBox(height: 16),
            _buildStep(),
            const SizedBox(height: 24),
            Row(
              children: [
                if (_current > 0) OutlinedButton(onPressed: _prev, child: const Text('Previous')),
                const Spacer(),
                if (_current < 7) ElevatedButton(onPressed: _next, style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF0077B6)), child: const Text('Next')),
                if (_current == 7) ...[
                  _isLoading ? const CircularProgressIndicator() : ElevatedButton(onPressed: _submit, style: ElevatedButton.styleFrom(backgroundColor: Colors.green), child: const Text('Submit Application')),
                ],
              ],
            ),
            if (_aiResult != null && _current != 7) ...[
              const SizedBox(height: 16),
              Card(color: const Color(0xFF0A2B4E), child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('AI Assessment', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)), Text('Installment: ${_aiResult!['monthly_installment']} TZS', style: const TextStyle(color: Colors.white)), Text('Affordability: ${_aiResult!['affordability_score']}/100', style: const TextStyle(color: Colors.white))]))),
            ],
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _dobCtrl.dispose();
    _dependentsCtrl.dispose();
    _employerCtrl.dispose();
    _jobCtrl.dispose();
    _yearsEmployedCtrl.dispose();
    _monthlyIncomeCtrl.dispose();
    _monthlyExpensesCtrl.dispose();
    _bizNameCtrl.dispose();
    _bizRegCtrl.dispose();
    _bizYearsCtrl.dispose();
    _bizIncomeCtrl.dispose();
    _bizExpensesCtrl.dispose();
    _loanAmountCtrl.dispose();
    _downPaymentCtrl.dispose();
    super.dispose();
  }
}
