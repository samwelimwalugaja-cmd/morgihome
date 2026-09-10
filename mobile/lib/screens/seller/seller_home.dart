import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../utils/constants.dart';

/// Seller dashboard like web: stats + quick actions.
class SellerHomeScreen extends StatefulWidget {
  const SellerHomeScreen({super.key});
  @override
  State<SellerHomeScreen> createState() => _SellerHomeScreenState();
}

class _SellerHomeScreenState extends State<SellerHomeScreen> {
  final _api = ApiService();
  bool _loading = true;
  int _properties = 0;
  int _available = 0;
  int _buyers = 0;
  int _contracts = 0;
  double _revenue = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final props = await _api.getMyProperties();
      var buyers = 0;
      try {
        buyers = (await _api.getMyApplications()).length;
      } catch (_) {}
      var contracts = 0;
      var revenue = 0.0;
      try {
        final list = await _api.getMyContracts();
        contracts = list.length;
        for (final c in list) {
          if (c.status == 'executed') revenue += double.tryParse(c.loanAmount ?? '0') ?? 0;
        }
      } catch (_) {}
      if (!mounted) return;
      setState(() {
        _properties = props.length;
        _available = props.where((p) => p.status == 'available').length;
        _buyers = buyers;
        _contracts = contracts;
        _revenue = revenue;
        _loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _logout() async {
    await _api.logout();
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/welcome');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: const Text('Seller Dashboard', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
        centerTitle: true,
        actions: [
          IconButton(icon: const Icon(Icons.logout, color: Colors.white), onPressed: _logout),
        ],
      ),
      drawer: _drawer(context),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Overview', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 12),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.4,
                    children: [
                      _stat(Icons.home_work, '$_properties', 'My Properties', const Color(AppConstants.primaryColorValue)),
                      _stat(Icons.check_circle, '$_available', 'Available', const Color(0xFF28A745)),
                      _stat(Icons.group, '$_buyers', 'Interested Buyers', const Color(0xFFFFC107)),
                      _stat(Icons.handshake, '$_contracts', 'Contracts', const Color(0xFF7C3AED)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: const Color(AppConstants.secondaryColorValue), borderRadius: BorderRadius.circular(12)),
                    child: Row(children: [
                      const Icon(Icons.payments, color: Colors.white, size: 32),
                      const SizedBox(width: 12),
                      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        const Text('Total Revenue', style: TextStyle(color: Colors.white70, fontSize: 12)),
                        Text('TZS ${_revenue.toStringAsFixed(0)}', style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
                      ]),
                    ]),
                  ),
                  const SizedBox(height: 20),
                  const Text('Quick Actions', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 12),
                  _action(context, Icons.add_home, 'Add Property', '/seller-property-form'),
                  _action(context, Icons.list_alt, 'My Properties', '/seller-properties'),
                  _action(context, Icons.group, 'Interested Buyers', '/seller-buyers'),
                  _action(context, Icons.handshake, 'My Contracts', '/contracts'),
                  _action(context, Icons.trending_up, 'Sales', '/seller-sales'),
                  _action(context, Icons.person, 'Profile', '/profile'),
                ]),
              ),
            ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: 0,
        selectedItemColor: const Color(AppConstants.primaryColorValue),
        type: BottomNavigationBarType.fixed,
        onTap: (i) {
          if (i == 1) Navigator.pushNamed(context, '/seller-properties');
          if (i == 2) Navigator.pushNamed(context, '/seller-buyers');
          if (i == 3) Navigator.pushNamed(context, '/profile');
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.home_work), label: 'Properties'),
          BottomNavigationBarItem(icon: Icon(Icons.group), label: 'Buyers'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }

  Widget _stat(IconData icon, String value, String label, Color color) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 6),
          Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        ]),
      );

  Widget _action(BuildContext context, IconData icon, String title, String route) => InkWell(
        onTap: () => Navigator.pushNamed(context, route),
        child: Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE5E7EB))),
          child: Row(children: [
            Container(width: 38, height: 38, decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(8)), child: Icon(icon, color: const Color(AppConstants.primaryColorValue), size: 20)),
            const SizedBox(width: 12),
            Expanded(child: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14))),
            const Icon(Icons.chevron_right, color: Colors.grey),
          ]),
        ),
      );

  Widget _drawer(BuildContext context) => Drawer(
        child: ListView(padding: EdgeInsets.zero, children: [
          DrawerHeader(
            decoration: const BoxDecoration(color: Color(AppConstants.secondaryColorValue)),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
                child: Image.asset('assets/images/morgihome_logo.png', height: 34, fit: BoxFit.contain, errorBuilder: (_, __, ___) => const Icon(Icons.store, color: Color(AppConstants.primaryColorValue), size: 34)),
              ),
              const SizedBox(height: 8),
              const Text('Seller Portal', style: TextStyle(color: Colors.white70, fontSize: 12)),
            ]),
          ),
          _drawerItem(context, Icons.dashboard, 'Dashboard', '/seller'),
          _drawerItem(context, Icons.home_work, 'My Properties', '/seller-properties'),
          _drawerItem(context, Icons.add_home, 'Add Property', '/seller-property-form'),
          _drawerItem(context, Icons.group, 'Interested Buyers', '/seller-buyers'),
          _drawerItem(context, Icons.handshake, 'My Contracts', '/contracts'),
          _drawerItem(context, Icons.trending_up, 'Sales', '/seller-sales'),
          _drawerItem(context, Icons.person, 'Profile', '/profile'),
          const Divider(),
          ListTile(leading: const Icon(Icons.logout, color: Colors.red), title: const Text('Logout'), onTap: _logout),
        ]),
      );

  Widget _drawerItem(BuildContext context, IconData icon, String title, String route) => ListTile(
        leading: Icon(icon, color: const Color(AppConstants.primaryColorValue)),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        onTap: () {
          Navigator.pop(context);
          if (route == '/seller') return;
          Navigator.pushNamed(context, route);
        },
      );
}
