import 'package:flutter/material.dart';
import '../models/contract.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Activity feed: application + contract changes (like web notifications).
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _Item {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;
  final String? route;
  final Object? args;
  _Item({required this.icon, required this.color, required this.title, required this.subtitle, this.route, this.args});
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final _api = ApiService();
  List<_Item> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final apps = await _api.getMyApplications();
      List<Contract> contracts = [];
      try {
        contracts = await _api.getMyContracts();
      } catch (_) {}
      final items = <_Item>[];
      // Live bank review updates first (like web notifications from timeline)
      for (final a in apps) {
        try {
          final t = await _api.getApplicationTimeline(a.id);
          final events = (t['events'] as List? ?? []);
          for (final e in events.reversed.take(3)) {
            final m = Map<String, dynamic>.from(e as Map);
            items.add(_Item(
              icon: Icons.account_balance,
              color: const Color(AppConstants.primaryColorValue),
              title: '${m['title'] ?? m['stage']} — ${a.applicationNumber}',
              subtitle: (m['message'] ?? '').toString(),
              route: '/application-detail',
              args: a.id,
            ));
          }
        } catch (_) {}
      }
      for (final a in apps) {
        items.add(_Item(
          icon: Icons.description,
          color: _appColor(a.status),
          title: '${a.applicationNumber} • ${a.statusDisplay}',
          subtitle: '${a.liveReviewMessage} • ${_date(a.createdAt)}',
          route: '/application-detail',
          args: a.id,
        ));
      }
      for (final c in contracts) {
        items.add(_Item(
          icon: Icons.handshake,
          color: const Color(AppConstants.primaryColorValue),
          title: 'Contract #CTR-${c.id} • ${c.statusDisplay}',
          subtitle: '${c.propertyTitle ?? ''} • ${_date(c.createdAt)}',
          route: '/contracts',
        ));
      }
      if (mounted) setState(() { _items = items; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Color _appColor(String s) {
    switch (s) {
      case 'approved':
      case 'disbursed':
        return const Color(0xFF28A745);
      case 'rejected':
        return const Color(0xFFDC3545);
      case 'pending':
        return const Color(0xFFFFC107);
      default:
        return const Color(AppConstants.primaryColorValue);
    }
  }

  String _date(String iso) => iso.isNotEmpty && iso.length >= 10 ? iso.substring(0, 10) : '—';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Notifications', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'notifications'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? const Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  Icon(Icons.notifications_off_outlined, size: 64, color: Colors.grey),
                  SizedBox(height: 12),
                  Text('No notifications', style: TextStyle(fontWeight: FontWeight.w700)),
                  SizedBox(height: 4),
                  Text('Updates about your applications will appear here.', style: TextStyle(color: Colors.grey, fontSize: 12)),
                ]))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _items.length,
                    itemBuilder: (_, i) {
                      final it = _items[i];
                      return InkWell(
                        onTap: it.route == null ? null : () => Navigator.pushNamed(context, it.route!, arguments: it.args),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE5E7EB))),
                          child: Row(children: [
                            Container(width: 40, height: 40, decoration: BoxDecoration(color: it.color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(10)), child: Icon(it.icon, color: it.color, size: 20)),
                            const SizedBox(width: 12),
                            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                              Text(it.title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13)),
                              const SizedBox(height: 2),
                              Text(it.subtitle, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                            ])),
                            const Icon(Icons.chevron_right, color: Colors.grey, size: 18),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
