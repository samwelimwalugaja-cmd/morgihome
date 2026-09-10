import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Session helper: role + user parity with web (customer/seller/bank/realestate)
class Session {
  static Map<String, dynamic>? _cachedUser;

  static Future<Map<String, dynamic>?> currentUser() async {
    if (_cachedUser != null) return _cachedUser;
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('user_json');
    if (raw == null || raw.isEmpty) return null;
    try {
      _cachedUser = jsonDecode(raw) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
    return _cachedUser;
  }

  static Future<String> role() async {
    final u = await currentUser();
    final r = (u?['role'] ?? '').toString().toLowerCase();
    if (['customer', 'seller', 'bank', 'realestate'].contains(r)) return r;
    return 'customer';
  }

  static Future<String> displayName() async {
    final u = await currentUser();
    final fn = (u?['first_name'] ?? '').toString();
    final ln = (u?['last_name'] ?? '').toString();
    final full = '$fn $ln'.trim();
    if (full.isNotEmpty) return full;
    return (u?['email'] ?? 'MorgiHome User').toString();
  }

  static Future<String?> profileImage() async {
    final u = await currentUser();
    final v = u?['profile_image'];
    if (v is String && v.isNotEmpty) return v;
    return null;
  }

  static void clearCache() => _cachedUser = null;
}
