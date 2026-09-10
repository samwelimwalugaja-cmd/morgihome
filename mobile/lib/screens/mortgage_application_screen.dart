import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../models/contract.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../widgets/custom_button.dart';
import '../widgets/customer_drawer.dart';
import '../utils/constants.dart';

class MortgageApplicationScreen extends StatefulWidget {
  const MortgageApplicationScreen({super.key});
  @override
  State<MortgageApplicationScreen> createState() => _MortgageApplicationScreenState();
}

class _MortgageApplicationScreenState extends State<MortgageApplicationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _loanCtrl = TextEditingController();
  final _downCtrl = TextEditingController(text: '0');
  final _periodCtrl = TextEditingController(text: '180');
  final _incomeCtrl = TextEditingController();
  final _expenseCtrl = TextEditingController();
  String _employment = 'employed';
  String _mortgageType = 'residential';
  int? _bankId;
  String? _pendingBankName;
  List<Bank> _banks = [];
  Map<String, dynamic>? _preview;
  bool _calculating = false;
  bool _loading = false;
  final _api = ApiService();
  Property? _property;

  bool _argsApplied = false;

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
      if (m['bank_name'] is String) {
        // preselect by name after banks load
        _pendingBankName = m['bank_name'];
      }
    }
    if (_banks.isEmpty) _loadBanks();
    // Guard: seller is not allowed to apply (backend also rejects 403) - go back
    _api.getStoredUser().then((u) {
      if (!mounted) return;
      if ((u?.role ?? '') == 'seller') {
        Fluttertoast.showToast(msg: 'Sellers list properties — only customers apply for mortgages');
        Navigator.pop(context);
      }
    });
  }

  Future<void> _loadBanks() async {
    try {
      final b = await _api.getBanks();
      if (mounted) {
        setState(() => _banks = b);
        if (_pendingBankName != null) {
          final match = b.where((x) => x.name.toLowerCase().contains(_pendingBankName!.toLowerCase())).toList();
          if (match.isNotEmpty) setState(() => _bankId = match.first.id);
          _pendingBankName = null;
        }
      }
    } catch (_) {}
  }

  Future<void> _previewCalc() async {
    if (_loanCtrl.text.isEmpty || _periodCtrl.text.isEmpty || _incomeCtrl.text.isEmpty) return;
    setState(() { _calculating = true; _preview = null; });
    try {
      final r = await _api.calculateAffordability({
        'loan_amount': _loanCtrl.text,
        'down_payment': _downCtrl.text.isEmpty ? '0' : _downCtrl.text,
        'repayment_period': _periodCtrl.text,
        'monthly_income': _incomeCtrl.text,
        'monthly_expenses': _expenseCtrl.text.isEmpty ? '0' : _expenseCtrl.text,
        'employment_status': _employment,
        if (_bankId != null) 'bank': _bankId,
      });
      if (mounted) setState(() => _preview = r);
    } catch (_) {
    } finally {
      if (mounted) setState(() => _calculating = false);
    }
  }

  void _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final loanAmt = double.tryParse(_loanCtrl.text) ?? 0;
    if (loanAmt < 5000000) {
      Fluttertoast.showToast(msg: 'Minimum loan is 5,000,000 TZS');
      return;
    }
    // Purchase loans can never exceed the property value (backend enforces too)
    if (['residential', 'commercial', 'land'].contains(_mortgageType) && _property != null) {
      final price = double.tryParse(_property!.price) ?? 0;
      if (price > 0 && loanAmt > price) {
        Fluttertoast.showToast(msg: 'Loan exceeds property value (TZS ${_property!.price}). Reduce the amount.', backgroundColor: const Color(AppConstants.errorColorValue));
        return;
      }
    }
    if (_bankId == null) {
      Fluttertoast.showToast(msg: 'Please select a bank — your application is sent directly to that bank');
      return;
    }
    if (_property == null) {
      Fluttertoast.showToast(msg: 'Select a property first (browse properties)');
      return;
    }
    setState(() => _loading = true);
    try {
      await _api.applyMortgage({
        'property': _property?.id,
        'loan_amount': _loanCtrl.text,
        'down_payment': _downCtrl.text.isEmpty ? '0' : _downCtrl.text,
        'repayment_period': _periodCtrl.text,
        'monthly_income': _incomeCtrl.text,
        'monthly_expenses': _expenseCtrl.text.isEmpty ? '0' : _expenseCtrl.text,
        'employment_status': _employment,
        'mortgage_type': _mortgageType,
        if (_bankId != null) 'bank': _bankId,
      });
      if (!mounted) return;
      Fluttertoast.showToast(msg: 'Sent directly to bank — bank review started. Track every stage live.');
      Navigator.pushReplacementNamed(context, '/applications');
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Mortgage Application', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'apply'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (_property != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(AppConstants.primaryColorValue))),
                  child: Row(children: [
                    const Icon(Icons.home, color: Color(AppConstants.primaryColorValue)),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_property!.title, style: const TextStyle(fontWeight: FontWeight.w700))),
                    Text(_property!.formattedPrice, style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w700)),
                  ]),
                ),
              const SizedBox(height: 16),
              TextFormField(controller: _loanCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Loan Amount (TZS) *', border: OutlineInputBorder()), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              TextFormField(controller: _downCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Down Payment (TZS)', border: OutlineInputBorder())),
              const SizedBox(height: 12),
              TextFormField(controller: _periodCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Repayment Period (months) *', border: OutlineInputBorder()), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              TextFormField(controller: _incomeCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Monthly Income (TZS) *', border: OutlineInputBorder()), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              TextFormField(controller: _expenseCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Monthly Expenses (TZS) *', border: OutlineInputBorder()), validator: (v) => v == null || v.isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _employment,
                decoration: const InputDecoration(labelText: 'Employment Status', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'employed', child: Text('Employed')),
                  DropdownMenuItem(value: 'self_employed', child: Text('Self Employed')),
                  DropdownMenuItem(value: 'business_owner', child: Text('Business Owner')),
                ],
                onChanged: (v) => setState(() => _employment = v ?? 'employed'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _mortgageType,
                decoration: const InputDecoration(labelText: 'Mortgage Type', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 'residential', child: Text('Residential')),
                  DropdownMenuItem(value: 'construction', child: Text('Construction')),
                  DropdownMenuItem(value: 'renovation', child: Text('Renovation')),
                  DropdownMenuItem(value: 'land', child: Text('Land Purchase')),
                  DropdownMenuItem(value: 'commercial', child: Text('Commercial')),
                ],
                onChanged: (v) => setState(() => _mortgageType = v ?? 'residential'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                // ignore: deprecated_member_use
                value: _banks.any((b) => b.id == _bankId) ? _bankId : null,
                decoration: const InputDecoration(labelText: 'Bank — application is sent directly to this bank *', border: OutlineInputBorder()),
                items: [
                  const DropdownMenuItem(value: null, child: Text('Select bank')),
                  ..._banks.map((b) => DropdownMenuItem(value: b.id, child: Text('${b.name}${b.interestRate != null ? ' • ${b.interestRate}%' : ''}', overflow: TextOverflow.ellipsis))),
                ],
                validator: (v) => v == null ? 'Please select a bank' : null,
                onChanged: (v) => setState(() => _bankId = v),
              ),
              const SizedBox(height: 20),
              OutlinedButton.icon(
                onPressed: _calculating ? null : _previewCalc,
                icon: _calculating
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.calculate),
                label: const Text('Check Affordability (AI)'),
              ),
              if (_preview != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFFBFDBFE))),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('Monthly: TZS ${_preview!['monthly_installment']}', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                    Text('Affordability: ${_preview!['affordability_score']}/100 • Risk: ${_preview!['risk_score']}/100', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                    if (_preview!['recommendation'] != null) Text(_preview!['recommendation'].toString(), style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ]),
                ),
              ],
              const SizedBox(height: 20),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: const Color(0xFFFFF7ED), borderRadius: BorderRadius.circular(8), border: Border.all(color: const Color(0xFFFFEDD5))),
                child: const Row(children: [Icon(Icons.lightbulb, color: Color(0xFFF59E0B), size: 20), SizedBox(width: 8), Expanded(child: Text('AI will assess your affordability instantly after submission.', style: TextStyle(fontSize: 12, color: Colors.grey)))]),
              ),
              const SizedBox(height: 20),
              CustomButton(text: 'Submit Application', onPressed: _submit, isLoading: _loading),
            ],
          ),
        ),
      ),
    );
  }
}
