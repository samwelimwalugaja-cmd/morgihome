import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/property.dart';
import 'property_detail_screen.dart';

/// Search parity with web (properties + banks hint).
class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _c = TextEditingController();
  bool loading = false;
  List<Property> results = [];

  Future<void> _search() async {
    final q = _c.text.trim().toLowerCase();
    if (q.isEmpty) return;
    setState(() => loading = true);
    try {
      final all = await ApiService().getProperties();
      if (!mounted) return;
      setState(() {
        results = all.where((p) => p.title.toLowerCase().contains(q) || p.location.toLowerCase().contains(q)).toList();
        loading = false;
      });
    } catch (_) {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(child: TextField(controller: _c, decoration: const InputDecoration(labelText: 'Search properties, location...'), onSubmitted: (_) => _search())),
              IconButton(onPressed: _search, icon: const Icon(Icons.search)),
            ],
          ),
          const SizedBox(height: 8),
          if (loading) const CircularProgressIndicator(),
          Expanded(
            child: ListView.builder(
              itemCount: results.length,
              itemBuilder: (c, i) {
                final p = results[i];
                return Card(child: ListTile(title: Text(p.title), subtitle: Text(p.location), onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => PropertyDetailScreen(property: p)))));
              },
            ),
          ),
        ],
      ),
    );
  }
}
