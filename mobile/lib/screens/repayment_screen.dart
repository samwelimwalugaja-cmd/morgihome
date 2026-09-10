import 'package:flutter/material.dart';
import '../models/contract.dart';
import '../models/mortgage.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Repayment schedule like web repayment page.
/// Arguments: int (application id) or null (choose application).
class RepaymentScreen extends StatefulWidget {
  const RepaymentScreen({super.key});
  @override
  State<RepaymentScreen> createState() => _RepaymentScreenState();
}

class _RepaymentScreenState extends State<RepaymentScreen> {
  final _api = ApiService();
  List<MortgageApplication> _apps = [];
  List<RepaymentEntry> _schedule = [];
  int? _selectedId;
  bool _loading = true;
  bool _loadingSchedule = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final arg = ModalRoute.of(context)!.settings.arguments;
    if (arg is int && _selectedId == null) _selectedId = arg;
    if (_apps.isEmpty && _loading) _init();
  }

  Future<void> _init() async {
    try {
      final apps = await _api.getMyApplications();
      if (!mounted) return;
      setState(() { _apps = apps; _loading = false; });
      final id = _selectedId ?? (apps.isNotEmpty ? apps.first.id : null);
      if (id != null) _loadSchedule(id);
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadSchedule(int id) async {
    setState(() { _selectedId = id; _loadingSchedule = true; _schedule = []; });
    try {
      final s = await _api.getRepaymentSchedule(id);
      if (mounted) setState(() { _schedule = s; _loadingSchedule = false; });
    } catch (_) {
      if (mounted) setState(() => _loadingSchedule = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Repayment Schedule', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'repayment'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _apps.isEmpty
              ? const Center(child: Text('No applications yet'))
              : Column(children: [
                  Container(
                    color: Colors.white,
                    padding: const EdgeInsets.all(12),
                    child: DropdownButtonFormField<int>(
                      initialValue: _selectedId,
                      decoration: const InputDecoration(labelText: 'Application', border: OutlineInputBorder()),
                      items: _apps.map((a) => DropdownMenuItem(value: a.id, child: Text('${a.applicationNumber} • ${a.propertyTitle ?? ''}', overflow: TextOverflow.ellipsis))).toList(),
                      onChanged: (v) { if (v != null) _loadSchedule(v); },
                    ),
                  ),
                  Expanded(
                    child: _loadingSchedule
                        ? const Center(child: CircularProgressIndicator())
                        : _schedule.isEmpty
                            ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                                Icon(Icons.calendar_month_outlined, size: 56, color: Colors.grey),
                                SizedBox(height: 8),
                                Text('No schedule yet', style: TextStyle(fontWeight: FontWeight.w700)),
                                SizedBox(height: 4),
                                Text('Schedule appears after approval.', style: TextStyle(color: Colors.grey, fontSize: 12)),
                              ]))
                            : ListView.builder(
                                padding: const EdgeInsets.all(12),
                                itemCount: _schedule.length,
                                itemBuilder: (_, i) {
                                  final e = _schedule[i];
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 8),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE5E7EB))),
                                    child: Row(children: [
                                      Container(width: 38, height: 38, decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(8)), child: Center(child: Text('${e.installmentNumber}', style: const TextStyle(fontWeight: FontWeight.w800, color: Color(AppConstants.primaryColorValue))))),
                                      const SizedBox(width: 12),
                                      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                        Text('TZS ${e.amountDue}', style: const TextStyle(fontWeight: FontWeight.w700)),
                                        Text(e.dueDate.isNotEmpty ? e.dueDate.substring(0, 10) : '—', style: const TextStyle(color: Colors.grey, fontSize: 12)),
                                      ])),
                                      Text('Bal TZS ${e.balanceRemaining}', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                                    ]),
                                  );
                                },
                              ),
                  ),
                ]),
    );
  }
}
