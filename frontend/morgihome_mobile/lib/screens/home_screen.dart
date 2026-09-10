import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/property.dart';
import '../utils/session.dart';
import '../utils/snackbar.dart';
import '../widgets/app_drawer.dart';
import 'property_detail_screen.dart';
import 'profile_screen.dart';
import 'dashboard_screen.dart';
import 'applications_screen.dart';
import 'banks_screen.dart';
import 'notifications_screen.dart';
import 'contracts_screen.dart';
import 'buyers_screen.dart';
import 'reports_screen.dart';
import 'search_screen.dart';
import 'property_form_screen.dart';

/// Role shell parity with web sidebars + same data via same APIs.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _role = 'customer';
  String _route = 'dashboard';
  List<Property> _properties = [];
  bool _isLoading = true;
  String? _errorMsg;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    final r = await Session.role();
    if (!mounted) return;
    setState(() => _role = r);
    _loadProperties();
  }

  Future<void> _loadProperties() async {
    setState(() {
      _isLoading = true;
      _errorMsg = null;
    });
    try {
      final properties = (_role == 'seller' || _role == 'realestate')
          ? await ApiService().getMyProperties()
          : await ApiService().getProperties();
      if (!mounted) return;
      setState(() {
        _properties = properties;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      final msg = e.toString().replaceAll('Exception: ', '');
      setState(() {
        _isLoading = false;
        _errorMsg = msg;
      });
      showAppSnackBar(context, msg, type: SnackBarType.error, title: 'Failed to load properties');
    }
  }

  String _resolveImageUrl(String url) {
    if (url.startsWith('http')) return url;
    final base = ApiService.baseUrl;
    final origin = base.replaceAll('/api/', '');
    if (url.startsWith('/')) return '$origin$url';
    return '$origin/$url';
  }

  String _title() {
    switch (_route) {
      case 'dashboard':
        return 'MorgiHome • ${_role.toUpperCase()}';
      case 'properties':
        return _role == 'seller' ? 'My Properties' : 'Properties';
      case 'applications':
        return 'Applications';
      case 'banks':
        return _role == 'customer' ? 'Bank Requirements' : 'Partner Banks';
      case 'notifications':
        return 'Notifications';
      case 'contracts':
        return 'Contracts';
      case 'buyers':
        return 'Buyers';
      case 'reports':
        return 'Reports';
      case 'search':
        return 'Search';
      case 'profile':
        return 'Profile';
      case 'apply':
        return 'Apply Mortgage';
      case 'property_add':
        return 'Add Property';
      default:
        return 'MorgiHome';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_title()),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            onPressed: () => setState(() => _route = 'notifications'),
          ),
        ],
      ),
      drawer: AppDrawer(role: _role, onNavigate: (r) => setState(() => _route = r)),
      body: _buildBody(),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _route == 'dashboard' ? 0 : (_route == 'search' ? 1 : 2),
        onTap: (i) => setState(() => _route = i == 0 ? 'dashboard' : (i == 1 ? 'search' : 'profile')),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Search'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
      floatingActionButton: (_route == 'properties' && (_role == 'seller' || _role == 'realestate'))
          ? FloatingActionButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PropertyFormScreen())),
              child: const Icon(Icons.add),
            )
          : null,
    );
  }

  Widget _buildBody() {
    switch (_route) {
      case 'dashboard':
        return DashboardScreen(role: _role);
      case 'applications':
        return ApplicationsScreen(role: _role);
      case 'banks':
        return BanksScreen(role: _role);
      case 'notifications':
        return const NotificationsScreen();
      case 'contracts':
        return const ContractsScreen();
      case 'buyers':
        return const BuyersScreen();
      case 'reports':
        return const ReportsScreen();
      case 'search':
        return const SearchScreen();
      case 'profile':
        return const ProfileScreen();
      case 'property_add':
        return const PropertyFormScreen();
      case 'properties':
        return _buildProperties();
      default:
        return _buildProperties();
    }
  }

  Widget _buildProperties() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_errorMsg != null && _properties.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.redAccent),
              const SizedBox(height: 12),
              Text(_errorMsg!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton.icon(onPressed: _loadProperties, icon: const Icon(Icons.refresh), label: const Text('Jaribu tena')),
            ],
          ),
        ),
      );
    }
    if (_properties.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.home_outlined, size: 64, color: Colors.grey),
            const SizedBox(height: 12),
            const Text('No properties available'),
            const SizedBox(height: 16),
            ElevatedButton.icon(onPressed: _loadProperties, icon: const Icon(Icons.refresh), label: const Text('Refresh')),
          ],
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _loadProperties,
      child: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, childAspectRatio: 0.75, crossAxisSpacing: 12, mainAxisSpacing: 12),
        itemCount: _properties.length,
        itemBuilder: (context, index) {
          final property = _properties[index];
          return GestureDetector(
            onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => PropertyDetailScreen(property: property))),
            child: Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    height: 120,
                    decoration: BoxDecoration(
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                      color: Colors.grey[300],
                      image: property.image != null && property.image!.isNotEmpty
                          ? DecorationImage(image: NetworkImage(_resolveImageUrl(property.image!)), fit: BoxFit.cover)
                          : null,
                    ),
                    child: property.image == null ? const Icon(Icons.home, size: 50, color: Colors.grey) : null,
                  ),
                  Padding(
                    padding: const EdgeInsets.all(8),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(property.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                        const SizedBox(height: 4),
                        Text('${property.price.toStringAsFixed(0)} TZS • ${property.status}', style: const TextStyle(color: Color(0xFF0077B6), fontWeight: FontWeight.bold, fontSize: 11)),
                        const SizedBox(height: 4),
                        Text(property.location, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 10, color: Colors.grey)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
