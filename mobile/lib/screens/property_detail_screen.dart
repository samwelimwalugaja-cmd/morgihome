import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../widgets/custom_button.dart';
import '../utils/constants.dart';

/// Full property detail like web: gallery, house/plot features, documents, seller.
class PropertyDetailScreen extends StatefulWidget {
  const PropertyDetailScreen({super.key});
  @override
  State<PropertyDetailScreen> createState() => _PropertyDetailScreenState();
}

class _PropertyDetailScreenState extends State<PropertyDetailScreen> {
  final _api = ApiService();
  Property? _property;
  bool _loading = true;
  String? _error;
  int _photoIndex = 0;
  String _role = 'customer';
  String? _myEmail;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final id = ModalRoute.of(context)!.settings.arguments as int?;
    if (id != null && _property == null && _error == null) _load(id);
  }

  Future<void> _load(int id) async {
    try {
      final user = await _api.getStoredUser();
      final p = await _api.getPropertyDetail(id);
      if (mounted) setState(() {
        _property = p;
        _loading = false;
        _role = user?.role ?? 'customer';
        _myEmail = user?.email;
      });
    } catch (e) {
      if (mounted) setState(() { _loading = false; _error = e.toString().replaceAll('Exception:', '').trim(); });
    }
  }

  /// Seller doesn't apply for mortgage - they only list property (like web).
  bool get _isSeller => _role == 'seller';
  bool get _isMine => _property != null && _myEmail != null && _myEmail!.isNotEmpty &&
      (_property!.sellerEmail ?? '').toLowerCase() == _myEmail!.toLowerCase();

  Future<void> _openDoc(String? path, String name) async {
    if (path == null || path.isEmpty) return;
    final uri = Uri.parse(_api.buildImageUrl(path));
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), iconTheme: const IconThemeData(color: Colors.white)),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_property == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Not found')),
        body: Center(child: Text(_error ?? 'Property not found')),
      );
    }
    final p = _property!;
    final photos = <String>[
      for (final g in p.gallery)
        if ((g.image ?? '').isNotEmpty) g.image!,
      if ((p.coverImageUrl ?? '').isNotEmpty) p.coverImageUrl!,
      if ((p.image ?? '').isNotEmpty) p.image!,
    ].toSet().toList();

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: const Color(AppConstants.secondaryColorValue),
        title: Text(p.title, style: const TextStyle(color: Colors.white, fontSize: 16)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Gallery
            SizedBox(
              height: 240,
              child: photos.isEmpty
                  ? Container(color: Colors.grey.shade200, child: const Center(child: Icon(Icons.home, size: 60, color: Colors.grey)))
                  : Stack(
                      children: [
                        PageView.builder(
                          itemCount: photos.length,
                          onPageChanged: (i) => setState(() => _photoIndex = i),
                          itemBuilder: (_, i) => Image.network(
                            _api.buildImageUrl(photos[i]),
                            fit: BoxFit.cover, width: double.infinity,
                            errorBuilder: (_, __, ___) => Container(color: Colors.grey.shade200, child: const Icon(Icons.home, size: 60)),
                          ),
                        ),
                        if (photos.length > 1)
                          Positioned(
                            bottom: 8, left: 0, right: 0,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: List.generate(photos.length, (i) => Container(
                                margin: const EdgeInsets.symmetric(horizontal: 3),
                                width: 8, height: 8,
                                decoration: BoxDecoration(shape: BoxShape.circle, color: i == _photoIndex ? Colors.white : Colors.white54),
                              )),
                            ),
                          ),
                      ],
                    ),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Expanded(child: Text(p.title, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800))),
                    _badge(p.status.toUpperCase(), p.status == 'available' ? const Color(0xFF15803D) : Colors.red),
                  ]),
                  const SizedBox(height: 4),
                  Row(children: [
                    _badge(p.typeDisplay, const Color(AppConstants.primaryColorValue)),
                    if ((p.napa ?? '').isNotEmpty) ...[
                      const SizedBox(width: 6),
                      _badge('NaPa: ${p.napa}', Colors.grey),
                    ],
                  ]),
                  const SizedBox(height: 8),
                  Row(children: [const Icon(Icons.location_on, size: 16, color: Colors.grey), const SizedBox(width: 4), Expanded(child: Text(p.location, style: const TextStyle(color: Colors.grey)))]),
                  const SizedBox(height: 8),
                  Text(p.formattedPrice, style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontSize: 22, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 16),
                  // Quick facts
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    if (!p.isPlot) ...[
                      _feat(Icons.bed, '${p.bedrooms} Beds'),
                      _feat(Icons.bathtub, '${p.bathrooms} Baths'),
                    ],
                    _feat(Icons.square_foot, '${p.area} sqm'),
                    if ((p.propertySize ?? '').isNotEmpty) _feat(Icons.home, '${p.propertySize} sqm house'),
                    if ((p.landSize ?? '').isNotEmpty) _feat(Icons.map, '${p.landSize} sqm land'),
                    if (p.parking > 0) _feat(Icons.local_parking, '${p.parking} Parking'),
                    if (p.yearBuilt != null) _feat(Icons.calendar_today, 'Built ${p.yearBuilt}'),
                  ]),
                  // House features
                  if (p.hasHouseFeatures) ...[
                    const SizedBox(height: 20),
                    _sectionTitle('House Features'),
                    const SizedBox(height: 8),
                    Wrap(spacing: 8, runSpacing: 8, children: [
                      if (p.furnished.isNotEmpty) _feat(Icons.weekend, 'Furnished: ${p.furnished}'),
                      if (p.propertyCondition.isNotEmpty) _feat(Icons.grade, p.propertyCondition),
                      if (p.floorNumber != null) _feat(Icons.layers, 'Floor ${p.floorNumber}${p.totalFloors != null ? '/${p.totalFloors}' : ''}'),
                      if (p.security) _feat(Icons.shield, 'Security'),
                      if (p.swimmingPool) _feat(Icons.pool, 'Pool'),
                      if (p.garden) _feat(Icons.park, 'Garden'),
                      if (p.balcony) _feat(Icons.balcony, 'Balcony'),
                      if (p.elevator) _feat(Icons.elevator, 'Elevator'),
                      if (p.airConditioning) _feat(Icons.ac_unit, 'AC'),
                      if (p.backupGenerator) _feat(Icons.power, 'Generator'),
                    ]),
                  ],
                  // Plot features
                  if (p.hasPlotFeatures || p.isPlot) ...[
                    const SizedBox(height: 20),
                    _sectionTitle('Plot Details'),
                    const SizedBox(height: 8),
                    if (p.landType.isNotEmpty) _kv('Land Type', p.landType),
                    if (p.plotDimensions.isNotEmpty) _kv('Dimensions', p.plotDimensions),
                    if (p.landUse.isNotEmpty) _kv('Land Use', p.landUse),
                    if (p.zoning.isNotEmpty) _kv('Zoning', p.zoning),
                    if (p.titleDeedAvailable.isNotEmpty) _kv('Title Deed', p.titleDeedAvailable),
                    if (p.surveyPlanAvailable.isNotEmpty) _kv('Survey Plan', p.surveyPlanAvailable),
                    const SizedBox(height: 8),
                    Wrap(spacing: 8, runSpacing: 8, children: [
                      if (p.infraRoad) _feat(Icons.add_road, 'Road'),
                      if (p.infraElectricity) _feat(Icons.flash_on, 'Electricity'),
                      if (p.infraWater) _feat(Icons.water_drop, 'Water'),
                      if (p.infraSewage) _feat(Icons.plumbing, 'Sewage'),
                      if (p.infraInternet) _feat(Icons.wifi, 'Internet'),
                      if (p.infraFenced) _feat(Icons.fence, 'Fenced'),
                    ]),
                  ],
                  const SizedBox(height: 20),
                  _sectionTitle('Description'),
                  const SizedBox(height: 8),
                  Text(p.description.isNotEmpty ? p.description : 'No description provided.', style: const TextStyle(color: Colors.grey, height: 1.5)),
                  // Documents
                  if (p.titleDeedFile != null || p.surveyPlanFile != null || p.taxClearanceFile != null || p.landCertificateFile != null || p.buildingPermitFile != null) ...[
                    const SizedBox(height: 20),
                    _sectionTitle('Documents'),
                    const SizedBox(height: 8),
                    _doc('Title Deed', p.titleDeedFile),
                    _doc('Survey Plan', p.surveyPlanFile),
                    _doc('Tax Clearance', p.taxClearanceFile),
                    _doc('Land Certificate', p.landCertificateFile),
                    _doc('Building Permit', p.buildingPermitFile),
                  ],
                  // Seller
                  if (p.sellerName != null) ...[
                    const SizedBox(height: 20),
                    _sectionTitle('Seller'),
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: const Color(0xFFF9FAFB), borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
                      child: Row(children: [
                        const CircleAvatar(child: Icon(Icons.person)),
                        const SizedBox(width: 12),
                        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text(p.sellerName!, style: const TextStyle(fontWeight: FontWeight.w700)),
                          if ((p.sellerPhone ?? '').isNotEmpty) Text(p.sellerPhone!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                          if ((p.sellerEmail ?? '').isNotEmpty) Text(p.sellerEmail!, style: const TextStyle(color: Colors.grey, fontSize: 12)),
                        ])),
                      ]),
                    ),
                  ],
                  const SizedBox(height: 24),
                  // Only customer applies (mortgage applicant). Seller: edit if it's theirs.
                  if (!_isSeller)
                    CustomButton(text: 'Apply for Mortgage', icon: Icons.description, onPressed: () => Navigator.pushNamed(context, '/mortgage-apply', arguments: p)),
                  if (_isSeller && _isMine)
                    CustomButton(text: 'Edit Property', icon: Icons.edit, onPressed: () => Navigator.pushNamed(context, '/seller-property-form', arguments: p)),
                  if (_isSeller && !_isMine)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: const Color(0xFFF9FAFB), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE5E7EB))),
                      child: const Row(children: [Icon(Icons.info_outline, size: 18, color: Colors.grey), SizedBox(width: 8), Expanded(child: Text('Sellers list properties — mortgage applications are for customers.', style: TextStyle(fontSize: 12, color: Colors.grey)))]),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _sectionTitle(String t) => Text(t, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16));

  Widget _badge(String text, Color color) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20), border: Border.all(color: color.withValues(alpha: 0.3))),
        child: Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w700)),
      );

  Widget _feat(IconData icon, String text) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(color: const Color(0xFFF3F4F6), borderRadius: BorderRadius.circular(20)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [Icon(icon, size: 16, color: const Color(AppConstants.primaryColorValue)), const SizedBox(width: 6), Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600))]),
      );

  Widget _kv(String k, String v) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(children: [
          Expanded(child: Text(k, style: const TextStyle(color: Colors.grey, fontSize: 13))),
          Text(v, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ]),
      );

  Widget _doc(String name, String? path) {
    if (path == null || path.isEmpty) return const SizedBox.shrink();
    return InkWell(
      onTap: () => _openDoc(path, name),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Row(children: [
          const Icon(Icons.picture_as_pdf, color: Color(AppConstants.primaryColorValue)),
          const SizedBox(width: 10),
          Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
          const Icon(Icons.open_in_new, size: 16, color: Colors.grey),
        ]),
      ),
    );
  }
}
