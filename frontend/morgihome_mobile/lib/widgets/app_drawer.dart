import 'package:flutter/material.dart';
import '../utils/session.dart';
import '../services/api_service.dart';

/// Role drawer mirroring web sidebars (customer/seller/realestate/bank).
class AppDrawer extends StatelessWidget {
  final String role;
  final Function(String route) onNavigate;
  const AppDrawer({super.key, required this.role, required this.onNavigate});

  List<Map<String, dynamic>> _menu() {
    switch (role) {
      case 'seller':
        return [
          {'label': 'Dashboard', 'icon': Icons.dashboard, 'route': 'dashboard'},
          {'label': 'My Properties', 'icon': Icons.home, 'route': 'properties'},
          {'label': 'Add Property', 'icon': Icons.add_home, 'route': 'property_add'},
          {'label': 'Interested Buyers', 'icon': Icons.group, 'route': 'buyers'},
          {'label': 'My Contracts', 'icon': Icons.description, 'route': 'contracts'},
          {'label': 'Sales', 'icon': Icons.attach_money, 'route': 'reports'},
          {'label': 'Notifications', 'icon': Icons.notifications, 'route': 'notifications'},
          {'label': 'Search', 'icon': Icons.search, 'route': 'search'},
          {'label': 'Profile', 'icon': Icons.person, 'route': 'profile'},
        ];
      case 'bank':
        return [
          {'label': 'Dashboard', 'icon': Icons.dashboard, 'route': 'dashboard'},
          {'label': 'Applications', 'icon': Icons.description, 'route': 'applications'},
          {'label': 'Contracts', 'icon': Icons.file_copy, 'route': 'contracts'},
          {'label': 'Partner Reports', 'icon': Icons.bar_chart, 'route': 'reports'},
          {'label': 'Notifications', 'icon': Icons.notifications, 'route': 'notifications'},
          {'label': 'Search', 'icon': Icons.search, 'route': 'search'},
          {'label': 'Profile', 'icon': Icons.person, 'route': 'profile'},
        ];
      case 'realestate':
        return [
          {'label': 'Dashboard', 'icon': Icons.dashboard, 'route': 'dashboard'},
          {'label': 'Properties', 'icon': Icons.home, 'route': 'properties'},
          {'label': 'Add Property', 'icon': Icons.add_home, 'route': 'property_add'},
          {'label': 'Buyers', 'icon': Icons.group, 'route': 'buyers'},
          {'label': 'Applications', 'icon': Icons.description, 'route': 'applications'},
          {'label': 'Contracts', 'icon': Icons.file_copy, 'route': 'contracts'},
          {'label': 'Partner Banks', 'icon': Icons.account_balance, 'route': 'banks'},
          {'label': 'Reports', 'icon': Icons.bar_chart, 'route': 'reports'},
          {'label': 'Notifications', 'icon': Icons.notifications, 'route': 'notifications'},
          {'label': 'Search', 'icon': Icons.search, 'route': 'search'},
          {'label': 'Profile', 'icon': Icons.person, 'route': 'profile'},
        ];
      default: // customer
        return [
          {'label': 'Dashboard', 'icon': Icons.dashboard, 'route': 'dashboard'},
          {'label': 'Properties', 'icon': Icons.home, 'route': 'properties'},
          {'label': 'Apply Mortgage', 'icon': Icons.edit_document, 'route': 'apply'},
          {'label': 'My Applications', 'icon': Icons.description, 'route': 'applications'},
          {'label': 'My Contracts', 'icon': Icons.file_copy, 'route': 'contracts'},
          {'label': 'Bank Requirements', 'icon': Icons.account_balance, 'route': 'banks'},
          {'label': 'Notifications', 'icon': Icons.notifications, 'route': 'notifications'},
          {'label': 'Search', 'icon': Icons.search, 'route': 'search'},
          {'label': 'Profile', 'icon': Icons.person, 'route': 'profile'},
        ];
    }
  }

  String _roleLabel() {
    switch (role) {
      case 'seller':
        return 'SELLER PORTAL';
      case 'bank':
        return 'BANK PORTAL';
      case 'realestate':
        return 'REAL ESTATE PORTAL';
      default:
        return 'CUSTOMER PORTAL';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(16, 48, 16, 16),
            color: const Color(0xFF0A2B4E),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.home_work, color: Colors.white, size: 28),
                    SizedBox(width: 8),
                    Text('MorgiHome', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18)),
                  ],
                ),
                const SizedBox(height: 4),
                Text(_roleLabel(), style: const TextStyle(color: Colors.white70, fontSize: 10, letterSpacing: 1.5)),
                const SizedBox(height: 12),
                FutureBuilder<String>(
                  future: Session.displayName(),
                  builder: (c, s) => Text(s.data ?? '', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: [
                for (final m in _menu())
                  ListTile(
                    leading: Icon(m['icon'] as IconData, color: const Color(0xFF0077B6)),
                    title: Text(m['label'] as String),
                    onTap: () {
                      Navigator.pop(context);
                      onNavigate(m['route'] as String);
                    },
                  ),
                const Divider(),
                ListTile(
                  leading: const Icon(Icons.logout, color: Colors.red),
                  title: const Text('Logout'),
                  onTap: () async {
                    await ApiService().logout();
                    Session.clearCache();
                    if (context.mounted) Navigator.pushReplacementNamed(context, '/login');
                  },
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.all(8),
            child: Text('MorgiHome v1.0 • Brain-Wave', style: TextStyle(fontSize: 10, color: Colors.grey)),
          ),
        ],
      ),
    );
  }
}
