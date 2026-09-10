import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';

class ContractsScreen extends StatefulWidget {
  const ContractsScreen({super.key});

  @override
  State<ContractsScreen> createState() => _ContractsScreenState();
}

class _ContractsScreenState extends State<ContractsScreen> {
  bool loading = true;
  List<dynamic> items = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final data = await ApiService().getContracts();
      if (!mounted) return;
      setState(() {
        items = data;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (items.isEmpty) return const Center(child: Text('No contracts yet.'));
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: items.length,
        itemBuilder: (c, i) {
          final m = items[i] as Map;
          return Card(child: ListTile(leading: const Icon(Icons.file_copy, color: Color(0xFF0077B6)), title: Text('Contract #${m['id']} • ${m['status'] ?? ''}'), subtitle: Text((m.toString().length > 100 ? m.toString().substring(0, 100) : m.toString()))));
        },
      ),
    );
  }
}
