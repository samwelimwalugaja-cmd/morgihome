import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';
import '../models/contract.dart';
import '../models/property.dart';
import '../models/mortgage.dart';
import '../models/user.dart';

class ApiService {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _userKey = 'user_data';
  static const _timeout = Duration(seconds: 15);

  String get baseUrl => AppConstants.baseUrl;

  // Token handling - web-safe: FlutterSecureStorage may fail on web,
  // so fallback is SharedPreferences.
  Future<void> saveTokens({required String access, required String refresh, Map<String, dynamic>? user}) async {
    try {
      await _storage.write(key: _accessKey, value: access);
      await _storage.write(key: _refreshKey, value: refresh);
    } catch (_) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_accessKey, access);
      await prefs.setString(_refreshKey, refresh);
    }
    if (user != null) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey, jsonEncode(user));
    }
  }

  Future<String?> getAccessToken() async {
    try {
      final v = await _storage.read(key: _accessKey);
      if (v != null && v.isNotEmpty) return v;
    } catch (_) {}
    // Fallback (web or if secure storage failed)
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_accessKey);
    } catch (_) {
      return null;
    }
  }

  Future<String?> getRefreshToken() async {
    try {
      final v = await _storage.read(key: _refreshKey);
      if (v != null && v.isNotEmpty) return v;
    } catch (_) {}
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString(_refreshKey);
    } catch (_) {
      return null;
    }
  }

  /// Friendly message when user fails to connect to server.
  /// This is the fix for "ClientException: Failed to fetch".
  /// It throws an Exception with English instructions.
  Never _throwConnectionError(Object e) {
    if (e is TimeoutException) {
      throw Exception('Server unreachable (timeout). Make sure backend is running: python manage.py runserver');
    }
    throw Exception(
        'Failed to connect to server ($baseUrl).\n'
        '1. Make sure Django backend is running:\n'
        '   python manage.py runserver\n'
        '2. If using Chrome (web), baseUrl is http://127.0.0.1:8000/api\n'
        '3. If using emulator, use http://10.0.2.2:8000/api');
  }

  bool _isNetworkError(Object e) {
    if (e is TimeoutException || e is SocketException || e is http.ClientException) return true;
    final msg = e.toString();
    return msg.contains('Failed to fetch') ||
        msg.contains('Connection refused') ||
        msg.contains('Connection reset') ||
        msg.contains('Network is unreachable') ||
        msg.contains('SocketException') ||
        msg.contains('ClientException') ||
        msg.contains('XMLHttpRequest');
  }

  Future<Map<String, String>> _headers({bool auth = false}) async {
    final headers = {'Content-Type': 'application/json'};
    if (auth) {
      final token = await getAccessToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<User?> getStoredUser() async {
    final prefs = await SharedPreferences.getInstance();
    final str = prefs.getString(_userKey);
    if (str == null) return null;
    try {
      return User.fromJson(jsonDecode(str));
    } catch (_) {
      return null;
    }
  }

  // Auth
  Future<Map<String, dynamic>> login({required String email, required String password}) async {
    final url = Uri.parse('$baseUrl${AppConstants.loginEndpoint}');
    try {
      final res = await http
          .post(url,
              headers: await _headers(),
              body: jsonEncode({'email': email, 'password': password}))
          .timeout(_timeout);
      if (res.body.isEmpty) {
        throw Exception('Server returned an empty response (${res.statusCode}). Make sure backend is running.');
      }
      dynamic decoded;
      try {
        decoded = jsonDecode(res.body);
      } catch (_) {
        throw Exception('Server returned an invalid response (${res.statusCode}). URL: $url');
      }
      final data = decoded as Map<String, dynamic>;
      if (res.statusCode == 200) {
        if (data['access'] == null) {
          throw Exception('Login failed: server did not send a token.');
        }
        await saveTokens(
            access: data['access'].toString(),
            refresh: (data['refresh'] ?? '').toString(),
            user: data['user'] is Map ? Map<String, dynamic>.from(data['user']) : null);
        return data;
      } else {
        throw Exception(data['error'] ?? data['detail'] ?? 'Login failed (${res.statusCode})');
      }
    } catch (e) {
      // If already a friendly message (already thrown above), rethrow as is
      final msg = e.toString();
      if (msg.contains('Failed to connect') || msg.contains('Server returned') || msg.contains('Server unreachable')) rethrow;
      if (_isNetworkError(e)) _throwConnectionError(e);
      // If already an Exception with friendly message, send as is
      if (e is FormatException || e is TypeError) {
        throw Exception('Server returned an unreadable response. Make sure backend is running: python manage.py runserver');
      }
      rethrow;
    }
  }

  Future<Map<String, dynamic>> register({
    required String firstName,
    required String lastName,
    required String email,
    required String phone,
    required String password,
    required String confirmPassword,
    String role = 'customer',
  }) async {
    // Backend only allows customer/seller to register (see RegisterSerializer)
    final safeRole = (role == 'seller') ? 'seller' : 'customer';
    final url = Uri.parse('$baseUrl${AppConstants.registerEndpoint}');
    try {
      final res = await http
          .post(url,
              headers: await _headers(),
              body: jsonEncode({
                'first_name': firstName,
                'last_name': lastName,
                'email': email,
                'phone_number': phone,
                'password': password,
                'confirm_password': confirmPassword,
                'role': safeRole,
              }))
          .timeout(_timeout);
      if (res.body.isEmpty) {
        throw Exception('Server returned an empty response (${res.statusCode}). Make sure backend is running.');
      }
      final data = jsonDecode(res.body) as Map<String, dynamic>;
      if (res.statusCode == 201 || res.statusCode == 200) {
        return data;
      } else {
        // collect errors
        final msg = data.values.map((e) => e is List ? e.join(', ') : e.toString()).join('\n');
        throw Exception(msg.isNotEmpty ? msg : 'Registration failed');
      }
    } on TimeoutException catch (e) {
      _throwConnectionError(e);
    } on SocketException catch (e) {
      _throwConnectionError(e);
    } on http.ClientException catch (e) {
      _throwConnectionError(e);
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('Failed to fetch') || msg.contains('XMLHttpRequest')) {
        _throwConnectionError(e);
      }
      rethrow;
    }
  }

  Future<void> logout() async {
    try {
      final refresh = await getRefreshToken();
      final url = Uri.parse('$baseUrl${AppConstants.logoutEndpoint}');
      await http.post(url,
          headers: await _headers(auth: true),
          body: jsonEncode({'refresh': refresh}));
    } catch (_) {}
    try {
      await _storage.delete(key: _accessKey);
      await _storage.delete(key: _refreshKey);
    } catch (_) {}
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_accessKey);
    await prefs.remove(_refreshKey);
    await prefs.remove(_userKey);
  }

  // Properties
  Future<List<Property>> getProperties({String? search, String? type}) async {
    var url = '$baseUrl${AppConstants.propertiesEndpoint}';
    final query = <String, String>{};
    if (search != null && search.isNotEmpty) query['search'] = search;
    if (type != null && type.isNotEmpty) query['property_type'] = type;
    if (query.isNotEmpty) url += '?${Uri(queryParameters: query).query}';
    final res = await http.get(Uri.parse(url), headers: await _headers()).timeout(_timeout);
    if (res.statusCode == 200) {
      final decoded = jsonDecode(res.body);
      List list;
      if (decoded is Map && decoded.containsKey('results')) {
        list = decoded['results'];
      } else if (decoded is List) {
        list = decoded;
      } else {
        list = [];
      }
      return list.map((e) => Property.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load properties');
    }
  }

  Future<Property> getPropertyDetail(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.propertiesEndpoint}$id/');
    final res = await http.get(url, headers: await _headers()).timeout(_timeout);
    if (res.statusCode == 200) {
      return Property.fromJson(jsonDecode(res.body));
    } else {
      throw Exception('Property not found');
    }
  }

  // Mortgage
  Future<Map<String, dynamic>> applyMortgage(Map<String, dynamic> data) async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}');
    final res = await http.post(url,
        headers: await _headers(auth: true), body: jsonEncode(data)).timeout(_timeout);
    final body = jsonDecode(res.body);
    if (res.statusCode == 201 || res.statusCode == 200) {
      return body;
    } else {
      final msg = body is Map
          ? body.values.map((e) => e is List ? e.join(', ') : e.toString()).join('\n')
          : body.toString();
      throw Exception(msg.isNotEmpty ? msg : 'Failed to apply');
    }
  }

  Future<List<MortgageApplication>> getMyApplications() async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}');
    final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
    if (res.statusCode == 200) {
      final decoded = jsonDecode(res.body);
      List list;
      if (decoded is Map && decoded.containsKey('results')) {
        list = decoded['results'];
      } else if (decoded is List) {
        list = decoded;
      } else {
        list = [];
      }
      return list.map((e) => MortgageApplication.fromJson(e)).toList();
    } else {
      throw Exception('Failed to load applications');
    }
  }

  Future<User> getProfile() async {
    final url = Uri.parse('$baseUrl${AppConstants.profileApiEndpoint}');
    var res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
    if (res.statusCode == 200) {
      return User.fromJson(jsonDecode(res.body));
    }
    // fallback to /auth/profile/
    final url2 = Uri.parse('$baseUrl${AppConstants.profileEndpoint}');
    res = await http.get(url2, headers: await _headers(auth: true)).timeout(_timeout);
    if (res.statusCode == 200) {
      return User.fromJson(jsonDecode(res.body));
    }
    throw Exception('Failed to load profile');
  }

  /// Edit profile (name, phone) - like web profile page.
  Future<User> updateProfile({String? firstName, String? lastName, String? phone}) async {
    final url = Uri.parse('$baseUrl${AppConstants.profileApiEndpoint}');
    final body = <String, dynamic>{};
    if (firstName != null) body['first_name'] = firstName;
    if (lastName != null) body['last_name'] = lastName;
    if (phone != null) body['phone_number'] = phone;
    try {
      final res = await http
          .patch(url, headers: await _headers(auth: true), body: jsonEncode(body))
          .timeout(_timeout);
      if (res.statusCode == 200) {
        final u = User.fromJson(jsonDecode(res.body));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userKey, jsonEncode(u.toJson()));
        return u;
      }
      throw Exception(_msg(res.body, 'Failed to update profile (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Upload profile photo - like web "Upload Photo".
  Future<User> uploadProfilePhoto(XFile file) async {
    final url = Uri.parse('$baseUrl${AppConstants.profileApiEndpoint}');
    try {
      final req = http.MultipartRequest('PATCH', url);
      final h = await _headers(auth: true);
      req.headers.addAll(h);
      req.files.add(await http.MultipartFile.fromPath('profile_image', file.path));
      final streamed = await req.send().timeout(_timeout);
      final res = await http.Response.fromStream(streamed);
      if (res.statusCode == 200) {
        final u = User.fromJson(jsonDecode(res.body));
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_userKey, jsonEncode(u.toJson()));
        return u;
      }
      throw Exception(_msg(res.body, 'Failed to upload photo (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Change password - like web Change Password.
  Future<void> changePassword({required String oldPassword, required String newPassword}) async {
    final url = Uri.parse('$baseUrl${AppConstants.changePasswordEndpoint}');
    try {
      final res = await http
          .post(url,
              headers: await _headers(auth: true),
              body: jsonEncode({
                'old_password': oldPassword,
                'new_password': newPassword,
                'confirm_password': newPassword,
              }))
          .timeout(_timeout);
      if (res.statusCode == 200) return;
      throw Exception(_msg(res.body, 'Failed to change password (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Live timeline: every bank confirmation step - like web track page.
  Future<Map<String, dynamic>> getApplicationTimeline(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}$id/timeline/');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data is Map<String, dynamic>) return data;
      }
      throw Exception('Failed to load timeline (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Details of one application (track) - like web track page.
  Future<MortgageApplication> getApplicationDetail(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}$id/');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        if (data is Map<String, dynamic>) return MortgageApplication.fromJson(data);
        throw Exception('Invalid response from server.');
      }
      throw Exception('Application not found (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// AI affordability preview - like web calculate.
  Future<Map<String, dynamic>> calculateAffordability(Map<String, dynamic> data) async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}calculate/');
    try {
      final res = await http
          .post(url, headers: await _headers(auth: true), body: jsonEncode(data))
          .timeout(_timeout);
      final body = jsonDecode(res.body);
      if (res.statusCode == 200 && body is Map<String, dynamic>) return body;
      throw Exception(_msg(res.body, 'Calculation failed'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Repayment schedule - like web repayment page.
  Future<List<RepaymentEntry>> getRepaymentSchedule(int applicationId) async {
    final url = Uri.parse('$baseUrl${AppConstants.mortgagesEndpoint}$applicationId/repayment_schedule/');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => RepaymentEntry.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Failed to load repayment schedule (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// My contracts - like web contracts page (customer + seller).
  Future<List<Contract>> getMyContracts() async {
    final url = Uri.parse('$baseUrl${AppConstants.contractsEndpoint}');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => Contract.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Failed to load contracts (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  Future<Contract> getContractDetail(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.contractsEndpoint}$id/');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) return Contract.fromJson(jsonDecode(res.body));
      throw Exception('Contract not found (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Sign contract (customer/seller) - like web sign button.
  Future<Map<String, dynamic>> signContract(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.contractsEndpoint}$id/sign/');
    try {
      final res = await http.post(url, headers: await _headers(auth: true)).timeout(_timeout);
      final body = res.body.isNotEmpty ? jsonDecode(res.body) : <String, dynamic>{};
      if (res.statusCode == 200 && body is Map<String, dynamic>) return body;
      throw Exception(_msg(res.body, 'Failed to sign (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Transactions - like web transactions.
  Future<List<AppTransaction>> getMyTransactions() async {
    final url = Uri.parse('$baseUrl${AppConstants.transactionsEndpoint}');
    try {
      final res = await http.get(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => AppTransaction.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Failed to load transactions (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Partner banks - like web bank requirements / apply step 6.
  Future<List<Bank>> getBanks() async {
    final url = Uri.parse('$baseUrl${AppConstants.banksEndpoint}');
    try {
      final res = await http.get(url, headers: await _headers()).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => Bank.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Failed to load banks (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Search properties by price and type - like web search.
  Future<List<Property>> searchProperties({String? q, String? minPrice, String? maxPrice, String? type}) async {
    var url = '$baseUrl${AppConstants.propertySearchEndpoint}';
    final query = <String, String>{};
    if (q != null && q.isNotEmpty) query['q'] = q;
    if (minPrice != null && minPrice.isNotEmpty) query['min_price'] = minPrice;
    if (maxPrice != null && maxPrice.isNotEmpty) query['max_price'] = maxPrice;
    if (type != null && type.isNotEmpty) query['property_type'] = type;
    if (query.isNotEmpty) url += '?${Uri(queryParameters: query).query}';
    try {
      final res = await http.get(Uri.parse(url), headers: await _headers()).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => Property.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Search failed (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Properties of logged-in seller - like web seller properties.
  Future<List<Property>> getMyProperties() async {
    var url = '$baseUrl${AppConstants.propertiesEndpoint}?mine=1';
    try {
      final res = await http.get(Uri.parse(url), headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 200) {
        final decoded = jsonDecode(res.body);
        final list = decoded is List ? decoded : (decoded is Map && decoded['results'] is List ? decoded['results'] : []);
        return (list as List).map((e) => Property.fromJson(Map<String, dynamic>.from(e))).toList();
      }
      throw Exception('Failed to load your properties (${res.statusCode})');
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Seller adds property (with photos) - like web add property.
  Future<Property> createProperty(Map<String, String> fields, {List<XFile>? images, int coverIndex = 0}) async {
    final url = Uri.parse('$baseUrl${AppConstants.propertiesEndpoint}');
    try {
      final req = http.MultipartRequest('POST', url);
      req.headers.addAll(await _headers(auth: true));
      fields.forEach((k, v) => req.fields[k] = v);
      if (images != null) {
        for (final img in images.take(5)) {
          req.files.add(await http.MultipartFile.fromPath('images', img.path));
        }
        req.fields['cover_index'] = coverIndex.toString();
      }
      final streamed = await req.send().timeout(_timeout);
      final res = await http.Response.fromStream(streamed);
      if (res.statusCode == 201 || res.statusCode == 200) {
        return Property.fromJson(jsonDecode(res.body));
      }
      throw Exception(_msg(res.body, 'Failed to add property (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Seller edits property - like web edit property.
  Future<Property> updateProperty(int id, Map<String, String> fields, {List<XFile>? images}) async {
    final url = Uri.parse('$baseUrl${AppConstants.propertiesEndpoint}$id/');
    try {
      if (images == null || images.isEmpty) {
        final res = await http
            .patch(url, headers: await _headers(auth: true), body: jsonEncode(fields))
            .timeout(_timeout);
        if (res.statusCode == 200) return Property.fromJson(jsonDecode(res.body));
        throw Exception(_msg(res.body, 'Failed to update (${res.statusCode})'));
      }
      final req = http.MultipartRequest('PATCH', url);
      req.headers.addAll(await _headers(auth: true));
      fields.forEach((k, v) => req.fields[k] = v);
      for (final img in images.take(5)) {
        req.files.add(await http.MultipartFile.fromPath('images', img.path));
      }
      final streamed = await req.send().timeout(_timeout);
      final res = await http.Response.fromStream(streamed);
      if (res.statusCode == 200) return Property.fromJson(jsonDecode(res.body));
      throw Exception(_msg(res.body, 'Failed to update (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  Future<void> deleteProperty(int id) async {
    final url = Uri.parse('$baseUrl${AppConstants.propertiesEndpoint}$id/');
    try {
      final res = await http.delete(url, headers: await _headers(auth: true)).timeout(_timeout);
      if (res.statusCode == 204 || res.statusCode == 200) return;
      throw Exception(_msg(res.body, 'Failed to delete (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Add photos to gallery - like web gallery upload.
  Future<void> uploadGallery(int id, List<XFile> images) async {
    final url = Uri.parse('$baseUrl${AppConstants.propertiesEndpoint}$id/gallery/');
    try {
      final req = http.MultipartRequest('POST', url);
      req.headers.addAll(await _headers(auth: true));
      for (final img in images.take(5)) {
        req.files.add(await http.MultipartFile.fromPath('images', img.path));
      }
      final streamed = await req.send().timeout(_timeout);
      final res = await http.Response.fromStream(streamed);
      if (res.statusCode == 201 || res.statusCode == 200) return;
      throw Exception(_msg(res.body, 'Failed to upload photos (${res.statusCode})'));
    } catch (e) {
      if (_isNetworkError(e)) _throwConnectionError(e);
      rethrow;
    }
  }

  /// Extract error message from server JSON.
  String _msg(String body, String fallback) {
    try {
      final d = jsonDecode(body);
      if (d is Map) {
        final m = d.values.map((e) => e is List ? e.join(', ') : e.toString()).join('\n');
        if (m.isNotEmpty && m != '{}') return m;
      }
      return d.toString();
    } catch (_) {
      return body.isNotEmpty ? body : fallback;
    }
  }

  // Helper to build image url
  String buildImageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    // Django media url
    final base = baseUrl.replaceAll('/api', '');
    if (path.startsWith('/')) return '$base$path';
    return '$base/$path';
  }
}
