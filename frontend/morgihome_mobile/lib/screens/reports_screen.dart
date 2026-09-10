import 'package:flutter/material.dart';
import '../services/api_service.dart';

/// Reports parity (computed from same data as web).
class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  bool loading = true;
  Map<String, int> stats = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final api = ApiService();
      final props = await api.getProperties();
      List<dynamic> apps = [];
      List<dynamic> contracts = [];
      try {
        apps = await api.getMyMortgages();
      } catch (_) {}
      try {
        contracts = await api.getContracts();
      } catch (_) {}
      if (!mounted) return;
      setState(() {
        stats = {
          'properties': props.length,
          'available': props.where((p) => p.status == 'available').length,
          'sold': props.where((p) => p.status == 'sold').length,
          'applications': apps.length,
          'contracts': contracts.length,
        };
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
          const Text('Reports', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          for (final e in stats.entries)
            Card(child: ListTile(title: Text(e.key.toUpperCase()), trailing: Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)))),
        ],
      ),
    );
  }
}
