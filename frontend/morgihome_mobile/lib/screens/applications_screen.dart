import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';
import '../models/mortgage.dart';

/// Applications list parity with web (filter pending/approved/rejected).
class ApplicationsScreen extends StatefulWidget {
  final String role;
  const ApplicationsScreen({super.key, required this.role});

  @override
  State<ApplicationsScreen> createState() => _ApplicationsScreenState();
}

class _ApplicationsScreenState extends State<ApplicationsScreen> {
  bool loading = true;
  List<MortgageApplication> all = [];
  String filter = 'all';

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
        all = data;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      showAppSnackBar(context, e.toString().replaceAll('Exception: ', ''), type: SnackBarType.error, title: 'Failed to load');
    }
  }

  @override
  Widget build(BuildContext context) {
    final list = filter == 'all' ? all : all.where((a) => a.status == filter).toList();
    return Column(
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.all(8),
          child: Row(
            children: [
              for (final f in ['all', 'pending', 'approved', 'rejected'])
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: ChoiceChip(label: Text(f), selected: filter == f, onSelected: (_) => setState(() => filter = f)),
                ),
            ],
          ),
        ),
        Expanded(
          child: loading
              ? const Center(child: CircularProgressIndicator())
              : list.isEmpty
                  ? const Center(child: Text('No applications yet.'))
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.builder(
                        itemCount: list.length,
                        itemBuilder: (c, i) {
                          final a = list[i];
                          return Card(
                            margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            child: ListTile(
                              leading: const Icon(Icons.description, color: Color(0xFF0077B6)),
                              title: Text('${a.propertyTitle} • ${a.loanAmount.toStringAsFixed(0)} TZS'),
                              subtitle: Text('${a.status} • ${a.createdAt.toString().substring(0, 10)}'),
                              trailing: const Icon(Icons.arrow_forward_ios, size: 14),
                              onTap: () => Navigator.pushNamed(context, '/application_detail', arguments: a.id),
                            ),
                          );
                        },
                      ),
                    ),
        ),
      ],
    );
  }
}
