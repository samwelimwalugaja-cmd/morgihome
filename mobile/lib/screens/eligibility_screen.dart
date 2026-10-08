import 'dart:math';
import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../models/contract.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/custom_button.dart';
import '../widgets/customer_drawer.dart';

/// Check Eligibility — like web /customer/eligibility/:
/// short qualification against the pilot bank (NCBA).
class EligibilityScreen extends StatefulWidget {
  const EligibilityScreen({super.key});
  @override
  State<EligibilityScreen> createState() => _EligibilityScreenState();
}

class _EligibilityScreenState extends State<EligibilityScreen> {
  final _formKey = GlobalKey<FormState>();
  final _api = ApiService();
  final _incomeCtrl = TextEditingController();
  final _loanCtrl = TextEditingController();
  final _yearsCtrl = TextEditingController();

  String _customerType = 'employed';
  int _period = 180;
  bool _checking = false;
  Map<String, dynamic>? _result;

  @override
  void dispose() {
    _incomeCtrl.dispose();
    _loanCtrl.dispose();
    _yearsCtrl.dispose();
    super.dispose();
  }

  double _num(String s) {
    try {
      return double.parse(s.replaceAll(',', '').trim());
    } catch (_) {
      return 0;
    }
  }

  Future<void> _check() async {
    if (!_formKey.currentState!.validate()) return;
    final income = _num(_incomeCtrl.text);
    final loan = _num(_loanCtrl.text);
    if (income <= 0 || loan <= 0) {
      Fluttertoast.showToast(msg: 'Enter a valid monthly income and loan amount');
      return;
    }
    setState(() {
      _checking = true;
      _result = null;
    });
    try {
      // Pilot bank limits (NCBA) — like web qualifying_banks.
      List<Bank> banks = [];
      try {
        banks = await _api.getBanks();
      } catch (_) {}
      final bank = banks.isNotEmpty ? banks.first : null;
      final rate = bank?.interestRate != null ? double.tryParse(bank!.interestRate!) ?? 14.0 : 14.0;

      // Same maths as web eligibility POST (representative 14% unless bank known).
      final annualRate = (bank != null ? rate : 14.0) / 100.0;
      final mr = annualRate / 12;
      final double installment = mr == 0
          ? loan / _period
          : loan * (mr * pow(1 + mr, _period)) / (pow(1 + mr, _period) - 1);

      final employmentStatus = _customerType == 'employed' ? 'employed' : 'business_owner';
      final dti = income > 0 ? (installment / income) * 100 : 100;
      final disposable = income;
      double aff;
      if (disposable <= 0 || installment <= 0) {
        aff = installment <= 0 && disposable > 0 ? 100 : 0;
      } else {
        aff = min(100, (disposable / installment) * 100);
      }
      var risk = 100 - aff;
      risk += employmentStatus == 'employed' ? -10 : 5;
      risk = risk.clamp(0, 100);
      final canApply = dti <= 40 && aff >= 40 && risk <= 80;

      String reason;
      bool bankCan = canApply;
      if (bank != null) {
        final minLoan = double.tryParse(bank.minLoan ?? '') ?? 0;
        final maxLoan = double.tryParse(bank.maxLoan ?? '') ?? 0;
        final fitsAmount = (maxLoan <= 0 || loan <= maxLoan) && loan >= minLoan;
        // max period is not exposed on mobile Bank model; web default allows 360.
        bankCan = canApply && fitsAmount;
        reason = bankCan
            ? 'You meet the basic criteria for this bank.'
            : (!fitsAmount
                ? "Loan amount is outside this bank's range."
                : 'Affordability/DTI does not meet this bank\'s criteria.');
      } else {
        reason = canApply
            ? 'You meet the basic criteria for this bank.'
            : 'Affordability/DTI does not meet the criteria.';
      }

      if (!mounted) return;
      setState(() {
        _result = {
          'installment': installment,
          'affordability': aff,
          'dti': dti,
          'risk': risk,
          'canApply': canApply,
          'bank': bank,
          'bankCan': bankCan,
          'reason': reason,
        };
      });
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final r = _result;
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
          backgroundColor: const Color(AppConstants.secondaryColorValue),
          title: const Text('Check Eligibility', style: TextStyle(color: Colors.white)),
          iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'eligibility'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
                color: const Color(AppConstants.secondaryColorValue),
                borderRadius: BorderRadius.circular(12)),
            child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Short Qualification',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16)),
              SizedBox(height: 4),
              Text('Takes 30 seconds. No credit bureau check. See instantly whether you may qualify for NCBA Bank.',
                  style: TextStyle(color: Colors.white70, fontSize: 12)),
            ]),
          ),
          const SizedBox(height: 16),
          Form(
            key: _formKey,
            child: Column(children: [
              Row(children: [
                Expanded(
                    child: _typeCard('Employed', Icons.work, 'employed')),
                const SizedBox(width: 12),
                Expanded(
                    child: _typeCard('Business Owner', Icons.store, 'business')),
              ]),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _incomeCtrl,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                      labelText: _customerType == 'business'
                          ? 'Monthly Business Revenue (TZS)'
                          : 'Monthly Gross Salary (TZS)',
                      border: const OutlineInputBorder()),
                  validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _loanCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                      labelText: 'Desired House / Loan Amount (TZS)',
                      border: OutlineInputBorder()),
                  validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null),
              const SizedBox(height: 12),
              TextFormField(
                  controller: _yearsCtrl,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                      labelText: _customerType == 'business'
                          ? 'Years in Business (optional)'
                          : 'Years with Current Employer (optional)',
                      border: const OutlineInputBorder())),
              const SizedBox(height: 12),
              DropdownButtonFormField<int>(
                initialValue: _period,
                decoration: const InputDecoration(
                    labelText: 'Repayment Period', border: OutlineInputBorder()),
                items: const [
                  DropdownMenuItem(value: 60, child: Text('60 months (5 years)')),
                  DropdownMenuItem(value: 120, child: Text('120 months (10 years)')),
                  DropdownMenuItem(value: 180, child: Text('180 months (15 years)')),
                  DropdownMenuItem(value: 240, child: Text('240 months (20 years)')),
                  DropdownMenuItem(value: 300, child: Text('300 months (25 years)')),
                ],
                onChanged: (v) => setState(() => _period = v ?? 180),
              ),
              const SizedBox(height: 16),
              CustomButton(
                  text: 'Check Eligibility',
                  icon: Icons.calculate,
                  onPressed: _check,
                  isLoading: _checking),
            ]),
          ),
          if (r != null) ...[
            const SizedBox(height: 20),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE5E7EB))),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('Eligibility Result',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                const SizedBox(height: 12),
                Row(children: [
                  Expanded(
                      child: _metric('Monthly Payment',
                          'TZS ${(r['installment'] as double).toStringAsFixed(0)}')),
                  Expanded(
                      child: _metric('Affordability',
                          '${(r['affordability'] as double).toStringAsFixed(0)}/100')),
                ]),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                      child: _metric('DTI Ratio',
                          '${(r['dti'] as double).toStringAsFixed(1)}%')),
                  Expanded(
                      child: _metric('Risk Score',
                          '${(r['risk'] as double).toStringAsFixed(0)}/100')),
                ]),
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                      color: (r['canApply'] as bool)
                          ? const Color(0xFFECFDF5)
                          : const Color(0xFFFEF2F2),
                      borderRadius: BorderRadius.circular(8)),
                  child: Text(
                      (r['canApply'] as bool)
                          ? 'Good news! Based on this short check, you may qualify for a mortgage.'
                          : 'Affordability is tight (DTI ${(r['dti'] as double).toStringAsFixed(1)}%). Try reducing the loan amount or increasing the period.',
                      style: const TextStyle(fontSize: 13)),
                ),
                const SizedBox(height: 12),
                const Text('Matching Bank',
                    style: TextStyle(fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                _bankRow(r),
                if ((r['bankCan'] as bool)) ...[
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () {
                          final b = r['bank'] as Bank?;
                          Navigator.pushNamed(context, '/mortgage-apply',
                              arguments: {
                                'bank_id': b?.id,
                                'bank_name': b?.name,
                                'mortgage_type': 'residential'
                              });
                        },
                        icon: const Icon(Icons.send, size: 16),
                        label: const Text('Apply Direct'),
                        style: ElevatedButton.styleFrom(
                            backgroundColor:
                                const Color(AppConstants.primaryColorValue)),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => Navigator.pushNamed(
                            context, '/mortgage-apply',
                            arguments: const {'mortgage_type': 'residential'}),
                        child: const Text('Start Full Form'),
                      ),
                    ),
                  ]),
                ],
                const SizedBox(height: 8),
                const Text(
                    'This is only a short qualification. The bank still verifies documents, credit history and property value before final approval.',
                    style: TextStyle(fontSize: 11, color: Colors.grey)),
              ]),
            ),
          ],
        ]),
      ),
    );
  }

  Widget _typeCard(String label, IconData icon, String value) {
    final selected = _customerType == value;
    return InkWell(
      onTap: () => setState(() => _customerType = value),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
            color: selected
                ? const Color(AppConstants.primaryColorValue).withValues(alpha: 0.1)
                : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
                color: selected
                    ? const Color(AppConstants.primaryColorValue)
                    : const Color(0xFFE5E7EB),
                width: selected ? 2 : 1)),
        child: Column(children: [
          Icon(icon, color: const Color(AppConstants.primaryColorValue)),
          const SizedBox(height: 6),
          Text(label,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
              textAlign: TextAlign.center),
        ]),
      ),
    );
  }

  Widget _metric(String label, String value) => Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
            color: const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 10)),
          const SizedBox(height: 2),
          Text(value,
              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13)),
        ]),
      );

  Widget _bankRow(Map<String, dynamic> r) {
    final bank = r['bank'] as Bank?;
    final ok = r['bankCan'] as bool;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
              color: ok ? const Color(0xFF28A745) : const Color(0xFFE5E7EB))),
      child: Row(children: [
        Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
                color: const Color(AppConstants.secondaryColorValue),
                borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.account_balance, color: Colors.white)),
        const SizedBox(width: 12),
        Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
              Text(bank?.name ?? 'NCBA Bank',
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              Text(r['reason'].toString(),
                  style: TextStyle(
                      fontSize: 12,
                      color: ok
                          ? const Color(0xFF15803D)
                          : const Color(AppConstants.errorColorValue))),
            ])),
        Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
                color: ok
                    ? const Color(0xFF28A745)
                    : Colors.grey.shade300,
                borderRadius: BorderRadius.circular(20)),
            child: Text(ok ? 'Qualify' : 'Not a match',
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 11,
                    fontWeight: FontWeight.w700))),
      ]),
    );
  }
}
