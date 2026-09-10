import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Customer Dashboard — like web customer_dashboard: stats + shortcuts.
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final _api = ApiService();
  bool _loading = true;
  int _properties = 0;
  int _applications = 0;
  int _pending = 0;
  int _approved = 0;
  String? _activeMortgage;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final props = await _api.getProperties();
      final apps = await _api.getMyApplications();
      if (!mounted) return;
      setState(() {
        _properties = props.length;
        _applications = apps.length;
        _pending = apps.where((a) => ['pending', 'document_verification', 'crb_check', 'valuation', 'credit_assessment'].contains(a.status)).length;
        _approved = apps.where((a) => a.status == 'approved').length;
        final active = apps.where((a) => a.status == 'approved' || a.status == 'disbursed');
        _activeMortgage = active.isNotEmpty ? active.first.applicationNumber : null;
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Dashboard', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'dashboard'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Row(children: [
                    Expanded(child: _stat('$_properties', 'Properties', Icons.home, 'Available')),
                    const SizedBox(width: 12),
                    Expanded(child: _stat('$_applications', 'Applications', Icons.description, '$_pending pending')),
                  ]),
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(child: _stat(_activeMortgage ?? '—', 'Active Mortgage', Icons.account_balance, _activeMortgage != null ? 'Active' : 'None')),
                    const SizedBox(width: 12),
                    Expanded(child: _stat('$_approved', 'Approved', Icons.check_circle, 'loans')),
                  ]),
                  const SizedBox(height: 20),
                  const Text('Quick Actions', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                  const SizedBox(height: 12),
                  _action(context, Icons.add_circle, 'Apply Mortgage', 'Residential, Construction, Renovation, Land, Commercial', '/mortgage-apply'),
                  _action(context, Icons.description, 'My Applications', 'Track every bank review stage live', '/applications'),
                  _action(context, Icons.home_work, 'Property Verification', 'Verify title via e-Ardhi portal', '/verify-property'),
                  _action(context, Icons.account_balance, 'Bank Requirements', 'Compare 6 banks before you choose', '/banks'),
                  _action(context, Icons.search, 'Search', 'Properties, applications, banks', '/search'),
                ],
              ),
            ),
    );
  }

  Widget _stat(String value, String label, IconData icon, String sub) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18), overflow: TextOverflow.ellipsis)), Icon(icon, color: const Color(AppConstants.primaryColorValue))]),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          Text(sub, style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontSize: 11, fontWeight: FontWeight.w600)),
        ]),
      );

  Widget _action(BuildContext context, IconData icon, String title, String sub, String route) => InkWell(
        onTap: () => Navigator.pushNamed(context, route),
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
          child: Row(children: [
            Container(width: 44, height: 44, decoration: BoxDecoration(color: const Color(AppConstants.primaryColorValue).withValues(alpha: 0.12), borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: const Color(AppConstants.primaryColorValue))),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w700)), Text(sub, style: const TextStyle(color: Colors.grey, fontSize: 12))])),
            const Icon(Icons.chevron_right, color: Colors.grey),
          ]),
        ),
      );
}
