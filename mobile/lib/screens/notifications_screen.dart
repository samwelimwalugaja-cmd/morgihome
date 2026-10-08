import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Notifications — like web bell + /customer/notifications/:
/// server timeline events with persisted mark-as-read.
class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});
  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _Item {
  final String id;
  final String title;
  final String subtitle;
  final String time;
  final bool read;
  final int? appId;
  _Item(
      {required this.id,
      required this.title,
      required this.subtitle,
      required this.time,
      required this.read,
      this.appId});
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final _api = ApiService();
  List<_Item> _items = [];
  int _unread = 0;
  bool _loading = true;
  bool _marking = false;
  String _role = 'customer';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final user = await _api.getStoredUser();
      final data = await _api.getNotifications();
      if (!mounted) return;
      final list = (data['notifications'] as List? ?? []);
      setState(() {
        _role = user?.role ?? 'customer';
        _unread = (data['unread'] is int) ? data['unread'] as int : 0;
        _items = list.whereType<Map>().map((e) {
          final m = Map<String, dynamic>.from(e);
          int? appId;
          final raw = m['app_id'];
          if (raw is int) {
            appId = raw;
          } else if (raw != null) {
            appId = int.tryParse(raw.toString());
          }
          return _Item(
            id: (m['id'] ?? '').toString(),
            title: (m['title'] ?? '').toString(),
            subtitle: (m['message'] ?? '').toString(),
            time: (m['time'] ?? '').toString(),
            read: m['read'] == true,
            appId: appId,
          );
        }).toList();
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _loading = false);
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue));
    }
  }

  Future<void> _markAll() async {
    setState(() => _marking = true);
    try {
      await _api.markNotificationsRead();
      if (!mounted) return;
      setState(() {
        _unread = 0;
        _items = _items
            .map((i) => _Item(
                id: i.id,
                title: i.title,
                subtitle: i.subtitle,
                time: i.time,
                read: true,
                appId: i.appId))
            .toList();
      });
      Fluttertoast.showToast(msg: 'All marked as read');
    } catch (e) {
      Fluttertoast.showToast(
          msg: e.toString().replaceAll('Exception:', '').trim(),
          backgroundColor: const Color(AppConstants.errorColorValue));
    } finally {
      if (mounted) setState(() => _marking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isSeller = _role == 'seller';
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
          backgroundColor: const Color(AppConstants.secondaryColorValue),
          title: Text(_unread > 0 ? 'Notifications ($_unread new)' : 'Notifications',
              style: const TextStyle(color: Colors.white)),
          iconTheme: const IconThemeData(color: Colors.white),
          actions: [
            if (_unread > 0)
              TextButton(
                  onPressed: _marking ? null : _markAll,
                  child: _marking
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : const Text('Mark all read',
                          style: TextStyle(color: Colors.white, fontSize: 12))),
          ]),
      drawer: isSeller ? null : const CustomerDrawer(active: 'notifications'),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? const Center(
                  child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                      Icon(Icons.notifications_off_outlined,
                          size: 64, color: Colors.grey),
                      SizedBox(height: 12),
                      Text('No notifications',
                          style: TextStyle(fontWeight: FontWeight.w700)),
                      SizedBox(height: 4),
                      Text('Bank review updates will appear here live.',
                          style: TextStyle(color: Colors.grey, fontSize: 12)),
                    ]))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _items.length,
                    itemBuilder: (_, i) {
                      final it = _items[i];
                      return InkWell(
                        onTap: it.appId == null || isSeller
                            ? null
                            : () => Navigator.pushNamed(
                                context, '/application-detail',
                                arguments: it.appId),
                        child: Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                              color: it.read
                                  ? Colors.white
                                  : const Color(0xFFF0F9FF),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                  color: it.read
                                      ? const Color(0xFFE5E7EB)
                                      : const Color(
                                          AppConstants.primaryColorValue))),
                          child: Row(children: [
                            Container(
                                width: 40,
                                height: 40,
                                decoration: BoxDecoration(
                                    color: const Color(
                                            AppConstants.primaryColorValue)
                                        .withValues(alpha: 0.12),
                                    borderRadius: BorderRadius.circular(10)),
                                child: const Icon(Icons.account_balance,
                                    color: Color(
                                        AppConstants.primaryColorValue),
                                    size: 20)),
                            const SizedBox(width: 12),
                            Expanded(
                                child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                  Text(it.title,
                                      style: TextStyle(
                                          fontWeight: it.read
                                              ? FontWeight.w600
                                              : FontWeight.w800,
                                          fontSize: 13)),
                                  const SizedBox(height: 2),
                                  Text(it.subtitle,
                                      style: const TextStyle(
                                          color: Colors.grey, fontSize: 12)),
                                  if (it.time.isNotEmpty)
                                    Text(it.time,
                                        style: const TextStyle(
                                            color: Colors.grey,
                                            fontSize: 11)),
                                ])),
                            if (!it.read)
                              Container(
                                  width: 10,
                                  height: 10,
                                  decoration: const BoxDecoration(
                                      color: Color(
                                          AppConstants.primaryColorValue),
                                      shape: BoxShape.circle)),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
