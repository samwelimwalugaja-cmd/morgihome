import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/mortgage.dart';

/// Buyers parity (seller/realestate see who applied).
class BuyersScreen extends StatefulWidget {
  const BuyersScreen({super.key});

  @override
  State<BuyersScreen> createState() => _BuyersScreenState();
}

class _BuyersScreenState extends State<BuyersScreen> {
  bool loading = true;
  List<MortgageApplication> items = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final data = await ApiService().getMyMortgages();
      if (!mounted) return;
      setState(() {
        items = data;
        loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (items.isEmpty) return const Center(child: Text('No buyers yet.'));
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: items.length,
        itemBuilder: (c, i) {
          final a = items[i];
          return Card(
            child: ListTile(
              leading: const CircleAvatar(backgroundColor: Color(0xFF0077B6), child: Icon(Icons.person, color: Colors.white)),
              title: Text('${a.propertyTitle} • ${a.loanAmount.toStringAsFixed(0)} TZS'),
              subtitle: Text('${a.status} • ${a.createdAt.toString().substring(0, 10)}'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 14),
              onTap: () => Navigator.pushNamed(context, '/application_detail', arguments: a.id),
            ),
          );
        },
      ),
    );
  }
}
