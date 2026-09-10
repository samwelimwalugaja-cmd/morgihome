import 'package:flutter/material.dart';
import '../models/property.dart';
import '../utils/session.dart';
import 'mortgage_application_screen.dart';

class PropertyDetailScreen extends StatelessWidget {
  final Property property;

  const PropertyDetailScreen({super.key, required this.property});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(property.title)),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              height: 220,
              width: double.infinity,
              color: Colors.grey[300],
              child: property.image != null
                  ? Image.network(property.image!, fit: BoxFit.cover)
                  : const Icon(Icons.home, size: 80, color: Colors.grey),
            ),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    property.title,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF0A2B4E),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${property.price.toStringAsFixed(0)} TZS',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF0077B6),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.location_on, color: Colors.grey),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          property.location,
                          style: const TextStyle(fontSize: 16),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.bed, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text('${property.bedrooms} Bedrooms'),
                      const SizedBox(width: 24),
                      const Icon(Icons.bathtub, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text('${property.bathrooms} Bathrooms'),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.square_foot, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text('${property.area.toStringAsFixed(0)} sqm'),
                      const SizedBox(width: 24),
                      const Icon(Icons.category, color: Colors.grey),
                      const SizedBox(width: 6),
                      Text(property.propertyType),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Description',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    property.description,
                    style: const TextStyle(fontSize: 15, color: Colors.black87),
                  ),
                  const SizedBox(height: 24),
                  FutureBuilder<String>(
                    future: Session.role(),
                    builder: (c, s) {
                      final role = s.data ?? 'customer';
                      if (role != 'customer') {
                        return Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(8)),
                          child: Text('Viewing as ${role.toUpperCase()} — mortgage application is for customers only.', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                        );
                      }
                      return ElevatedButton(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) =>
                                  MortgageApplicationScreen(property: property),
                            ),
                          );
                        },
                        child: const Text('Apply for Mortgage'),
                      );
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
