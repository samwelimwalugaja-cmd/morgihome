import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/user.dart';
import '../models/property.dart';
import '../models/mortgage.dart';

class ApiService {
  // 10.0.2.2 kwa Android Emulator, localhost kwa iOS/Web/Desktop
  // Badilisha IP ya kifaa halisi kupitia: --dart-define=API_BASE_URL=http://192.168.x.x:8000/api/
  static String get baseUrl {
    const envUrl = String.fromEnvironment('API_BASE_URL');
    if (envUrl.isNotEmpty) return envUrl.endsWith('/') ? envUrl : '$envUrl/';
    if (kIsWeb) return 'http://localhost:8000/api/';
    try {
      if (Platform.isAndroid) return 'http://10.0.2.2:8000/api/';
    } catch (_) {}
    return 'http://localhost:8000/api/';
  }

  static Duration get timeout => const Duration(seconds: 15);

  Future<Map<String, String>> _getHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('access_token');
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // ----- AUTH -----
  Future<Map<String, dynamic>> login(String username, String password) async {
    // username is email (web parity) - backend accepts email or username
    final email = username.trim();
    try {
      final response = await http
          .post(
            Uri.parse('${baseUrl}auth/login/'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'username': email, 'password': password}),
          )
          .timeout(timeout);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', data['access']);
        await prefs.setString('refresh_token', data['refresh']);
        if (data['user'] != null) {
          await prefs.setString('user_json', jsonEncode(data['user']));
        }
        return data;
      } else {
        String msg = 'Login failed';
        try {
          final err = jsonDecode(response.body);
          if (err is Map && err.containsKey('error')) msg = err['error'].toString();
          else if (err is Map && err.containsKey('detail')) msg = err['detail'].toString();
        } catch (_) {}
        throw Exception(msg);
      }
    } on SocketException {
      throw Exception('Failed to connect to server. Ensure backend is running at ${baseUrl} and cleartext (http) is allowed.');
    } catch (e) {
      if (e.toString().contains('ClientException') || e.toString().contains('Failed host lookup') || e.toString().contains('Connection refused')) {
        throw Exception('Failed to fetch ${baseUrl}auth/login/ - Server not reachable. Android emulator use 10.0.2.2, real device use computer IP.');
      }
      rethrow;
    }
  }

  Future<User> register(String username, String email, String password, String role, {String? phoneNumber}) async {
    final body = <String, dynamic>{
      'username': username,
      'email': email,
      'password': password,
      'role': role,
    };
    if (phoneNumber != null && phoneNumber.isNotEmpty) {
      body['phone_number'] = phoneNumber;
    }
    try {
      final response = await http
          .post(
            Uri.parse('${baseUrl}auth/signup/'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(timeout);

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return User.fromJson(data);
      } else {
        String msg = 'Registration failed';
        try {
          final err = jsonDecode(response.body);
          if (err is Map) {
            if (err.containsKey('username')) msg = (err['username'] as List).first.toString();
            else if (err.containsKey('email')) msg = (err['email'] as List).first.toString();
            else if (err.containsKey('password')) msg = (err['password'] as List).first.toString();
            else if (err.containsKey('role')) msg = (err['role'] as List).first.toString();
            else if (err.containsKey('phone_number')) msg = (err['phone_number'] as List).first.toString();
            else if (err.containsKey('detail')) msg = err['detail'].toString();
            else if (err.containsKey('non_field_errors')) msg = (err['non_field_errors'] as List).first.toString();
            else msg = err.values.first.toString();
          }
        } catch (_) {
          msg = response.body.isNotEmpty ? response.body : 'Registration failed (${response.statusCode})';
        }
        throw Exception(msg);
      }
    } on SocketException {
      throw Exception('Failed to connect to server ${baseUrl}auth/signup/. Ensure backend is running and firewall allows port 8000.');
    } catch (e) {
      final s = e.toString();
      if (s.contains('SocketException') || s.contains('ClientException') || s.contains('Failed host lookup') || s.contains('Connection refused') || s.contains('Failed to fetch')) {
        throw Exception('Failed to fetch, uri=${baseUrl}auth/signup/ - Server not reachable. Use correct IP: emulator 10.0.2.2, device 192.168.x.x');
      }
      rethrow;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user_json');
  }

  // ----- PROPERTIES -----
  Future<List<Property>> getProperties() async {
    try {
      // Jaribu na bila token pia (AllowAny kwenye backend)
      final response = await http.get(Uri.parse('${baseUrl}properties/')).timeout(timeout);

      if (response.statusCode == 200) {
        final dynamic decoded = jsonDecode(response.body);
        List<dynamic> data;
        if (decoded is List) {
          data = decoded;
        } else if (decoded is Map && decoded.containsKey('results')) {
          data = decoded['results'] as List<dynamic>;
        } else {
          throw Exception('Unexpected response format');
        }
        return data.map((json) => Property.fromJson(json as Map<String, dynamic>)).toList();
      } else {
        throw Exception('Failed to load properties (${response.statusCode})');
      }
    } on SocketException {
      throw Exception('Failed to load properties - server not reachable ${baseUrl}properties/');
    } catch (e) {
      if (e.toString().contains('Failed to load properties')) rethrow;
      throw Exception('Failed to load properties: $e');
    }
  }

  Future<Property> getProperty(int id) async {
    final response = await http.get(Uri.parse('${baseUrl}properties/$id/')).timeout(timeout);
    if (response.statusCode == 200) {
      return Property.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load property');
    }
  }

  // ----- BANKS -----
  Future<List<Map<String, dynamic>>> getBanks() async {
    final response = await http.get(Uri.parse('${baseUrl}banks/')).timeout(timeout);
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      final List list = decoded is List ? decoded : (decoded['results'] ?? []);
      return list.cast<Map<String, dynamic>>();
    }
    return [];
  }

  // ----- MORTGAGES -----
  Future<Map<String, dynamic>> applyMortgage(Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    final response = await http.post(Uri.parse('${baseUrl}mortgages/'), headers: headers, body: jsonEncode(data)).timeout(timeout);
    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      String msg = response.body;
      try { final j=jsonDecode(response.body); msg = j['property']?.toString() ?? j['detail']?.toString() ?? msg; } catch(_){}
      throw Exception(msg);
    }
  }

  Future<List<dynamic>> getDrafts({String? mortgageType}) async {
    final headers = await _getHeaders();
    var url = '${baseUrl}mortgages/draft/';
    if (mortgageType != null && mortgageType.isNotEmpty) url += '?mortgage_type=$mortgageType';
    final response = await http.get(Uri.parse(url), headers: headers).timeout(timeout);
    if (response.statusCode == 200) return jsonDecode(response.body) as List;
    return [];
  }

  Future<Map<String, dynamic>> saveDraft(Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    final response = await http.post(Uri.parse('${baseUrl}mortgages/draft/'), headers: headers, body: jsonEncode(data)).timeout(timeout);
    if (response.statusCode == 200 || response.statusCode == 201) return jsonDecode(response.body);
    throw Exception('Failed to save draft');
  }

  Future<Map<String, dynamic>> calculateAffordability(Map<String, dynamic> data) async {
    final headers = await _getHeaders();
    final response = await http.post(Uri.parse('${baseUrl}mortgages/calculate/'), headers: headers, body: jsonEncode(data)).timeout(timeout);
    if (response.statusCode == 200) return jsonDecode(response.body);
    throw Exception('Failed to calculate');
  }

  Future<List<MortgageApplication>> getMyMortgages() async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('${baseUrl}mortgages/'), headers: headers).timeout(timeout);
    if (response.statusCode == 200) {
      final dynamic decoded = jsonDecode(response.body);
      final List<dynamic> data = decoded is List ? decoded : (decoded['results'] as List);
      return data.map((json) => MortgageApplication.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load mortgages');
    }
  }

  Future<Map<String, dynamic>> getAffordability(int mortgageId) async {
    final headers = await _getHeaders();
    final response = await http.get(Uri.parse('${baseUrl}mortgages/$mortgageId/affordability/'), headers: headers).timeout(timeout);
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get affordability');
    }
  }

  // ----- PROFILE (web parity: /api/profile/) -----
  Future<Map<String, dynamic>> getProfile() async {
    final headers = await _getHeaders();
    final res = await http.get(Uri.parse('${baseUrl}profile/'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to load profile');
  }

  // ----- NOTIFICATIONS (role parity with web bells) -----
  Future<Map<String, dynamic>> getNotifications() async {
    final headers = await _getHeaders();
    // try customer -> realestate -> seller (backend returns [] for wrong role)
    for (final path in ['auth/notifications/', 'auth/notifications/realestate/', 'auth/notifications/seller/']) {
      try {
        final res = await http.get(Uri.parse('$baseUrl$path'), headers: headers).timeout(timeout);
        if (res.statusCode == 200) {
          final data = jsonDecode(res.body) as Map<String, dynamic>;
          final items = (data['notifications'] as List?) ?? [];
          if (items.isNotEmpty || path == 'auth/notifications/seller/') return data;
          // keep first non-empty; customer empty -> try next
          if (path == 'auth/notifications/') continue;
          return data;
        }
      } catch (_) {}
    }
    return {'notifications': [], 'unread': 0};
  }

  Future<void> markNotificationsRead() async {
    final headers = await _getHeaders();
    for (final path in ['auth/notifications/', 'auth/notifications/seller/']) {
      try {
        await http.post(Uri.parse('$baseUrl$path'), headers: headers).timeout(timeout);
      } catch (_) {}
    }
  }

  // ----- CONTRACTS (web parity: seller/realestate/bank/customer) -----
  Future<List<dynamic>> getContracts() async {
    final headers = await _getHeaders();
    final res = await http.get(Uri.parse('${baseUrl}contracts/'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) {
      final d = jsonDecode(res.body);
      if (d is List) return d;
      if (d is Map && d['results'] is List) return d['results'] as List;
      return [];
    }
    return [];
  }

  // ----- MORTGAGE DETAIL + TIMELINE (web parity: track/review) -----
  Future<Map<String, dynamic>> getMortgageDetail(int id) async {
    final headers = await _getHeaders();
    final res = await http.get(Uri.parse('${baseUrl}mortgages/$id/'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to load application');
  }

  Future<Map<String, dynamic>> getTimeline(int id) async {
    final headers = await _getHeaders();
    final res = await http.get(Uri.parse('${baseUrl}mortgages/$id/timeline/'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    return {'events': [], 'corrections': []};
  }

  // ----- BANK REVIEW ACTIONS (web parity: stage/approve/reject/correction) -----
  Future<Map<String, dynamic>> advanceStage(int id, String stage, {String note = ''}) async {
    final headers = await _getHeaders();
    final res = await http.post(Uri.parse('${baseUrl}mortgages/$id/advance_stage/'), headers: headers, body: jsonEncode({'stage': stage, 'note': note})).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to update stage: ${res.body}');
  }

  Future<Map<String, dynamic>> approveMortgage(int id) async {
    final headers = await _getHeaders();
    final res = await http.post(Uri.parse('${baseUrl}mortgages/$id/approve/'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to approve: ${res.body}');
  }

  Future<Map<String, dynamic>> rejectMortgage(int id, String reason) async {
    final headers = await _getHeaders();
    final res = await http.post(Uri.parse('${baseUrl}mortgages/$id/reject/'), headers: headers, body: jsonEncode({'reason': reason})).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to reject: ${res.body}');
  }

  Future<Map<String, dynamic>> requestCorrection(int id, {required String kind, required String target, required String instructions}) async {
    final headers = await _getHeaders();
    final res = await http.post(Uri.parse('${baseUrl}mortgages/$id/request_correction/'), headers: headers, body: jsonEncode({'kind': kind, 'target': target, 'instructions': instructions})).timeout(timeout);
    if (res.statusCode == 200 || res.statusCode == 201) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to send correction: ${res.body}');
  }

  Future<Map<String, dynamic>> respondCorrection(int mortgageId, int correctionId, {String text = ''}) async {
    final headers = await _getHeaders();
    final res = await http.post(Uri.parse('${baseUrl}mortgages/$mortgageId/respond_correction/'), headers: headers, body: jsonEncode({'correction_id': correctionId, 'response_text': text})).timeout(timeout);
    if (res.statusCode == 200) return jsonDecode(res.body) as Map<String, dynamic>;
    throw Exception('Failed to respond: ${res.body}');
  }

  // ----- PROPERTIES MINE (seller/realestate parity) -----
  Future<List<Property>> getMyProperties() async {
    final headers = await _getHeaders();
    final res = await http.get(Uri.parse('${baseUrl}properties/?mine=1'), headers: headers).timeout(timeout);
    if (res.statusCode == 200) {
      final d = jsonDecode(res.body);
      final List list = d is List ? d : (d['results'] ?? []);
      return list.map((j) => Property.fromJson(j as Map<String, dynamic>)).toList();
    }
    return [];
  }
}
