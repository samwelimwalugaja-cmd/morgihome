import 'package:flutter/material.dart';
import '../models/contract.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Partner banks like web bank requirements (list + rates).
class BanksScreen extends StatefulWidget {
  const BanksScreen({super.key});
  @override
  State<BanksScreen> createState() => _BanksScreenState();
}

class _BanksScreenState extends State<BanksScreen> {
  final _api = ApiService();
  List<Bank> _banks = [];
  List<Bank> _filtered = [];
  bool _loading = true;
  String _filter = '';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final arg = ModalRoute.of(context)?.settings.arguments;
    if (arg is Map && arg['filter'] is String) {
      _filter = (arg['filter'] as String).toLowerCase();
    } else if (arg is String) {
      _filter = arg.toLowerCase();
    }
    if (_banks.isEmpty) _load();
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final b = await _api.getBanks();
      if (mounted) setState(() {
        _banks = b;
        _applyFilter();
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _applyFilter() {
    if (_filter.isEmpty) {
      _filtered = _banks;
    } else {
      _filtered = _banks.where((b) => b.name.toLowerCase().contains(_filter)).toList();
      // Fallback to static web list when API banks don't match slug
      if (_filtered.isEmpty) _filtered = _banks;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: Text(_filter.isEmpty ? 'Bank Requirements' : 'Bank Requirements • ${_filter.toUpperCase()}', style: const TextStyle(color: Colors.white, fontSize: 16)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'banks'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _filtered.isEmpty
              ? const Center(child: Text('No banks available'))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _filtered.length,
                    itemBuilder: (_, i) {
                      final b = _filtered[i];
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Row(children: [
                            Container(width: 44, height: 44, decoration: BoxDecoration(color: const Color(0xFF0A2B4E), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.account_balance, color: Colors.white)),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(b.name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 15)),
                              Text(b.email, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                            ])),
                            if (b.isVerified)
                              Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: const Color(0xFFDCFCE7), borderRadius: BorderRadius.circular(20)), child: const Text('VERIFIED', style: TextStyle(color: Color(0xFF15803D), fontSize: 10, fontWeight: FontWeight.w700))),
                          ]),
                          const Divider(height: 24),
                          Row(children: [
                            Expanded(child: _info('Interest', b.interestRate != null ? '${b.interestRate}%' : '—')),
                            Expanded(child: _info('Fee', b.processingFee != null ? 'TZS ${b.processingFee}' : '—')),
                            Expanded(child: _info('Min Loan', b.minLoan != null ? 'TZS ${b.minLoan}' : '—')),
                          ]),
                          const SizedBox(height: 6),
                          Row(children: [
                            Expanded(child: _info('Max Loan', b.maxLoan != null ? 'TZS ${b.maxLoan}' : '—')),
                            Expanded(child: _info('Requirements', (b.requirements != null && b.requirements!.isNotEmpty) ? b.requirements! : '—')),
                            const Expanded(child: SizedBox()),
                          ]),
                          const SizedBox(height: 12),
                          SizedBox(
                            width: double.infinity, height: 44,
                            child: ElevatedButton(
                              onPressed: () => Navigator.pushNamed(context, '/mortgage-apply', arguments: {'bank_id': b.id, 'bank_name': b.name}),
                              style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue)),
                              child: Text('Apply via ${b.name}'),
                            ),
                          ),
                        ]),
                      );
                    },
                  ),
                ),
    );
  }

  Widget _info(String label, String value) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: Colors.grey, fontSize: 10)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
      ]);
}
