import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../utils/constants.dart';
import '../widgets/customer_drawer.dart';

/// Property Verification — like web customer_verify_property:
/// copy Title/NAPA code then verify on official e-Ardhi portal.
class VerifyPropertyScreen extends StatelessWidget {
  const VerifyPropertyScreen({super.key});
  static const portal = 'https://eardhi.lands.go.tz/';

  Future<void> _open() async {
    final uri = Uri.parse(portal);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF9FAFB),
      appBar: AppBar(backgroundColor: const Color(AppConstants.secondaryColorValue), title: const Text('Property Verification', style: TextStyle(color: Colors.white)), iconTheme: const IconThemeData(color: Colors.white)),
      drawer: const CustomerDrawer(active: 'verify'),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(color: const Color(AppConstants.secondaryColorValue), borderRadius: BorderRadius.circular(16)),
            child: Column(children: [
              const Icon(Icons.shield_outlined, color: Colors.white, size: 48),
              const SizedBox(height: 8),
              const Text('Verify Property Ownership', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 17)),
              const SizedBox(height: 6),
              const Text('Copy the Title Number / Plot No / NAPA Code from the property, then verify it on the official Ministry of Lands portal (e-Ardhi).', textAlign: TextAlign.center, style: TextStyle(color: Colors.white70, fontSize: 13)),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity, height: 50,
                child: ElevatedButton.icon(onPressed: _open, icon: const Icon(Icons.verified), label: const Text('Go to e-Ardhi Portal — Verify Document'), style: ElevatedButton.styleFrom(backgroundColor: const Color(AppConstants.primaryColorValue))),
              ),
              const SizedBox(height: 8),
              const Text('https://eardhi.lands.go.tz/ — Official Ministry of Lands', style: TextStyle(color: Colors.white54, fontSize: 11)),
            ]),
          ),
          const SizedBox(height: 16),
          _step('1', 'Copy Property Code', 'Go to Properties → View Details → copy the Title Number / NAPA / Plot No.'),
          _step('2', 'Go to Portal & Verify', 'Tap the button above. On the portal click Verify Document, then paste the code.'),
          _step('3', 'View Official Information', 'The portal shows official title info so you can confirm it is valid. Verification only — no download needed.'),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: const Color(0xFFF0F9FF), borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFBFDBFE))),
            child: const Row(children: [Icon(Icons.lightbulb, color: Color(0xFFF59E0B)), SizedBox(width: 8), Expanded(child: Text('Tip: if you do not have the title code, contact the seller or agent. MorgiHome does not store your title — verification is via e-Ardhi only.', style: TextStyle(fontSize: 12, color: Colors.grey)))]),
          ),
        ],
      ),
    );
  }

  Widget _step(String n, String title, String body) => Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE5E7EB))),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(width: 32, height: 32, decoration: const BoxDecoration(color: Color(AppConstants.primaryColorValue), shape: BoxShape.circle), child: Center(child: Text(n, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)))),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w700)), const SizedBox(height: 2), Text(body, style: const TextStyle(color: Colors.grey, fontSize: 13))])),
        ]),
      );
}
