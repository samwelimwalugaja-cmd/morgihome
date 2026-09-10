import 'package:flutter/material.dart';
import '../models/property.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

class PropertyCard extends StatelessWidget {
  final Property property;
  final VoidCallback? onTap;
  const PropertyCard({super.key, required this.property, this.onTap});

  @override
  Widget build(BuildContext context) {
    final api = ApiService();
    final imageUrl = api.buildImageUrl(property.image ?? property.coverImageUrl);
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE5E7EB)),
          boxShadow: [
            BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 8, offset: const Offset(0, 2)),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image
            AspectRatio(
              aspectRatio: 1.5,
              child: Stack(
                children: [
                  Container(
                    width: double.infinity,
                    color: const Color(0xFFF3F4F6),
                    child: imageUrl.isNotEmpty
                        ? Image.network(imageUrl, fit: BoxFit.cover, errorBuilder: (_, __, ___) => const Icon(Icons.home, size: 40, color: Colors.grey))
                        : const Icon(Icons.home, size: 40, color: Colors.grey),
                  ),
                  Positioned(
                    top: 8,
                    left: 8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: property.status == 'available' ? const Color(0xFF28A745) : const Color(0xFFDC3545),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(property.status.toUpperCase(),
                          style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w600)),
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(property.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
                  const SizedBox(height: 4),
                  Row(children: [
                    const Icon(Icons.location_on, size: 12, color: Color(0xFF6B7280)),
                    const SizedBox(width: 4),
                    Expanded(child: Text(property.location, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Color(0xFF6B7280), fontSize: 12))),
                  ]),
                  const SizedBox(height: 6),
                  Row(children: [
                    _feature(Icons.bed, '${property.bedrooms}'),
                    const SizedBox(width: 8),
                    _feature(Icons.bathtub, '${property.bathrooms}'),
                    const SizedBox(width: 8),
                    _feature(Icons.square_foot, '${property.area} sqm'),
                  ]),
                  const SizedBox(height: 8),
                  Text(property.formattedPrice, style: const TextStyle(color: Color(AppConstants.primaryColorValue), fontWeight: FontWeight.w800, fontSize: 14)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _feature(IconData icon, String text) {
    return Row(children: [
      Icon(icon, size: 12, color: const Color(0xFF6B7280)),
      const SizedBox(width: 4),
      Text(text, style: const TextStyle(fontSize: 11, color: Color(0xFF6B7280))),
    ]);
  }
}
