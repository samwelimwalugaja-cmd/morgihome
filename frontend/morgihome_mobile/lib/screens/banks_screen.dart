import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';

/// Banks parity with web: real data, logo, no Apply for non-customer.
class BanksScreen extends StatefulWidget {
  final String role;
  const BanksScreen({super.key, required this.role});

  @override
  State<BanksScreen> createState() => _BanksScreenState();
}

class _BanksScreenState extends State<BanksScreen> {
  bool loading = true;
  List<Map<String, dynamic>> banks = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final data = await ApiService().getBanks();
      if (!mounted) return;
      setState(() {
        banks = data;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  String _img(String? url) {
    if (url == null || url.isEmpty) return '';
    if (url.startsWith('http')) return url;
    final base = ApiService.baseUrl.replaceAll('/api/', '');
    return url.startsWith('/') ? '$base$url' : '$base/$url';
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (banks.isEmpty) return const Center(child: Text('No partner banks yet.'));
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: banks.length,
        itemBuilder: (c, i) {
          final b = banks[i];
          final name = (b['name'] ?? b['email'] ?? 'Bank').toString();
          final email = (b['email'] ?? '').toString();
          final img = _img(b['profile_image']?.toString() ?? b['logo']?.toString());
          return Card(
            child: ListTile(
              leading: img.isNotEmpty
                  ? CircleAvatar(backgroundImage: NetworkImage(img))
                  : CircleAvatar(backgroundColor: const Color(0xFF0077B6), child: Text(name.isNotEmpty ? name.substring(0, 2).toUpperCase() : 'B', style: const TextStyle(color: Colors.white))),
              title: Text(name),
              subtitle: Text('$email\nInterest: ${b['interest_rate'] ?? '-'}% • Max: ${b['max_loan_amount'] ?? '-'}'),
              isThreeLine: true,
              trailing: widget.role == 'customer'
                  ? ElevatedButton(onPressed: () => Navigator.pushNamed(context, '/apply', arguments: b['id']), child: const Text('Apply', style: TextStyle(fontSize: 11)))
                  : const Icon(Icons.arrow_forward_ios, size: 14),
              onTap: () => showDialog(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: Text(name),
                  content: SingleChildScrollView(child: Text('Email: $email\nInterest: ${b['interest_rate']}\nFee: ${b['processing_fee']}\nMin: ${b['min_loan_amount']}\nMax: ${b['max_loan_amount']}\n\n${b['bank_requirements'] ?? ''}')),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Close')),
                    if (widget.role == 'customer') ElevatedButton(onPressed: () => Navigator.pushNamed(context, '/apply', arguments: b['id']), child: const Text('Apply')),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
