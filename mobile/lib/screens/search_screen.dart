import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';
import '../widgets/property_card.dart';

/// Search — like web customer search: properties + quick page links.
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});
  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _api = ApiService();
  final _ctrl = TextEditingController();
  List<Property> _results = [];
  bool _loading = false;

  Future<void> _search() async {
    final q = _ctrl.text.trim();
    if (q.isEmpty) return;
    setState(() => _loading = true);
    try {
      final r = await _api.searchProperties(q: q);
      if (mounted) setState(() => _results = r);
    } catch (_) {
      if (mounted) setState(() => _results = []);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Search', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'search'),
      body: Column(children: [
        Container(
          color: Colors.white,
          padding: const EdgeInsets.all(16),
          child: TextField(
            controller: _ctrl,
            onSubmitted: (_) => _search(),
            decoration: InputDecoration(hintText: 'Search properties, banks, pages...', prefixIcon: const Icon(Icons.search), suffixIcon: IconButton(icon: const Icon(Icons.send), onPressed: _search)),
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(12),
          child: Wrap(spacing: 8, children: [
            _pageChip(context, 'Dashboard', '/dashboard'),
            _pageChip(context, 'Apply Mortgage', '/mortgage-apply'),
            _pageChip(context, 'My Applications', '/applications'),
            _pageChip(context, 'Bank Requirements', '/banks'),
            _pageChip(context, 'Property Verification', '/verify-property'),
          ]),
        ),
        Expanded(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _results.isEmpty
                  ? const Center(child: Text('Type and search — e.g. Tegeta, land, apartment'))
                  : GridView.builder(
                      padding: const EdgeInsets.all(12),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2, childAspectRatio: 0.68, crossAxisSpacing: 12, mainAxisSpacing: 12),
                      itemCount: _results.length,
                      itemBuilder: (context, i) => PropertyCard(property: _results[i], onTap: () => Navigator.pushNamed(context, '/property-detail', arguments: _results[i].id)),
                    ),
        ),
      ]),
    );
  }

  Widget _pageChip(BuildContext context, String label, String route) => ActionChip(label: Text(label, style: const TextStyle(fontSize: 12)), onPressed: () => Navigator.pushNamed(context, route));
}
