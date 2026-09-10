import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/property.dart';
import '../widgets/customer_drawer.dart';
import '../widgets/property_card.dart';
import '../widgets/loading_spinner.dart';
import '../utils/constants.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _api = ApiService();
  final _searchCtrl = TextEditingController();
  List<Property> _properties = [];
  List<Property> _filtered = [];
  bool _loading = true;
  String _selectedType = '';
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final props = await _api.getProperties();
      setState(() {
        _properties = props;
        _filtered = props;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  void _filter(String type) {
    setState(() {
      _selectedType = type == _selectedType ? '' : type;
      _applyFilter();
    });
  }

  void _applyFilter() {
    final q = _searchCtrl.text.toLowerCase();
    setState(() {
      _filtered = _properties.where((p) {
        final matchSearch = q.isEmpty || p.title.toLowerCase().contains(q) || p.location.toLowerCase().contains(q);
        final matchType = _selectedType.isEmpty || p.propertyType.toLowerCase() == _selectedType.toLowerCase();
        return matchSearch && matchType;
      }).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: const Text('MorgiHome', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
        centerTitle: true,
        actions: [
          IconButton(icon: const Icon(Icons.logout, color: Colors.white), onPressed: () async { final nav = Navigator.of(context); await _api.logout(); if (mounted) nav.pushReplacementNamed('/login'); }),
        ],
      ),
      drawer: const CustomerDrawer(active: 'home'),
      body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: _searchCtrl,
                  onChanged: (_) => _applyFilter(),
                  decoration: InputDecoration(
                    hintText: 'Search properties...',
                    prefixIcon: const Icon(Icons.search),
                    filled: true,
                    fillColor: const Color(0xFFF3F4F6),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 36,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    children: [
                      _filterChip('All', ''),
                      _filterChip('House', 'house'),
                      _filterChip('Apartment', 'apartment'),
                      _filterChip('Land', 'land'),
                      _filterChip('Commercial', 'commercial'),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const PropertyShimmer()
                : _filtered.isEmpty
                    ? const Center(child: Text('No properties found'))
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: GridView.builder(
                          padding: const EdgeInsets.all(12),
                          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, childAspectRatio: 0.68, crossAxisSpacing: 12, mainAxisSpacing: 12),
                          itemCount: _filtered.length,
                          itemBuilder: (context, i) => PropertyCard(
                            property: _filtered[i],
                            onTap: () => Navigator.pushNamed(context, '/property-detail', arguments: _filtered[i].id),
                          ),
                        ),
                      ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        selectedItemColor: const Color(AppConstants.primaryColorValue),
        onTap: (i) {
          setState(() => _currentIndex = i);
          if (i == 1) Navigator.pushNamed(context, '/applications');
          if (i == 2) Navigator.pushNamed(context, '/profile');
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.description), label: 'Applications'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }

  Widget _filterChip(String label, String value) {
    final selected = _selectedType == value || (_selectedType.isEmpty && value.isEmpty && label == 'All');
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label),
        selected: selected,
        selectedColor: const Color(AppConstants.primaryColorValue),
        labelStyle: TextStyle(color: selected ? Colors.white : Colors.black87, fontWeight: FontWeight.w600, fontSize: 12),
        backgroundColor: const Color(0xFFF3F4F6),
        onSelected: (_) => _filter(value),
      ),
    );
  }
}
