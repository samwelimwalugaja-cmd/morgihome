import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/mortgage.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';
import '../widgets/loading_spinner.dart';

class ApplicationStatusScreen extends StatefulWidget {
  const ApplicationStatusScreen({super.key});
  @override
  State<ApplicationStatusScreen> createState() => _ApplicationStatusScreenState();
}

class _ApplicationStatusScreenState extends State<ApplicationStatusScreen> {
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
      final apps = await _api.getMyApplications();
      setState(() { _apps = apps; _loading = false; });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'approved': return const Color(0xFF28A745);
      case 'rejected': return const Color(0xFFDC3545);
      case 'pending': return const Color(0xFFFFC107);
      default: return const Color(AppConstants.primaryColorValue);
    }
  }

  double _progress(String status) {
    switch (status) {
      case 'pending': return 0.16;
      case 'document_verification': return 0.33;
      case 'valuation': return 0.5;
      case 'credit_assessment': return 0.66;
      case 'approved': return 0.83;
      case 'disbursed': return 1.0;
      default: return 0.16;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('My Applications', style: TextStyle(color: Colors.white)), centerTitle: true),
      drawer: const CustomerDrawer(active: 'applications'),
      body: _loading
          ? const LoadingSpinner()
          : _apps.isEmpty
              ? Center(
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    const Icon(Icons.description_outlined, size: 64, color: Colors.grey),
                    const SizedBox(height: 12),
                    const Text('No applications yet', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    ElevatedButton(onPressed: () => Navigator.pushNamed(context, '/home'), style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue)), child: const Text('Browse Properties')),
                  ]),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _apps.length,
                    itemBuilder: (context, i) {
                      final app = _apps[i];
                      return InkWell(
                        onTap: () => Navigator.pushNamed(context, '/application-detail', arguments: app.id),
                        borderRadius: BorderRadius.circular(12),
                        child: Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB)), boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 8, offset: const Offset(0, 2))]),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(children: [
                                Expanded(child: Text(app.applicationNumber, style: const TextStyle(fontWeight: FontWeight.w700))),
                                Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: _statusColor(app.status).withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20), border: Border.all(color: _statusColor(app.status).withValues(alpha: 0.3))), child: Text(app.statusDisplay, style: TextStyle(color: _statusColor(app.status), fontSize: 11, fontWeight: FontWeight.w700))),
                              ]),
                              const SizedBox(height: 4),
                              Text(app.propertyTitle ?? 'Property', style: const TextStyle(fontWeight: FontWeight.w600)),
                              const SizedBox(height: 8),
                              ClipRRect(borderRadius: BorderRadius.circular(10), child: LinearProgressIndicator(value: _progress(app.status), minHeight: 6, backgroundColor: const Color(0xFFE5E7EB), valueColor: AlwaysStoppedAnimation(_statusColor(app.status)))),
                              const SizedBox(height: 12),
                              Row(children: [
                                Expanded(child: _info('Loan', 'TZS ${app.loanAmount}')),
                                Expanded(child: _info('Bank', app.bankName ?? '—')),
                                Expanded(child: _info('Date', app.createdAt.isNotEmpty ? app.createdAt.substring(0, 10) : '—')),
                              ]),
                              const SizedBox(height: 8),
                              if (app.affordabilityScore != null)
                                Container(
                                  padding: const EdgeInsets.all(8),
                                  decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(8)),
                                  child: Row(children: [
                                    const Icon(Icons.lightbulb, size: 16, color: Color(AppConstants.primaryColorValue)),
                                    const SizedBox(width: 6),
                                    Text('Affordability ${app.affordabilityScore}/100 • Risk ${app.riskScore}/100', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                                  ]),
                                ),
                            ],
                          ),
                        ),
                        ),
                      );
                    },
                  ),
                ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 1,
        selectedItemColor: const Color(AppConstants.primaryColorValue),
        onTap: (i) {
          if (i == 0) Navigator.pushReplacementNamed(context, '/home');
          if (i == 2) Navigator.pushReplacementNamed(context, '/profile');
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.description), label: 'Applications'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }

  Widget _info(String label, String value) {
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(color: Colors.grey, fontSize: 10, letterSpacing: 0.5)),
      const SizedBox(height: 2),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
    ]);
  }
}
