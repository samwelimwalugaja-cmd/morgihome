import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/snackbar.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool loading = true;
  List<dynamic> items = [];
  int unread = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => loading = true);
    try {
      final data = await ApiService().getNotifications();
      if (!mounted) return;
      setState(() {
        items = (data['notifications'] as List?) ?? [];
        unread = (data['unread'] as int?) ?? 0;
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => loading = false);
      showAppSnackBar(context, e.toString(), type: SnackBarType.error, title: 'Failed');
    }
  }

  Future<void> _markAll() async {
    await ApiService().markNotificationsRead();
    if (!mounted) return;
    showAppSnackBar(context, 'All notifications marked as read.', type: SnackBarType.success, title: 'Done');
    _load();
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(
            children: [
              Text('$unread new', style: const TextStyle(fontWeight: FontWeight.bold)),
              const Spacer(),
              TextButton.icon(onPressed: _markAll, icon: const Icon(Icons.check), label: const Text('Mark all as read')),
            ],
          ),
        ),
        Expanded(
          child: items.isEmpty
              ? const Center(child: Text('No notifications.'))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    itemCount: items.length,
                    itemBuilder: (c, i) {
                      final n = items[i] as Map;
                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        child: ListTile(
                          leading: Icon((n['read'] == true) ? Icons.notifications_none : Icons.notifications, color: const Color(0xFF0077B6)),
                          title: Text((n['title'] ?? '').toString()),
                          subtitle: Text((n['message'] ?? '').toString(), maxLines: 2, overflow: TextOverflow.ellipsis),
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
