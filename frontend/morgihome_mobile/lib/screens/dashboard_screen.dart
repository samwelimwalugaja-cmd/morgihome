import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/property.dart';

/// Role dashboard parity with web (stats + recent).
class DashboardScreen extends StatefulWidget {
  final String role;
  const DashboardScreen({super.key, required this.role});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  bool loading = true;
  int props = 0, apps = 0, contracts = 0, banks = 0;
  List<Property> recent = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService();
      List<Property> allProps = [];
      List<dynamic> mortgages = [];
      List<dynamic> contracts = [];
      List<dynamic> banks = [];
      try {
        allProps = widget.role == 'seller' || widget.role == 'realestate'
            ? await api.getMyProperties()
            : await api.getProperties();
      } catch (_) {}
      try {
        mortgages = await api.getMyMortgages();
      } catch (_) {}
      try {
        contracts = await api.getContracts();
      } catch (_) {}
      try {
        banks = await api.getBanks();
      } catch (_) {}
      if (!mounted) return;
      setState(() {
        props = allProps.length;
        apps = mortgages.length;
        this.contracts = contracts.length;
        this.banks = banks.length;
        recent = allProps.take(4).toList();
        loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('${widget.role.toUpperCase()} Dashboard', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF0A2B4E))),
          const SizedBox(height: 12),
          Row(
            children: [
              _stat('Properties', props, Icons.home, Colors.blue),
              _stat('Applications', apps, Icons.description, Colors.orange),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              _stat('Contracts', contracts, Icons.file_copy, Colors.green),
              _stat('Banks', banks, Icons.account_balance, Colors.purple),
            ],
          ),
          const SizedBox(height: 16),
          const Text('Recent Properties', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          if (recent.isEmpty) const Text('No properties yet.', style: TextStyle(color: Colors.grey)),
          for (final p in recent)
            Card(
              child: ListTile(
                leading: const Icon(Icons.home, color: Color(0xFF0077B6)),
                title: Text(p.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                subtitle: Text('${p.location} • ${p.status}'),
                trailing: Text('${p.price.toStringAsFixed(0)} TZS', style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF0077B6), fontSize: 12)),
              ),
            ),
        ],
      ),
    );
  }

  Widget _stat(String label, int v, IconData icon, Color c) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Icon(icon, color: c),
              const SizedBox(height: 4),
              Text('$v', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        ),
      ),
    );
  }
}
