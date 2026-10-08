import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../models/mortgage.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

/// Track application like web: timeline, affordability, repayment preview.
/// Arguments: int (application id).
class ApplicationDetailScreen extends StatefulWidget {
  const ApplicationDetailScreen({super.key});
  @override
  State<ApplicationDetailScreen> createState() => _ApplicationDetailScreenState();
}

class _ApplicationDetailScreenState extends State<ApplicationDetailScreen> {
  final _api = ApiService();
  MortgageApplication? _app;
  bool _loading = true;
  String? _error;
  int? _appId;
  final _corrCtrl = TextEditingController();
  final Set<int> _responding = {};

  @override
  void dispose() {
    _corrCtrl.dispose();
    super.dispose();
  }

  static const _steps = ['pending', 'document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approved', 'disbursed'];
  static const _labels = ['Pending', 'Documents', 'CRB Check', 'Valuation', 'Credit Check', 'Approved', 'Disbursed'];

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final id = ModalRoute.of(context)!.settings.arguments as int?;
    if (id != null && _appId == null && _error == null) {
      _appId = id;
      _load(id);
    }
  }

  Future<void> _load(int id) async {
    try {
      final a = await _api.getApplicationDetail(id);
      // Merge live timeline (bank confirmations) — same as web track page
      try {
        final t = await _api.getApplicationTimeline(id);
        final events = (t['events'] as List? ?? [])
            .whereType<Map>()
            .map((e) => TimelineEntry.fromJson(Map<String, dynamic>.from(e)))
            .toList();
        final corrs = (t['corrections'] as List? ?? [])
            .whereType<Map>()
            .map((e) => CorrectionEntry.fromJson(Map<String, dynamic>.from(e)))
            .toList();
        final merged = MortgageApplication(
          id: a.id,
          applicationNumber: (t['application_number'] ?? a.applicationNumber).toString(),
          loanAmount: a.loanAmount,
          downPayment: a.downPayment,
          repaymentPeriod: a.repaymentPeriod,
          monthlyIncome: a.monthlyIncome,
          monthlyExpenses: a.monthlyExpenses,
          employmentStatus: a.employmentStatus,
          status: (t['status'] ?? a.status).toString(),
          mortgageType: a.mortgageType,
          loanType: a.loanType,
          affordabilityScore: a.affordabilityScore,
          riskScore: a.riskScore,
          dtiRatio: a.dtiRatio,
          monthlyInstallment: a.monthlyInstallment,
          propertyTitle: a.propertyTitle,
          propertyId: a.propertyId,
          bankName: (t['bank_name'] ?? a.bankName)?.toString(),
          bankId: a.bankId,
          createdAt: a.createdAt,
          reviewStage: (t['review_stage'] ?? a.reviewStage)?.toString(),
          reviewMessage: (t['review_message'] ?? a.reviewMessage)?.toString(),
          reviewNote: a.reviewNote,
          timeline: events.isNotEmpty ? events : a.timeline,
          corrections: corrs,
        );
        if (mounted) setState(() { _app = merged; _loading = false; });
      } catch (_) {
        if (mounted) setState(() { _app = a; _loading = false; });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = e.toString().replaceAll('Exception:', '').trim();
        });
      }
    }
  }

  Future<void> _respond(int correctionId) async {
    final text = _corrCtrl.text.trim();
    if (text.isEmpty) {
      Fluttertoast.showToast(msg: 'Write an answer first');
      return;
    }
    if (_appId == null) return;
    setState(() => _responding.add(correctionId));
    try {
      await _api.respondCorrection(applicationId: _appId!, correctionId: correctionId, text: text);
      if (!mounted) return;
      _corrCtrl.clear();
      Fluttertoast.showToast(msg: 'Response sent — the bank will continue review');
      _load(_appId!);
    } catch (e) {
      if (mounted) {
        Fluttertoast.showToast(
            msg: e.toString().replaceAll('Exception:', '').trim(),
            backgroundColor: const Color(AppConstants.errorColorValue));
      }
    } finally {
      if (mounted) setState(() => _responding.remove(correctionId));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Track Application', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _app == null
              ? Center(child: Text(_error ?? 'Not found'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    _card(children: [
                      Row(children: [
                        Expanded(child: Text(_app!.applicationNumber, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                        _badge(_app!.statusDisplay, _color(_app!.status)),
                      ]),
                      const SizedBox(height: 8),
                      Text(_app!.propertyTitle ?? 'Property', style: const TextStyle(fontWeight: FontWeight.w600)),
                      const Divider(height: 24),
                      _kv('Loan Amount', 'TZS ${_app!.loanAmount}'),
                      _kv('Bank', _app!.bankName ?? '—'),
                      _kv('Monthly Installment', _app!.monthlyInstallment != null ? 'TZS ${_app!.monthlyInstallment}' : '—'),
                      _kv('Type', _app!.mortgageType ?? _app!.loanType ?? '—'),
                      _kv('Applied', _app!.createdAt.isNotEmpty ? _app!.createdAt.substring(0, 10) : '—'),
                    ]),
                    const SizedBox(height: 12),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFBFDBFE))),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Container(width: 36, height: 36, decoration: BoxDecoration(color: const Color(AppConstants.primaryColorValue), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.account_balance, color: Colors.white, size: 20)),
                        const SizedBox(width: 10),
                        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          const Text('LIVE UPDATE FROM BANK', style: TextStyle(color: Colors.grey, fontSize: 10, letterSpacing: 1, fontWeight: FontWeight.w700)),
                          const SizedBox(height: 2),
                          Text(_app!.liveReviewMessage, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                          if (_app!.reviewNote != null && _app!.reviewNote!.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text('Bank note: ${_app!.reviewNote}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                          ],
                        ])),
                      ]),
                    ),
                    const SizedBox(height: 16),
                    if (_app!.corrections.where((c) => c.status == 'pending').isNotEmpty) ...[
                      _card(children: [
                        const Row(children: [
                          Icon(Icons.warning_amber_rounded, color: Color(0xFFD97706), size: 20),
                          SizedBox(width: 8),
                          Text('Bank Needs Your Response', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                        ]),
                        const SizedBox(height: 8),
                        ..._app!.corrections.where((c) => c.status == 'pending').map((c) => Container(
                              margin: const EdgeInsets.only(bottom: 10),
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                  color: const Color(0xFFFFFBEB),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(color: const Color(0xFFFDE68A))),
                              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Text(
                                    c.target.isNotEmpty ? c.target : c.kind,
                                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                                const SizedBox(height: 4),
                                Text(c.instructions, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                const SizedBox(height: 8),
                                TextField(
                                  controller: _corrCtrl,
                                  maxLines: 2,
                                  decoration: const InputDecoration(
                                      hintText: 'Write your answer…', border: OutlineInputBorder()),
                                ),
                                const SizedBox(height: 8),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: _responding.contains(c.id) ? null : () => _respond(c.id),
                                    style: ElevatedButton.styleFrom(
                                        backgroundColor: const Color(AppConstants.primaryColorValue)),
                                    child: _responding.contains(c.id)
                                        ? const SizedBox(
                                            width: 16,
                                            height: 16,
                                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                        : const Text('Send Response'),
                                  ),
                                ),
                              ]),
                            )),
                      ]),
                      const SizedBox(height: 16),
                    ],
                    _card(children: [
                      const Text('Progress', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      const SizedBox(height: 12),
                      ...List.generate(_steps.length, (i) {
                        final idx = _steps.indexOf(_app!.status);
                        final reached = _steps.contains(_app!.status) ? i <= idx : i == 0;
                        return Row(children: [
                          Column(children: [
                            Container(
                              width: 26, height: 26,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _app!.status == 'rejected' && i == 0 ? Colors.red : (reached ? const Color(AppConstants.primaryColorValue) : const Color(0xFFE5E7EB)),
                              ),
                              child: Icon(reached ? Icons.check : Icons.circle, size: 14, color: reached ? Colors.white : Colors.grey),

                            ),
                            if (i < _steps.length - 1) Container(width: 2, height: 22, color: reached ? const Color(AppConstants.primaryColorValue) : const Color(0xFFE5E7EB)),
                          ]),
                          const SizedBox(width: 12),
                          Padding(padding: const EdgeInsets.only(bottom: 22), child: Text(_labels[i], style: TextStyle(fontWeight: reached ? FontWeight.w700 : FontWeight.w400, color: reached ? Colors.black87 : Colors.grey))),
                        ]);
                      }),
                      if (_app!.status == 'rejected')
                        Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: Colors.red.shade50, borderRadius: BorderRadius.circular(8)), child: const Row(children: [Icon(Icons.cancel, color: Colors.red, size: 18), SizedBox(width: 8), Expanded(child: Text('This application was rejected.', style: TextStyle(fontSize: 12)))])),
                    ]),
                    const SizedBox(height: 16),
                    _card(children: [
                      const Text('AI Assessment', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                      const SizedBox(height: 8),
                      _kv('Affordability', '${_app!.affordabilityScore ?? '—'}/100'),
                      _kv('Risk Score', '${_app!.riskScore ?? '—'}/100'),
                      _kv('DTI Ratio', '${_app!.dtiRatio ?? '—'}%'),
                    ]),
                    if (_app!.timeline.isNotEmpty) ...[
                      const SizedBox(height: 16),
                      _card(children: [
                        const Text('Bank Review Timeline', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                        const SizedBox(height: 8),
                        ..._app!.timeline.map((e) => Padding(
                              padding: const EdgeInsets.symmetric(vertical: 6),
                              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                Container(width: 30, height: 30, decoration: const BoxDecoration(color: Color(AppConstants.primaryColorValue), shape: BoxShape.circle), child: const Icon(Icons.check, color: Colors.white, size: 16)),
                                const SizedBox(width: 10),
                                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Text(e.stageDisplay, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                                  Text(e.message, style: const TextStyle(fontSize: 12, color: Colors.grey)),
                                  Text(e.createdAt.isNotEmpty && e.createdAt.length >= 10 ? e.createdAt.substring(0, 10) : '', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                                ])),
                              ]),
                            )),
                      ]),
                    ],
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity, height: 48,
                      child: ElevatedButton.icon(
                        onPressed: () => Navigator.pushNamed(context, '/repayment', arguments: _app!.id),
                        icon: const Icon(Icons.calendar_month),
                        label: const Text('View Repayment Schedule'),
                        style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue), foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                      ),
                    ),
                  ]),
                ),
    );
  }

  Color _color(String s) {
    switch (s) {
      case 'approved': return const Color(0xFF28A745);
      case 'rejected': return const Color(0xFFDC3545);
      case 'disbursed': return const Color(0xFF0077B6);
      case 'pending': return const Color(0xFFFFC107);
      default: return const Color(AppConstants.primaryColorValue);
    }
  }

  Widget _card({required List<Widget> children}) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: children),
      );

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(children: [Expanded(child: Text(k, style: const TextStyle(color: Colors.grey, fontSize: 13))), Text(v, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))]),
      );

  Widget _badge(String t, Color c) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(color: c.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20), border: Border.all(color: c.withValues(alpha: 0.3))),
        child: Text(t, style: TextStyle(color: c, fontSize: 11, fontWeight: FontWeight.w700)),
      );
}
