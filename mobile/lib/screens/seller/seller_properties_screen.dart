import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';
import '../../models/property.dart';
import '../../services/api_service.dart';
import '../../utils/constants.dart';

/// My Properties like web seller properties (list + edit + delete).
class SellerPropertiesScreen extends StatefulWidget {
  const SellerPropertiesScreen({super.key});
  @override
  State<SellerPropertiesScreen> createState() => _SellerPropertiesScreenState();
}

class _SellerPropertiesScreenState extends State<SellerPropertiesScreen> {
  final _api = ApiService();
  List<Property> _props = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final list = await _api.getMyProperties();
      if (mounted) setState(() { _props = list; _loading = false; });
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
      }
    }
  }

  Future<void> _delete(Property p) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete property?'),
        content: Text('"${p.title}" will be removed permanently.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await _api.deleteProperty(p.id);
      if (!mounted) return;
      Fluttertoast.showToast(msg: 'Property deleted');
      _load();
    } catch (e) {
      Fluttertoast.showToast(msg: e.toString().replaceAll('Exception:', '').trim(), backgroundColor: const Color(AppConstants.errorColorValue));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: const Text('My Properties', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        actions: [
          IconButton(icon: const Icon(Icons.add, color: Colors.white), onPressed: () => Navigator.pushNamed(context, '/seller-property-form').then((_) => _load())),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _props.isEmpty
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                  const Icon(Icons.home_work_outlined, size: 64, color: Colors.grey),
                  const SizedBox(height: 12),
                  const Text('No properties yet', style: TextStyle(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: () => Navigator.pushNamed(context, '/seller-property-form').then((_) => _load()),
                    icon: const Icon(Icons.add),
                    label: const Text('Add Property'),
                    style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue), foregroundColor: Colors.white),
                  ),
                ]))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _props.length,
                    itemBuilder: (_, i) {
                      final p = _props[i];
                      final img = _api.buildImageUrl(p.coverImageUrl ?? p.image);
                      return Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                        child: InkWell(
                          onTap: () => Navigator.pushNamed(context, '/property-detail', arguments: p.id),
                          borderRadius: BorderRadius.circular(12),
                          child: Row(children: [
                            ClipRRect(
                              borderRadius: const BorderRadius.horizontal(left: Radius.circular(12)),
                              child: img.isNotEmpty
                                  ? Image.network(img, width: 110, height: 110, fit: BoxFit.cover, errorBuilder: (_, __, ___) => Container(width: 110, height: 110, color: Colors.grey.shade200, child: const Icon(Icons.home)))
                                  : Container(width: 110, height: 110, color: Colors.grey.shade200, child: const Icon(Icons.home)),
                            ),
                            Expanded(
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                                  Text(p.title, style: const TextStyle(fontWeight: FontWeight.w700), maxLines: 1, overflow: TextOverflow.ellipsis),
                                  Text(p.location, style: const TextStyle(color: Colors.grey, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                                  const SizedBox(height: 4),
                                  Text(p.formattedPrice, style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w800, fontSize: 13)),
                                  Text('${p.typeDisplay} • ${p.status}', style: const TextStyle(color: Colors.grey, fontSize: 11)),
                                ]),
                              ),
                            ),
                            Column(children: [
                              IconButton(icon: const Icon(Icons.edit, color: Color(AppConstants.primaryColorValue), size: 20), onPressed: () => Navigator.pushNamed(context, '/seller-property-form', arguments: p).then((_) => _load())),
                              IconButton(icon: const Icon(Icons.delete_outline, color: Colors.red, size: 20), onPressed: () => _delete(p)),
                            ]),
                          ]),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
