import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';

/// Application detail + bank review segments parity with web.
class ApplicationDetailScreen extends StatefulWidget {
  final int applicationId;
  const ApplicationDetailScreen({super.key, required this.applicationId});

  @override
  State<ApplicationDetailScreen> createState() => _ApplicationDetailScreenState();
}

class _ApplicationDetailScreenState extends State<ApplicationDetailScreen> {
  bool loading = true;
  Map<String, dynamic>? detail;
  Map<String, dynamic>? timeline;
  final List<String> stages = ['document_verification', 'crb_check', 'valuation', 'credit_assessment', 'approval_decision'];
  final Map<String, String> stageLabel = {
    'document_verification': 'Documents verified successfully.',
    'crb_check': 'CRB info approved successfully.',
    'valuation': 'Valuation confirmed successfully.',
    'credit_assessment': 'Credit assessment completed successfully.',
    'approval_decision': 'Moved to final decision successfully.',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final d = await ApiService().getMortgageDetail(widget.applicationId);
      Map<String, dynamic> t = {};
      try {
        t = await ApiService().getTimeline(widget.applicationId);
      } catch (_) {}
      if (!mounted) return;
      setState(() {
        detail = d;
        timeline = t;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  Future<void> _confirmStage(String stage) async {
    try {
      await ApiService().advanceStage(widget.applicationId, stage);
      if (!mounted) return;
      showAppSnackBar(context, stageLabel[stage] ?? 'Stage confirmed successfully.', type: SnackBarType.success, title: 'Confirmed');
      _load();
    } catch (e) {
      if (!mounted) return;
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  Future<void> _approve() async {
    try {
      await ApiService().approveMortgage(widget.applicationId);
      if (!mounted) return;
      showAppSnackBar(context, 'Application approved successfully.', type: SnackBarType.success, title: 'Approved');
      _load();
    } catch (e) {
      if (!mounted) return;
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  Future<void> _reject() async {
    final c = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reject application'),
        content: TextField(controller: c, decoration: const InputDecoration(labelText: 'Reason')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Reject')),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ApiService().rejectMortgage(widget.applicationId, c.text);
      if (!mounted) return;
      showAppSnackBar(context, 'Application rejected successfully.', type: SnackBarType.success, title: 'Rejected');
      _load();
    } catch (e) {
      if (!mounted) return;
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  Future<void> _askCorrection(String stage) async {
    final c = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Correction for $stage'),
        content: TextField(controller: c, decoration: const InputDecoration(labelText: 'Instructions'), maxLines: 3),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Send')),
        ],
      ),
    );
    if (ok != true || c.text.trim().isEmpty) return;
    try {
      await ApiService().requestCorrection(widget.applicationId, kind: 'info', target: stage, instructions: c.text.trim());
      if (!mounted) return;
      showAppSnackBar(context, 'Correction request sent successfully.', type: SnackBarType.success, title: 'Sent');
      _load();
    } catch (e) {
      if (!mounted) return;
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Application #${widget.applicationId}')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : detail == null
              ? const Center(child: Text('Not found'))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Status: ${detail!['status']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('Stage: ${detail!['review_stage'] ?? '-'}'),
                              Text('Loan: ${detail!['loan_amount']} TZS'),
                              Text('Property: ${(detail!['property_details'] ?? {})['title'] ?? detail!['property'] ?? '-'}'),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      const Text('Review Stages (bank)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      for (final s in stages)
                        Card(
                          child: ListTile(
                            title: Text(s),
                            subtitle: Text(stageLabel[s] ?? ''),
                            trailing: Wrap(
                              spacing: 4,
                              children: [
                                IconButton(icon: const Icon(Icons.edit, size: 18), tooltip: 'Need correction?', onPressed: () => _askCorrection(s)),
                                ElevatedButton(onPressed: () => _confirmStage(s), child: const Text('Confirm', style: TextStyle(fontSize: 11))),
                              ],
                            ),
                          ),
                        ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(child: ElevatedButton.icon(onPressed: _approve, icon: const Icon(Icons.check), label: const Text('Approve'))),
                          const SizedBox(width: 8),
                          Expanded(child: ElevatedButton.icon(onPressed: _reject, icon: const Icon(Icons.close), label: const Text('Reject'), style: ElevatedButton.styleFrom(backgroundColor: Colors.red))),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text('Timeline', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      for (final ev in ((timeline?['events'] as List?) ?? []))
                        ListTile(
                          leading: const Icon(Icons.circle, size: 10, color: Color(0xFF0077B6)),
                          title: Text((ev['title'] ?? ev['stage'] ?? '').toString()),
                          subtitle: Text((ev['message'] ?? '').toString(), maxLines: 3, overflow: TextOverflow.ellipsis),
                        ),
                      const Text('Corrections', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      for (final co in ((timeline?['corrections'] as List?) ?? []))
                        Card(child: ListTile(title: Text('${co['kind']} — ${co['target'] ?? ''} (${co['status']})'), subtitle: Text((co['instructions'] ?? '').toString()))),
                    ],
                  ),
                ),
    );
  }
}
