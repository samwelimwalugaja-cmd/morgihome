import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../../models/contract.dart';
import '../../services/api_service.dart';
import '../../utils/constants.dart';

/// Sales like web seller sales (executed contracts + revenue).
class SellerSalesScreen extends StatefulWidget {
  const SellerSalesScreen({super.key});
  @override
  State<SellerSalesScreen> createState() => _SellerSalesScreenState();
}

class _SellerSalesScreenState extends State<SellerSalesScreen> {
  final _api = ApiService();
  List<Contract> _sales = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getMyContracts();
      if (mounted) setState(() { _sales = list.where((c) => c.status == 'executed').toList(); _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
      }
    }
  }

  double get _revenue => _sales.fold(0.0, (s, c) => s + (double.tryParse(c.loanAmount ?? '0') ?? 0));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Sales', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(children: [
              Container(
                margin: const EdgeInsets.all(12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: const Color(AppConstants.secondaryColorValue), borderRadius: BorderRadius.circular(12)),
                child: Row(children: [
                  Expanded(child: _stat('${_sales.length}', 'Total Sales')),
                  Expanded(child: _stat('TZS ${_revenue.toStringAsFixed(0)}', 'Revenue')),
                  Expanded(child: _stat(_sales.isEmpty ? 'TZS 0' : 'TZS ${(_revenue / _sales.length).toStringAsFixed(0)}', 'Avg Sale')),
                ]),
              ),
              Expanded(
                child: _sales.isEmpty
                    ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Icon(Icons.trending_up_outlined, size: 64, color: Colors.grey),
                        SizedBox(height: 12),
                        Text('No sales yet', style: TextStyle(fontWeight: FontWeight.w700)),
                        SizedBox(height: 4),
                        Text('Executed contracts appear here.', style: TextStyle(color: Colors.grey, fontSize: 12)),
                      ]))
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                          itemCount: _sales.length,
                          itemBuilder: (_, i) {
                            final c = _sales[i];
                            return Container(
                              margin: const EdgeInsets.only(bottom: 10),
                              padding: const EdgeInsets.all(14),
                              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                              child: Row(children: [
                                Container(width: 40, height: 40, decoration: BoxDecoration(color: const Color(0xFFDCFCE7), borderRadius: BorderRadius.circular(10)), child: const Icon(Icons.check_circle, color: Color(0xFF15803D))),
                                const SizedBox(width: 12),
                                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Text(c.propertyTitle ?? 'Property', style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                                  Text('#CTR-${c.id} • ${_shortDate(c.executedDate ?? c.createdAt)}', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                                ])),
                                Text('TZS ${c.loanAmount ?? '0'}', style: const TextStyle(color: Color(0xFF15803D), fontWeight: FontWeight.w800, fontSize: 13)),
                              ]),
                            );
                          },
                        ),
                      ),
              ),
            ]),
    );
  }

  String _shortDate(String iso) => iso.length >= 10 ? iso.substring(0, 10) : (iso.isEmpty ? '—' : iso);

  Widget _stat(String value, String label) => Column(children: [
        Text(value, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 14), textAlign: TextAlign.center),
        const SizedBox(height: 2),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ]);
}
