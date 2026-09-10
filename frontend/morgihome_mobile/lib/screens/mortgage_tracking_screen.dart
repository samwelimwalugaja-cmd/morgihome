import 'package:flutter/material.dart';
import '../models/mortgage.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';

class MortgageTrackingScreen extends StatefulWidget {
  const MortgageTrackingScreen({super.key});

  @override
  State<MortgageTrackingScreen> createState() => _MortgageTrackingScreenState();
}

class _MortgageTrackingScreenState extends State<MortgageTrackingScreen> {
  List<MortgageApplication> _applications = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final apps = await ApiService().getMyMortgages();
      // deduplicate by property for pending (mirrors web logic)
      final seen = <int>{};
      final dedup = <MortgageApplication>[];
      for (final a in apps) {
        if (a.status == 'pending' || a.status == 'document_verification' || a.status == 'valuation' || a.status == 'credit_assessment') {
          if (seen.contains(a.propertyId)) continue;
          seen.add(a.propertyId);
        }
        dedup.add(a);
      }
      if (!mounted) return;
      setState(() {
        _applications = dedup;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      showAppSnackBar(
        context,
        'Failed to load applications',
        type: SnackBarType.error,
      );
    }
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'approved':
        return Colors.green;
      case 'rejected':
        return Colors.red;
      case 'disbursed':
        return const Color(0xFF0077B6);
      default:
        return Colors.orange;
    }
  }

  @override
  Widget build(BuildContext context) {
    final total = _applications.length;
    final pending = _applications.where((a) => a.status == 'pending').length;
    final approved = _applications.where((a) => a.status == 'approved').length;
    final disbursed = _applications.where((a) => a.status == 'disbursed').length;

    return Scaffold(
      appBar: AppBar(title: const Text('My Applications')),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // Summary cards - English only, pending count fixed
                  Row(
                    children: [
                      Expanded(child: _summaryCard('TOTAL', '$total', Icons.description, const Color(0xFF0077B6))),
                      const SizedBox(width: 8),
                      Expanded(child: _summaryCard('PENDING', '$pending', Icons.pending, Colors.orange)),
                      const SizedBox(width: 8),
                      Expanded(child: _summaryCard('APPROVED', '$approved', Icons.check_circle, Colors.green)),
                      const SizedBox(width: 8),
                      Expanded(child: _summaryCard('DISBURSED', '$disbursed', Icons.payments, const Color(0xFF0077B6))),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (_applications.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(32),
                      child: Center(child: Text('No mortgage applications yet')),
                    )
                  else
                    ..._applications.map((app) => Card(
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          margin: const EdgeInsets.only(bottom: 12),
                          child: ListTile(
                            title: Text(app.propertyTitle.isNotEmpty ? app.propertyTitle : 'Mortgage #${app.id}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Loan: ${app.loanAmount.toStringAsFixed(0)} TZS', style: const TextStyle(fontSize: 12)),
                                Text('Status: ${app.status}', style: const TextStyle(fontSize: 12)),
                                if (app.affordabilityScore != null) Text('Affordability: ${app.affordabilityScore}/100', style: const TextStyle(fontSize: 12)),
                                if (app.riskScore != null) Text('Risk: ${app.riskScore}', style: const TextStyle(fontSize: 12)),
                              ],
                            ),
                            trailing: Chip(
                              label: Text(app.status, style: const TextStyle(fontSize: 11)),
                              backgroundColor: _statusColor(app.status),
                              labelStyle: const TextStyle(color: Colors.white),
                            ),
                          ),
                        )),
                ],
              ),
            ),
    );
  }

  Widget _summaryCard(String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.w600)),
            Text(value, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }
}
