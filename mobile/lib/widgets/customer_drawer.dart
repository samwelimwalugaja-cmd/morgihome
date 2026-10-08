import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

/// Mortgage-applicant sidebar — mirrors web (customer_base.html) exactly:
/// Dashboard, Bank Requirements (pilot: NCBA only), Check Eligibility, Properties,
/// Apply Mortgage (4 types), My Applications, My Contracts, Repayment Schedule,
/// Search, Notifications, Profile, Logout.
class CustomerDrawer extends StatelessWidget {
  final String active;
  const CustomerDrawer({super.key, this.active = ''});

  static const applyTypes = [
    {'label': 'Residential Mortgage', 'value': 'residential'},
    {'label': 'Home Construction', 'value': 'construction'},
    {'label': 'Renovation Mortgage', 'value': 'renovation'},
    {'label': 'Commercial Property', 'value': 'commercial'},
  ];

  static const bankFilters = [
    {'label': 'NCBA Bank (Pilot)', 'value': 'ncba'},
  ];

  @override
  Widget build(BuildContext context) {
    final api = ApiService();
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(color: Color(AppConstants.secondaryColorValue)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                child: Image.asset('assets/images/morgihome_logo.png', height: 34, fit: BoxFit.contain, errorBuilder: (_, __, ___) => const Icon(Icons.home_work, color: Color(AppConstants.primaryColorValue), size: 34)),
              ),
              const SizedBox(height: 8),
              const Text('MorgiHome', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 16)),
              const Text('MORTGAGE PORTAL • Mortgage Applicant', style: TextStyle(color: Colors.white70, fontSize: 11)),
            ]),
          ),
          const Padding(padding: EdgeInsets.fromLTRB(16, 8, 16, 4), child: Text('MAIN', style: TextStyle(color: Colors.grey, fontSize: 11, letterSpacing: 1))),
          _item(context, Icons.dashboard, 'Dashboard', '/dashboard', isActive: active == 'dashboard'),
          _item(context, Icons.account_balance, 'Bank Requirements (NCBA)', '/banks', isActive: active == 'banks'),
          _item(context, Icons.verified_user, 'Check Eligibility', '/eligibility', isActive: active == 'eligibility'),
          _item(context, Icons.home, 'Properties', '/home', isActive: active == 'home'),
          ExpansionTile(
            leading: const Icon(Icons.add_circle, color: Color(AppConstants.primaryColorValue)),
            title: const Text('Apply Mortgage', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
            initiallyExpanded: active == 'apply',
            children: applyTypes
                .map((t) => ListTile(
                      contentPadding: const EdgeInsets.only(left: 56, right: 16),
                      title: Text(t['label']!, style: const TextStyle(fontSize: 13)),
                      trailing: const Icon(Icons.chevron_right, size: 16, color: Colors.grey),
                      onTap: () {
                        Navigator.pop(context);
                        Navigator.pushNamed(context, '/mortgage-apply', arguments: {'mortgage_type': t['value']});
                      },
                    ))
                .toList(),
          ),
          _item(context, Icons.description, 'My Applications', '/applications', isActive: active == 'applications'),
          _item(context, Icons.handshake, 'My Contracts', '/contracts', isActive: active == 'contracts'),
          _item(context, Icons.calendar_month, 'Repayment Schedule', '/repayment', isActive: active == 'repayment'),
          const Padding(padding: EdgeInsets.fromLTRB(16, 8, 16, 4), child: Text('SYSTEM', style: TextStyle(color: Colors.grey, fontSize: 11, letterSpacing: 1))),
          _item(context, Icons.search, 'Search', '/search', isActive: active == 'search'),
          _item(context, Icons.notifications, 'Notifications', '/notifications', isActive: active == 'notifications'),
          _item(context, Icons.person, 'Profile', '/profile', isActive: active == 'profile'),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.logout, color: Colors.red),
            title: const Text('Logout'),
            onTap: () async {
              final nav = Navigator.of(context);
              await api.logout();
              nav.pushNamedAndRemoveUntil('/welcome', (_) => false);
            },
          ),
        ],
      ),
    );
  }

  Widget _item(BuildContext context, IconData icon, String title, String route, {bool isActive = false}) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8),
      decoration: isActive ? BoxDecoration(color: const Color(AppConstants.primaryColorValue).withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)) : null,
      child: ListTile(
        leading: Icon(icon, color: const Color(AppConstants.primaryColorValue)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
        onTap: () {
          Navigator.pop(context);
          if (ModalRoute.of(context)?.settings.name == route) return;
          Navigator.pushNamed(context, route);
        },
      ),
    );
  }
}
