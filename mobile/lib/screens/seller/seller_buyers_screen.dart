import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../../models/mortgage.dart';
import '../../services/api_service.dart';
import '../../utils/constants.dart';

/// Interested Buyers like web seller buyers (applications for my properties).
class SellerBuyersScreen extends StatefulWidget {
  const SellerBuyersScreen({super.key});
  @override
  State<SellerBuyersScreen> createState() => _SellerBuyersScreenState();
}

class _SellerBuyersScreenState extends State<SellerBuyersScreen> {
  final _api = ApiService();
  List<MortgageApplication> _apps = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getMyApplications();
      if (mounted) setState(() { _apps = list; _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Interested Buyers', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _apps.isEmpty
              ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.group_outlined, size: 64, color: Colors.grey),
                  SizedBox(height: 12),
                  Text('No interested buyers yet', style: TextStyle(fontWeight: FontWeight.w700)),
                  SizedBox(height: 4),
                  Text('Buyers appear here when they apply.', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ]))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _apps.length,
                    itemBuilder: (_, i) {
                      final a = _apps[i];
                      return InkWell(
                        onTap: () => Navigator.pushNamed(context, '/application-detail', arguments: a.id),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 10),
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                          child: Row(children: [
                            CircleAvatar(backgroundColor: const Color(AppConstants.primaryColorValue), child: Text((a.propertyTitle ?? 'B').isNotEmpty ? (a.propertyTitle ?? 'B')[0].toUpperCase() : 'B', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700))),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(a.applicationNumber, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                              Text(a.propertyTitle ?? 'Property', style: const TextStyle(fontSize: 12)),
                              Text('TZS ${a.loanAmount} • ${a.statusDisplay}', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                            ])),
                            if (a.riskScore != null)
                              Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4), decoration: BoxDecoration(color: const Color(0xFFFFF7ED), borderRadius: BorderRadius.circular(20)), child: Text('Risk ${a.riskScore}', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Color(0xFFC2410C)))),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
