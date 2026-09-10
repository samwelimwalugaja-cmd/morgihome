import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/contract.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Contracts like web: list + sign (customers and sellers use this screen).
class ContractsScreen extends StatefulWidget {
  const ContractsScreen({super.key});
  @override
  State<ContractsScreen> createState() => _ContractsScreenState();
}

class _ContractsScreenState extends State<ContractsScreen> {
  final _api = ApiService();
  List<Contract> _contracts = [];
  bool _loading = true;
  final Set<int> _signing = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getMyContracts();
      if (mounted) setState(() { _contracts = list; _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
      }
    }
  }

  Future<void> _sign(Contract c) async {
    setState(() => _signing.add(c.id));
    try {
      final res = await _api.signContract(c.id);
      if (!mounted) return;
      Fluttertoast.showToast(msg: res['message']?.toString() ?? 'Signed successfully');
      _load();
    } catch (e) {
      if (mounted) Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _signing.remove(c.id));
    }
  }

  Future<void> _openFile(String? path) async {
    if (path == null || path.isEmpty) return;
    final uri = Uri.parse(_api.buildImageUrl(path));
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Color _color(String s) {
    switch (s) {
      case 'executed': return const Color(0xFF28A745);
      case 'signed': return const Color(AppConstants.primaryColorValue);
      case 'pending_signature': return const Color(0xFFFFC107);
      default: return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('My Contracts', style: TextStyle(color: Colors.white)), centerTitle: true),
      drawer: const CustomerDrawer(active: 'contracts'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _contracts.isEmpty
              ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.description_outlined, size: 64, color: Colors.grey),
                  SizedBox(height: 12),
                  Text('No contracts yet', style: TextStyle(fontWeight: FontWeight.w700)),
                  SizedBox(height: 4),
                  Text('Contracts will appear here once created.', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ]))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _contracts.length,
                    itemBuilder: (_, i) {
                      final c = _contracts[i];
                      final canSign = c.status == 'draft' || c.status == 'pending_signature';
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [
                            Expanded(child: Text('#CTR-${c.id}', style: const TextStyle(fontWeight: FontWeight.w800, fontFamily: 'monospace'))),
                            Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: _color(c.status).withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)), child: Text(c.statusDisplay, style: TextStyle(color: _color(c.status), fontSize: 11, fontWeight: FontWeight.w700))),
                          ]),
                          const SizedBox(height: 6),
                          if (c.propertyTitle != null) Text(c.propertyTitle!, style: const TextStyle(fontWeight: FontWeight.w600)),
                          if (c.loanAmount != null) Text('TZS ${c.loanAmount}', style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          Row(children: [
                            _sig('Customer', c.customerSigned),
                            const SizedBox(width: 12),
                            _sig('Seller', c.sellerSigned),
                            const SizedBox(width: 12),
                            _sig('Bank', c.bankSigned),
                          ]),
                          const SizedBox(height: 12),
                          Row(children: [
                            if (c.contractFile != null && c.contractFile!.isNotEmpty)
                              OutlinedButton.icon(onPressed: () => _openFile(c.contractFile), icon: const Icon(Icons.picture_as_pdf, size: 16), label: const Text('PDF', style: TextStyle(fontSize: 12))),
                            const Spacer(),
                            if (canSign)
                              ElevatedButton(
                                onPressed: _signing.contains(c.id) ? null : () => _sign(c),
                                style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue), foregroundColor: Colors.white),
                                child: _signing.contains(c.id)
                                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                                    : const Text('Sign'),
                              ),
                          ]),
                        ]),
                      );
                    },
                  ),
                ),
    );
  }

  Widget _sig(String label, bool done) => Row(children: [
        Icon(done ? Icons.check_circle : Icons.radio_button_unchecked, size: 15, color: done ? const Color(0xFF28A745) : Colors.grey),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      ]);
}
