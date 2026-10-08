import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../models/contract.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../widgets/custom_button.dart';
import '../widgets/customer_drawer.dart';
import '../utils/constants.dart';

/// Mortgage Application — full parity with web 8-step wizard
/// (/customer/apply/): personal (NIDA/DOB), employment + deductions
/// (PSSSF/HESLB/PAYE), business (BRELA/LIC), pilot bank (NCBA) +
/// account number, loan + other-loan consolidation, AI preview,
/// draft auto-save / resume / discard.
class MortgageApplicationScreen extends StatefulWidget {
  const MortgageApplicationScreen({super.key});
  @override
  State<MortgageApplicationScreen> createState() => _MortgageApplicationScreenState();
}

class _MortgageApplicationScreenState extends State<MortgageApplicationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService();

  // Loan
  final _loanCtrl = TextEditingController();
  final _incomeCtrl = TextEditingController();
  final _annualCtrl = TextEditingController();
  final _expenseCtrl = TextEditingController(text: '0');
  // Personal
  final _dobCtrl = TextEditingController();
  final _nidaCtrl = TextEditingController();
  final _marriageCertCtrl = TextEditingController();
  String _gender = '';
  String _marital = '';
  String _nationality = 'TZ';
  // Employment
  final _employerCtrl = TextEditingController();
  final _jobCtrl = TextEditingController();
  final _yearsEmpCtrl = TextEditingController();
  String _contractType = '';
  String _sector = '';
  bool _dedPsssf = false;
  bool _dedHeslb = false;
  bool _dedPaye = false;
  // Business
  final _bizNameCtrl = TextEditingController();
  final _bizRegCtrl = TextEditingController();
  final _bizYearsCtrl = TextEditingController();
  String _bizType = '';
  bool _dedHeslbBiz = false;
  bool _dedPayeBiz = false;
  // Bank (pilot)
  final _accNumCtrl = TextEditingController();
  final _accNameCtrl = TextEditingController();
  // Other loan
  String _hasOtherLoan = 'no';
  final _otherBankCtrl = TextEditingController();
  final _otherBalCtrl = TextEditingController();
  final _otherPayCtrl = TextEditingController();
  String _otherConsolidate = '';

  String _customerType = 'employed'; // employed | business
  String _employment = 'employed';
  String _mortgageType = 'residential';
  String _loanType = 'purchase';
  int? _propertyId;
  Property? _property;
  List<Property> _properties = [];
  int? _bankId;
  List<Bank> _banks = [];
  int _period = 180;

  Map<String, dynamic>? _preview;
  bool _calculating = false;
  bool _loading = false;
  bool _savingDraft = false;
  int? _draftId;
  Timer? _draftTimer;
  bool _argsApplied = false;
  bool _draftLoaded = false;

  @override
  void dispose() {
    _draftTimer?.cancel();
    _loanCtrl.dispose();
    _incomeCtrl.dispose();
    _annualCtrl.dispose();
    _expenseCtrl.dispose();
    _dobCtrl.dispose();
    _nidaCtrl.dispose();
    _marriageCertCtrl.dispose();
    _employerCtrl.dispose();
    _jobCtrl.dispose();
    _yearsEmpCtrl.dispose();
    _bizNameCtrl.dispose();
    _bizRegCtrl.dispose();
    _bizYearsCtrl.dispose();
    _accNumCtrl.dispose();
    _accNameCtrl.dispose();
    _otherBankCtrl.dispose();
    _otherBalCtrl.dispose();
    _otherPayCtrl.dispose();
    super.dispose();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final arg = ModalRoute.of(context)!.settings.arguments;
    if (arg is Property) _property = arg;
    if (arg is Map && !_argsApplied) {
      _argsApplied = true;
      final m = arg;
      if (m['mortgage_type'] is String) {
        final t = (m['mortgage_type'] as String).toLowerCase();
        if (['residential', 'construction', 'renovation', 'land', 'commercial'].contains(t)) {
          _mortgageType = t;
        }
      }
      if (m['bank_id'] is int) _bankId = m['bank_id'];
      if (m['property'] is Property) _property = m['property'];
      if (m['property_id'] is int) _propertyId = m['property_id'];
    }
    if (_property != null) _propertyId ??= _property!.id;
    if (_banks.isEmpty) _init();
    _api.getStoredUser().then((u) {
      if (!mounted) return;
      if ((u?.role ?? '') == 'seller') {
        Fluttertoast.showToast(msg: 'Sellers list properties — only customers apply for mortgages');
        Navigator.pop(context);
      }
    });
  }

  Future<void> _init() async {
    try {
      final banks = await _api.getBanks();
      List<Property> props = [];
      try {
        props = await _api.getProperties();
      } catch (_) {}
      if (!mounted) return;
      setState(() {
        _banks = banks;
        _properties = props.where((p) => p.status == 'available').toList();
        // Pilot: single bank auto-selected (NCBA).
        if (_banks.length == 1) _bankId ??= _banks.first.id;
        if (_property != null) _propertyId = _property!.id;
      });
      // Resume latest draft for this mortgage type (web auto-continues).
      if (!_draftLoaded) {
        _draftLoaded = true;
        await _resumeDraft();
      }
    } catch (_) {}
  }

  Bank? get _bank {
    for (final b in _banks) {
      if (b.id == _bankId) return b;
    }
    return _banks.isNotEmpty ? _banks.first : null;
  }

  double _num(String s) {
    try {
      return double.parse(s.replaceAll(',', '').trim());
    } catch (_) {
      return 0;
    }
  }

  // ---------- Draft auto-save (web parity) ----------
  Map<String, dynamic> _draftPayload() => {
        'mortgage_type': _mortgageType,
        'loan_type': _loanType,
        'current_step': 8,
        if (_draftId != null) 'draft_id': _draftId,
        if (_propertyId != null) 'property': _propertyId,
        if (_bankId != null) 'bank': _bankId,
        'loan_amount': _loanCtrl.text,
        'repayment_period': _period,
        'monthly_income': _incomeCtrl.text,
        'monthly_expenses': _expenseCtrl.text,
        'annual_income': _annualCtrl.text,
        'employment_status': _employment,
        'customer_type': _customerType,
        'dob': _dobCtrl.text,
        'nida_number': _nidaCtrl.text,
        'gender': _gender,
        'marital_status': _marital,
        'marriage_certificate_number': _marriageCertCtrl.text,
        'nationality': _nationality,
        'employer_name': _employerCtrl.text,
        'job_title': _jobCtrl.text,
        'years_employed': _yearsEmpCtrl.text,
        'contract_type': _contractType,
        'employment_sector': _sector,
        'deduction_psssf': _dedPsssf,
        'deduction_heslb': _customerType == 'business' ? _dedHeslbBiz : _dedHeslb,
        'deduction_paye': _customerType == 'business' ? _dedPayeBiz : _dedPaye,
        'business_name': _bizNameCtrl.text,
        'business_type': _bizType,
        'business_registration_number': _bizRegCtrl.text,
        'business_years': _bizYearsCtrl.text,
        'bank_account_number': _accNumCtrl.text,
        'bank_account_name': _accNameCtrl.text,
        'has_other_loan': _hasOtherLoan,
        'other_loan_bank': _otherBankCtrl.text,
        'other_loan_balance': _otherBalCtrl.text,
        'other_loan_monthly_payment': _otherPayCtrl.text,
        'other_loan_consolidate': _otherConsolidate,
      };

  void _scheduleDraftSave() {
    _draftTimer?.cancel();
    _draftTimer = Timer(const Duration(seconds: 2), _saveDraftSilent);
  }

  Future<void> _saveDraftSilent() async {
    if (!mounted) return;
    setState(() => _savingDraft = true);
    try {
      final res = await _api.saveDraft(_draftPayload());
      if (mounted && res['id'] is int) setState(() => _draftId = res['id'] as int);
    } catch (_) {
      // Silent — web also saves quietly.
    } finally {
      if (mounted) setState(() => _savingDraft = false);
    }
  }

  Future<void> _resumeDraft() async {
    try {
      final drafts = await _api.getDrafts(mortgageType: _mortgageType);
      if (!mounted || drafts.isEmpty) return;
      final d = drafts.first;
      final raw = await _api.getApplicationDetail(d.id);
      if (!mounted) return;
      // Only resume empty form (don't overwrite user typing / explicit args).
      if (_loanCtrl.text.isNotEmpty) return;
      setState(() {
        _draftId = raw.id;
        _loanCtrl.text = raw.loanAmount == '0' ? '' : raw.loanAmount;
        _period = raw.repaymentPeriod != 0 ? raw.repaymentPeriod : 180;
        _incomeCtrl.text = raw.monthlyIncome == '0' ? '' : raw.monthlyIncome;
        if (raw.mortgageType != null && raw.mortgageType!.isNotEmpty) _mortgageType = raw.mortgageType!;
        if (raw.bankId != null) _bankId = raw.bankId;
        if (raw.propertyId != null) {
          _propertyId = raw.propertyId;
          for (final p in _properties) {
            if (p.id == raw.propertyId) _property = p;
          }
        }
      });
      Fluttertoast.showToast(msg: 'Draft resumed — continue where you left off');
    } catch (_) {}
  }

  Future<void> _discardDraft() async {
    if (_draftId == null) return;
    try {
      await _api.deleteDraft(_draftId!);
      if (!mounted) return;
      setState(() => _draftId = null);
      Fluttertoast.showToast(msg: 'Draft discarded');
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim());
    }
  }

  // ---------- Validation (mirrors backend serializer) ----------
  String? _validateNida(String v) {
    v = v.trim().replaceAll(' ', '').replaceAll('-', '');
    if (v.isEmpty) return null;
    if (!RegExp(r'^\d{20}$').hasMatch(v)) return 'NIDA must be 20 digits';
    if (_dobCtrl.text.trim().isNotEmpty) {
      try {
        final parts = _dobCtrl.text.trim().split('-');
        final y = int.parse(parts[0]), m = int.parse(parts[1]), d = int.parse(parts[2]);
        final ny = int.parse(v.substring(0, 4)), nm = int.parse(v.substring(4, 6)), nd = int.parse(v.substring(6, 8));
        if (y != ny || m != nm || d != nd) return 'First 8 of NIDA must match birth date (YYYYMMDD)';
      } catch (_) {}
    }
    return null;
  }

  String? _validateBizReg(String v) {
    v = v.trim();
    if (v.isEmpty) return null;
    final brela = RegExp(r'^BRL-\d{4}-\d{6}$');
    final lic = RegExp(r'^LIC-[A-Z]{2,4}-\d{4}-\d{6}$');
    if (!brela.hasMatch(v) && !lic.hasMatch(v)) {
      return 'Use BRL-YYYY-XXXXXX or LIC-XXX-YYYY-XXXXXX';
    }
    return null;
  }

  bool get _needsProperty => !['construction', 'renovation'].contains(_mortgageType);

  Future<void> _previewCalc() async {
    if (_loanCtrl.text.trim().isEmpty || _incomeCtrl.text.trim().isEmpty) {
      Fluttertoast.showToast(msg: 'Enter loan amount and income first');
      return;
    }
    setState(() {
      _calculating = true;
      _preview = null;
    });
    try {
      final r = await _api.calculateAffordability(_submitPayload());
      if (mounted) setState(() => _preview = r);
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _calculating = false);
    }
  }

  Map<String, dynamic> _submitPayload() {
    final isBiz = _customerType == 'business';
    return {
      if (_propertyId != null) 'property': _propertyId,
      'loan_amount': _loanCtrl.text.replaceAll(',', '').trim(),
      'repayment_period': _period,
      'monthly_income': isBiz
          ? (_incomeCtrl.text.trim().isEmpty ? _annualCtrl.text.replaceAll(',', '').trim() : _incomeCtrl.text.replaceAll(',', '').trim())
          : _incomeCtrl.text.replaceAll(',', '').trim(),
      'monthly_expenses': _expenseCtrl.text.replaceAll(',', '').trim().isEmpty ? '0' : _expenseCtrl.text.replaceAll(',', '').trim(),
      'employment_status': _employment,
      'mortgage_type': _mortgageType,
      'loan_type': _loanType,
      if (_bankId != null) 'bank': _bankId,
      if (_dobCtrl.text.trim().isNotEmpty) 'dob': _dobCtrl.text.trim(),
      if (_nidaCtrl.text.trim().isNotEmpty) 'nida_number': _nidaCtrl.text.trim().replaceAll(' ', '').replaceAll('-', ''),
      if (_gender.isNotEmpty) 'gender': _gender,
      if (_marital.isNotEmpty) 'marital_status': _marital,
      if (_marriageCertCtrl.text.trim().isNotEmpty) 'marriage_certificate_number': _marriageCertCtrl.text.trim(),
      if (_employerCtrl.text.trim().isNotEmpty) 'employer_name': _employerCtrl.text.trim(),
      if (_jobCtrl.text.trim().isNotEmpty) 'job_title': _jobCtrl.text.trim(),
      if (_yearsEmpCtrl.text.trim().isNotEmpty) 'years_employed': _yearsEmpCtrl.text.trim(),
      if (_contractType.isNotEmpty) 'contract_type': _contractType,
      if (_sector.isNotEmpty) 'employment_sector': _sector,
      'deduction_psssf': isBiz ? false : _dedPsssf,
      'deduction_heslb': isBiz ? _dedHeslbBiz : _dedHeslb,
      'deduction_paye': isBiz ? _dedPayeBiz : _dedPaye,
      if (_bizNameCtrl.text.trim().isNotEmpty) 'business_name': _bizNameCtrl.text.trim(),
      if (_bizType.isNotEmpty) 'business_type': _bizType,
      if (_bizRegCtrl.text.trim().isNotEmpty) 'business_registration_number': _bizRegCtrl.text.trim(),
      if (_bizYearsCtrl.text.trim().isNotEmpty) 'business_years': _bizYearsCtrl.text.trim(),
      if (_annualCtrl.text.trim().isNotEmpty) 'annual_income': _annualCtrl.text.replaceAll(',', '').trim(),
      'bank_account_number': _accNumCtrl.text.trim(),
      if (_accNameCtrl.text.trim().isNotEmpty) 'bank_account_name': _accNameCtrl.text.trim(),
      'has_other_loan': _hasOtherLoan,
      if (_hasOtherLoan == 'yes') ...{
        'other_loan_bank': _otherBankCtrl.text.trim(),
        'other_loan_balance': _otherBalCtrl.text.replaceAll(',', '').trim(),
        'other_loan_monthly_payment': _otherPayCtrl.text.replaceAll(',', '').trim(),
        'other_loan_consolidate': _otherConsolidate,
      },
    };
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final loanAmt = _num(_loanCtrl.text);
    if (loanAmt < 5000000) {
      Fluttertoast.showToast(msg: 'Minimum loan is 5,000,000 TZS');
      return;
    }
    // Bank limits (web Step 6 validation).
    final b = _bank;
    if (b != null) {
      final minL = double.tryParse(b.minLoan ?? '') ?? 0;
      final maxL = double.tryParse(b.maxLoan ?? '') ?? 0;
      if (minL > 0 && loanAmt < minL) {
        Fluttertoast.showToast(msg: 'Loan below bank minimum (TZS ${b.minLoan})');
        return;
      }
      if (maxL > 0 && loanAmt > maxL) {
        Fluttertoast.showToast(msg: 'Loan exceeds bank maximum (TZS ${b.maxLoan})');
        return;
      }
    }
    if (['residential', 'commercial', 'land'].contains(_mortgageType) && _property != null) {
      final price = double.tryParse(_property!.price) ?? 0;
      if (price > 0 && loanAmt > price) {
        Fluttertoast.showToast(
            msg: 'Loan exceeds property value (TZS ${_property!.price}). Reduce the amount.',
            backgroundColor: const Color(AppConstants.errorColorValue));
        return;
      }
    }
    if (_bankId == null) {
      Fluttertoast.showToast(msg: 'No bank available — try again later');
      return;
    }
    if (_needsProperty && _propertyId == null) {
      Fluttertoast.showToast(msg: 'Select a property first (browse properties)');
      return;
    }
    if (_accNumCtrl.text.trim().isEmpty) {
      Fluttertoast.showToast(msg: 'Enter your account number at ${_bank?.name ?? 'the bank'}');
      return;
    }
    if (_marital == 'married' && _marriageCertCtrl.text.trim().isEmpty) {
      Fluttertoast.showToast(msg: 'Married applicants must provide the marriage certificate number');
      return;
    }
    if (_hasOtherLoan == 'yes') {
      if (_otherBankCtrl.text.trim().isEmpty || _otherBalCtrl.text.trim().isEmpty || _otherConsolidate.isEmpty) {
        Fluttertoast.showToast(msg: 'Complete the other-loan details (bank, balance, consolidation choice)');
        return;
      }
    }
    setState(() => _loading = true);
    try {
      await _api.applyMortgage(_submitPayload());
      if (_draftId != null) {
        try {
          await _api.deleteDraft(_draftId!);
        } catch (_) {}
      }
      if (!mounted) return;
      Fluttertoast.showToast(msg: 'Sent directly to bank — bank review started. Track every stage live.');
      Navigator.pushReplacementNamed(context, '/applications');
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<int> get _periodOptions {
    const base = [60, 120, 180, 240, 300, 360];
    return base.where((p) => p <= _period || true).toList();
  }

  @override
  Widget build(BuildContext context) {
    final isBiz = _customerType == 'business';
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
          backgroundColor: const Color(AppConstants.secondaryColorValue),
          title: const Text('Mortgage Application', style: TextStyle(color: Colors.white)),
          iconTheme: const IconThemeData(color: Colors.white),
          actions: [
            if (_savingDraft)
              const Padding(
                  padding: EdgeInsets.all(14),
                  child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))),
            if (_draftId != null)
              IconButton(
                  tooltip: 'Discard draft',
                  icon: const Icon(Icons.delete_outline, color: Colors.white),
                  onPressed: _discardDraft),
          ]),
      drawer: const CustomerDrawer(active: 'apply'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          onChanged: _scheduleDraftSave,
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            if (_draftId != null)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                    color: const Color(0xFFFFFBEB),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFFDE68A))),
                child: const Row(children: [
                  Icon(Icons.save_outlined, size: 16, color: Color(0xFFB45309)),
                  SizedBox(width: 8),
                  Expanded(
                      child: Text('Draft auto-saved — it resumes automatically if you leave.',
                          style: TextStyle(fontSize: 12, color: Color(0xFF92400E)))),
                ]),
              ),
            _section('1 · Mortgage & Property', [
              DropdownButtonFormField<String>(
                initialValue: _mortgageType,
                decoration: const InputDecoration(labelText: 'Mortgage Type *', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'residential', child: Text('Residential — Buy house/apartment')),
                  DropdownMenuItem(value: 'construction', child: Text('Construction — Build new house')),
                  DropdownMenuItem(value: 'renovation', child: Text('Renovation — Semi Finish')),
                  DropdownMenuItem(value: 'land', child: Text('Land Purchase')),
                  DropdownMenuItem(value: 'commercial', child: Text('Commercial Property')),
                ],
                onChanged: (v) => setState(() => _mortgageType = v ?? 'residential'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _loanType,
                decoration: const InputDecoration(labelText: 'Loan Type *', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'purchase', child: Text('Purchase — Buy property')),
                  DropdownMenuItem(value: 'refinance', child: Text('Refinance / Equity Release')),
                  DropdownMenuItem(value: 'semi_finish', child: Text('Semi Finish — Complete at lintel stage')),
                  DropdownMenuItem(value: 'construction', child: Text('Construction — Build in stages')),
                ],
                onChanged: (v) => setState(() => _loanType = v ?? 'purchase'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                initialValue: _properties.any((p) => p.id == _propertyId) ? _propertyId : null,
                decoration: InputDecoration(
                    labelText: _needsProperty ? 'Property *' : 'Property (optional for Construction/Renovation)',
                    border: const OutlineInputBorder()),
                items: [
                  if (!_needsProperty) const DropdownMenuItem(value: null, child: Text('— I own the house already —')),
                  ..._properties.map((p) => DropdownMenuItem(
                      value: p.id, child: Text('${p.title} — TZS ${p.price}', overflow: TextOverflow.ellipsis))),
                ],
                validator: (v) => (_needsProperty && v == null) ? 'Select a property' : null,
                onChanged: (v) => setState(() {
                  _propertyId = v;
                  _property = null;
                  for (final p in _properties) {
                    if (p.id == v) _property = p;
                  }
                  _scheduleDraftSave();
                }),
              ),
              if (_property != null) ...[
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                      color: const Color(0xFFF0F9FF),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: const Color(0xFFBFDBFE))),
                  child: Row(children: [
                    const Icon(Icons.home, color: Color(AppConstants.primaryColorValue), size: 18),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_property!.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13))),
                    Text(_property!.formattedPrice,
                        style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w700, fontSize: 13)),
                  ]),
                ),
              ],
            ]),
            _section('2 · Customer Type', [
              Row(children: [
                Expanded(child: _typeCard('Employed', Icons.work, 'employed')),
                const SizedBox(width: 12),
                Expanded(child: _typeCard('Business Owner', Icons.store, 'business')),
              ]),
            ]),
            _section('3 · Personal Information', [
              TextFormField(
                  controller: _dobCtrl,
                  readOnly: true,
                  decoration: const InputDecoration(
                      labelText: 'Date of Birth (age 18–57)',
                      border: OutlineInputBorder(),
                      suffixIcon: Icon(Icons.calendar_today)),
                  onTap: () async {
                    final now = DateTime.now();
                    final picked = await showDatePicker(
                        context: context,
                        initialDate: DateTime(now.year - 25, now.month, now.day),
                        firstDate: DateTime(now.year - 57, now.month, now.day),
                        lastDate: DateTime(now.year - 18, now.month, now.day));
                    if (picked != null) {
                      _dobCtrl.text =
                          '${picked.year.toString().padLeft(4, '0')}-${picked.month.toString().padLeft(2, '0')}-${picked.day.toString().padLeft(2, '0')}';
                      _scheduleDraftSave();
                    }
                  }),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _nidaCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 20,
                  decoration: const InputDecoration(
                      labelText: 'NIDA Number (20 digits)', border: OutlineInputBorder(), counterText: ''),
                  validator: (v) => _validateNida(v ?? '')),
              const SizedBox(height: 12),
              Row(children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _gender.isEmpty ? null : _gender,
                    decoration: const InputDecoration(labelText: 'Gender', border: OutlineInputBorder()),
                    items: const [
                      DropdownMenuItem(value: 'male', child: Text('Male')),
                      DropdownMenuItem(value: 'female', child: Text('Female')),
                    ],
                    onChanged: (v) => setState(() => _gender = v ?? ''),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _marital.isEmpty ? null : _marital,
                    decoration: const InputDecoration(labelText: 'Marital Status', border: OutlineInputBorder()),
                    items: const [
                      DropdownMenuItem(value: 'single', child: Text('Single')),
                      DropdownMenuItem(value: 'married', child: Text('Married')),
                    ],
                    onChanged: (v) => setState(() => _marital = v ?? ''),
                  ),
                ),
              ]),
              if (_marital == 'married') ...[
                const SizedBox(height: 12),
                TextFormField(
                    controller: _marriageCertCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Marriage Certificate Number *', border: OutlineInputBorder()),
                    validator: (v) => (_marital == 'married' && (v == null || v.trim().isEmpty))
                        ? 'Required for married applicants'
                        : null),
              ],
            ]),
            if (!isBiz)
              _section('4 · Employment & Income', [
                TextFormField(
                    controller: _incomeCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                        labelText: 'Gross Monthly Income (TZS) *', border: OutlineInputBorder()),
                    validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
                const SizedBox(height: 12),
                TextFormField(
                    controller: _employerCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Employer Name', border: OutlineInputBorder())),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                      child: TextFormField(
                          controller: _jobCtrl,
                          decoration: const InputDecoration(
                              labelText: 'Job Title', border: OutlineInputBorder()))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: TextFormField(
                          controller: _yearsEmpCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Years Employed', border: OutlineInputBorder()))),
                ]),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _contractType.isEmpty ? null : _contractType,
                      decoration: const InputDecoration(
                          labelText: 'Contract Type', border: OutlineInputBorder()),
                      items: const [
                        DropdownMenuItem(value: 'permanent', child: Text('Permanent')),
                        DropdownMenuItem(value: 'contract', child: Text('Contract')),
                      ],
                      onChanged: (v) => setState(() => _contractType = v ?? ''),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _sector.isEmpty ? null : _sector,
                      decoration: const InputDecoration(
                          labelText: 'Sector', border: OutlineInputBorder()),
                      items: const [
                        DropdownMenuItem(value: 'public', child: Text('Public')),
                        DropdownMenuItem(value: 'private', child: Text('Private')),
                      ],
                      onChanged: (v) => setState(() => _sector = v ?? ''),
                    ),
                  ),
                ]),
                const SizedBox(height: 8),
                const Text('Statutory Deductions (tick what applies to you)',
                    style: TextStyle(fontSize: 12, color: Colors.grey)),
                CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('PSSSF 5% (public sector only)', style: TextStyle(fontSize: 13)),
                    value: _dedPsssf,
                    onChanged: (v) => setState(() => _dedPsssf = v ?? false)),
                CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('HESLB 15% (education loan)', style: TextStyle(fontSize: 13)),
                    value: _dedHeslb,
                    onChanged: (v) => setState(() => _dedHeslb = v ?? false)),
                CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('PAYE (income tax 0–30%)', style: TextStyle(fontSize: 13)),
                    value: _dedPaye,
                    onChanged: (v) => setState(() => _dedPaye = v ?? false)),
              ]),
            if (isBiz)
              _section('4 · Business & Income', [
                TextFormField(
                    controller: _bizNameCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Business Name', border: OutlineInputBorder())),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: _bizType.isEmpty ? null : _bizType,
                  decoration: const InputDecoration(
                      labelText: 'Business Type', border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(value: 'wholesale', child: Text('Wholesale')),
                    DropdownMenuItem(value: 'retail', child: Text('Retail')),
                  ],
                  onChanged: (v) => setState(() => _bizType = v ?? ''),
                ),
                const SizedBox(height: 12),
                TextFormField(
                    controller: _bizRegCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Registration No (BRL-YYYY-XXXXXX)',
                        border: OutlineInputBorder()),
                    validator: (v) => _validateBizReg(v ?? '')),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                      child: TextFormField(
                          controller: _annualCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Avg Annual Income (TZS)',
                              border: OutlineInputBorder()))),
                  const SizedBox(width: 12),
                  Expanded(
                      child: TextFormField(
                          controller: _bizYearsCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Years in Business',
                              border: OutlineInputBorder()))),
                ]),
                const SizedBox(height: 12),
                TextFormField(
                    controller: _incomeCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                        labelText: 'Monthly Net (optional if annual given)',
                        border: OutlineInputBorder())),
                const SizedBox(height: 8),
                const Text('PSSSF does not apply to business owners',
                    style: TextStyle(fontSize: 12, color: Colors.grey)),
                CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('HESLB 15% (education loan)', style: TextStyle(fontSize: 13)),
                    value: _dedHeslbBiz,
                    onChanged: (v) => setState(() => _dedHeslbBiz = v ?? false)),
                CheckboxListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    title: const Text('PAYE (income tax 0–30%)', style: TextStyle(fontSize: 13)),
                    value: _dedPayeBiz,
                    onChanged: (v) => setState(() => _dedPayeBiz = v ?? false)),
              ]),
            _section('5 · Bank (Pilot: NCBA)', [
              if (_bank != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                      color: const Color(0xFFF0F9FF),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(AppConstants.primaryColorValue))),
                  child: Row(children: [
                    Container(
                        width: 44,
                        height: 44,
                        decoration: BoxDecoration(
                            color: const Color(AppConstants.secondaryColorValue),
                            borderRadius: BorderRadius.circular(10)),
                        child: const Icon(Icons.account_balance, color: Colors.white)),
                    const SizedBox(width: 12),
                    Expanded(
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Text(_bank!.name,
                              style: const TextStyle(fontWeight: FontWeight.w800)),
                          Text(
                              '${_bank!.interestRate ?? '—'}% p.a. • Fee ${_bank!.processingFee ?? '—'}%',
                              style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        ])),
                    const Icon(Icons.lock, size: 16, color: Colors.grey),
                  ]),
                )
              else
                const Text('Loading bank…',
                    style: TextStyle(color: Colors.grey, fontSize: 13)),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _accNumCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Your Account Number at NCBA *',
                      border: OutlineInputBorder()),
                  validator: (v) =>
                      v == null || v.trim().isEmpty ? 'Account number is required' : null),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _accNameCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Account Holder Name',
                      border: OutlineInputBorder())),
            ]),
            _section('6 · Loan Details', [
              TextFormField(
                  controller: _loanCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Loan Amount (TZS) *', border: OutlineInputBorder()),
                  validator: (v) =>
                      v == null || v.trim().isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                initialValue: _periodOptions.contains(_period) ? _period : 180,
                decoration: const InputDecoration(
                    labelText: 'Repayment Period (months) *',
                    border: OutlineInputBorder()),
                items: _periodOptions
                    .map((p) => DropdownMenuItem(
                        value: p,
                        child: Text('$p months (${p ~/ 12} years)')))
                    .toList(),
                onChanged: (v) => setState(() => _period = v ?? 180),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _hasOtherLoan,
                decoration: const InputDecoration(
                    labelText: 'Do you have another loan at a different bank? *',
                    border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(
                      value: 'no',
                      child: Text("No — I don't have another loan")),
                  DropdownMenuItem(
                      value: 'yes', child: Text('Yes — I have another loan')),
                ],
                onChanged: (v) =>
                    setState(() => _hasOtherLoan = v ?? 'no'),
              ),
              if (_hasOtherLoan == 'yes') ...[
                const SizedBox(height: 12),
                TextFormField(
                    controller: _otherBankCtrl,
                    decoration: const InputDecoration(
                        labelText: 'Other Loan Bank *',
                        border: OutlineInputBorder()),
                    validator: (v) => (_hasOtherLoan == 'yes' &&
                            (v == null || v.trim().isEmpty))
                        ? 'Required'
                        : null),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                      child: TextFormField(
                          controller: _otherBalCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Remaining Balance *',
                              border: OutlineInputBorder()),
                          validator: (v) => (_hasOtherLoan == 'yes' &&
                                  (v == null || v.trim().isEmpty))
                              ? 'Required'
                              : null)),
                  const SizedBox(width: 12),
                  Expanded(
                      child: TextFormField(
                          controller: _otherPayCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                              labelText: 'Monthly Payment',
                              border: OutlineInputBorder()))),
                ]),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue:
                      _otherConsolidate.isEmpty ? null : _otherConsolidate,
                  decoration: const InputDecoration(
                      labelText: 'Should NCBA take over this loan? *',
                      border: OutlineInputBorder()),
                  items: const [
                    DropdownMenuItem(
                        value: 'yes',
                        child: Text('Yes — include in new mortgage')),
                    DropdownMenuItem(
                        value: 'no',
                        child: Text('No — I keep repaying separately')),
                  ],
                  validator: (v) => (_hasOtherLoan == 'yes' && v == null)
                      ? 'Choose one'
                      : null,
                  onChanged: (v) =>
                      setState(() => _otherConsolidate = v ?? ''),
                ),
              ],
            ]),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: _calculating ? null : _previewCalc,
              icon: _calculating
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.calculate),
              label: const Text('Check Affordability (AI)'),
            ),
            if (_preview != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                    color: const Color(0xFFF0F9FF),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFBFDBFE))),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                          'Monthly: TZS ${_preview!['monthly_installment']}',
                          style: const TextStyle(
                              fontWeight: FontWeight.w700, fontSize: 13)),
                      Text(
                          'Affordability: ${_preview!['affordability_score']}/100 • Risk: ${_preview!['risk_score']}/100 • DTI: ${_preview!['dti_ratio']}%',
                          style: const TextStyle(
                              fontSize: 12, color: Colors.grey)),
                      if (_preview!['recommendation'] != null)
                        Text(_preview!['recommendation'].toString(),
                            style: const TextStyle(
                                fontSize: 12, color: Colors.grey)),
                    ]),
              ),
            ],
            const SizedBox(height: 20),
            CustomButton(
                text: 'Submit Application',
                onPressed: _submit,
                isLoading: _loading),
            const SizedBox(height: 8),
            const Text(
                'AI will assess your affordability instantly. The bank verifies documents, credit history and property value before final approval.',
                style: TextStyle(fontSize: 11, color: Colors.grey)),
          ]),
        ),
      ),
    );
  }

  Widget _section(String title, List<Widget> children) => Container(
        margin: const EdgeInsets.only(bottom: 16),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title,
                  style: const TextStyle(
                      fontWeight: FontWeight.w800, fontSize: 14)),
              const SizedBox(height: 12),
              ...children,
            ]),
      );

  Widget _typeCard(String label, IconData icon, String value) {
    final selected = _customerType == value;
    return InkWell(
      onTap: () {
        setState(() {
          _customerType = value;
          _employment = value == 'employed' ? 'employed' : 'business_owner';
        });
        _scheduleDraftSave();
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
            color: selected
                ? const Color(AppConstants.primaryColorValue)
                    .withValues(alpha: 0.1)
                : const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: selected
                    ? const Color(AppConstants.primaryColorValue)
                    : const Color(0xFFE5E7EB),
                width: selected ? 2 : 1)),
        child: Column(children: [
          Icon(icon,
              color: const Color(AppConstants.primaryColorValue)),
          const SizedBox(height: 6),
          Text(label,
              style:
                  const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
              textAlign: TextAlign.center),
        ]),
      ),
    );
  }
}
