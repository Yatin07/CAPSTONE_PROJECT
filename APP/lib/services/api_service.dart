import 'dart:convert';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb;
import 'package:http/http.dart' as http;
import '../models/inventory_item.dart';
import '../models/waste_alert.dart';

class ApiService {
  ApiService._internal();
  static final ApiService instance = ApiService._internal();

  /// Default API base URL:
  /// - Android Emulator: 10.0.2.2 routes to the host machine localhost
  /// - Web / Desktop: 127.0.0.1
  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000/api/v1';
      }
    } catch (_) {}
    return 'http://127.0.0.1:8000/api/v1';
  }

  String _baseUrl = defaultBaseUrl;
  // ignore: unnecessary_getters_setters
  String get baseUrl => _baseUrl;
  // ignore: unnecessary_getters_setters
  set baseUrl(String url) => _baseUrl = url;


  String? _token;
  String? _userId;
  String? _userName;
  String? _userRole;

  String? get token => _token;
  String? get userId => _userId;
  String? get userName => _userName;
  String? get userRole => _userRole;
  bool get isAuthenticated => _token != null && _token!.isNotEmpty;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  // --------------------------------------------------------------------------
  // Authentication
  // --------------------------------------------------------------------------

  Future<bool> login(String email, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/auth/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'email': email.trim().toLowerCase(),
              'password': password,
            }),
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _userId = data['user_id'];
        _userName = data['name'];
        _userRole = data['role'] ?? 'owner';
        if (kDebugMode) print('[API] Logged in successfully as $_userName');
        return true;
      } else {
        if (kDebugMode) print('[API] Login failed: ${response.statusCode} ${response.body}');
        return false;
      }
    } catch (e) {
      if (kDebugMode) print('[API] Login network error: $e');
      return false;
    }
  }

  Future<bool> register(String name, String email, String password, {String role = 'owner'}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/auth/register'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'name': name.trim(),
              'email': email.trim().toLowerCase(),
              'password': password,
              'role': role,
            }),
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        _token = data['access_token'];
        _userId = data['user_id'];
        _userName = data['name'];
        _userRole = data['role'] ?? role;
        return true;
      }
      return false;
    } catch (e) {
      if (kDebugMode) print('[API] Register error: $e');
      return false;
    }
  }

  void logout() {
    _token = null;
    _userId = null;
    _userName = null;
    _userRole = null;
  }

  // --------------------------------------------------------------------------
  // Dashboard & Forecast Read Layer
  // --------------------------------------------------------------------------

  Future<Map<String, dynamic>?> fetchTodayDashboard() async {
    try {
      final response = await http
          .get(
            Uri.parse('$_baseUrl/forecasts/today'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final rawItems = data['items'] as List? ?? [];
        final items = rawItems
            .map((item) => InventoryItem.fromJson(item as Map<String, dynamic>))
            .toList();

        return {
          'summary': data['summary']?.toString() ?? '',
          'total_items': data['total_items'] ?? items.length,
          'action_required_count': data['action_required_count'] ?? 0,
          'items': items,
        };
      }
    } catch (e) {
      if (kDebugMode) print('[API] fetchTodayDashboard error: $e');
    }
    return null;
  }

  Future<List<InventoryItem>?> fetchItems() async {
    try {
      final response = await http
          .get(
            Uri.parse('$_baseUrl/items'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final rawItems = data['items'] as List? ?? [];
        return rawItems
            .map((item) => InventoryItem.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      if (kDebugMode) print('[API] fetchItems error: $e');
    }
    return null;
  }

  Future<InventoryItem?> createItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  }) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/items'),
            headers: _headers,
            body: jsonEncode({
              'name': name.trim(),
              'category': category.trim(),
              'unit': unit.trim(),
              'currentStock': currentStock,
              'isPerishable': isPerishable,
              'price': price,
            }),
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final itemId = data['item_id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString();
        return InventoryItem(
          id: itemId,
          name: name,
          category: category,
          unit: unit,
          currentStock: currentStock,
          isPerishable: isPerishable,
          price: price,
          predictedDemand: currentStock + 15,
          safetyStock: 5,
          description: 'Cold-start analysis active — learning sales pace',
          updatedAt: DateTime.now(),
        );
      }
    } catch (e) {
      if (kDebugMode) print('[API] createItem error: $e');
    }
    return null;
  }

  Future<bool> restockItem(String itemId, {int? quantity}) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/items/$itemId/restock'),
            headers: _headers,
            body: jsonEncode({if (quantity != null) 'quantity': quantity}),
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] restockItem error: $e');
      return false;
    }
  }

  Future<bool> updateItem(
    String itemId, {
    String? name,
    String? category,
    String? unit,
    int? currentStock,
    bool? isPerishable,
    double? price,
  }) async {
    try {
      final payload = <String, dynamic>{
        if (name != null) 'name': name,
        if (category != null) 'category': category,
        if (unit != null) 'unit': unit,
        if (currentStock != null) 'currentStock': currentStock,
        if (isPerishable != null) 'isPerishable': isPerishable,
        if (price != null) 'price': price,
      };

      final response = await http
          .put(
            Uri.parse('$_baseUrl/items/$itemId'),
            headers: _headers,
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] updateItem error: $e');
      return false;
    }
  }

  Future<bool> deleteItem(String itemId) async {
    try {
      final response = await http
          .delete(
            Uri.parse('$_baseUrl/items/$itemId'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] deleteItem error: $e');
      return false;
    }
  }

  // --------------------------------------------------------------------------
  // Waste Action Engine
  // --------------------------------------------------------------------------

  Future<List<WasteAlert>?> fetchWasteAlerts() async {
    try {
      final response = await http
          .get(
            Uri.parse('$_baseUrl/waste-alerts'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final rawAlerts = data['alerts'] as List? ?? [];
        return rawAlerts
            .map((alert) => WasteAlert.fromJson(alert as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      if (kDebugMode) print('[API] fetchWasteAlerts error: $e');
    }
    return null;
  }

  Future<bool> recordIntradaySale(String itemId, int quantity) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/sales/intraday'),
            headers: _headers,
            body: jsonEncode({'item_id': itemId, 'quantity': quantity}),
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 201;
    } catch (e) {
      if (kDebugMode) print('[API] recordIntradaySale error: $e');
      return false;
    }
  }

  Future<bool> applyDiscount(String itemId) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/apply-discount'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] applyDiscount error: $e');
      return false;
    }
  }

  Future<bool> flagDonation(String itemId) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/flag-donation'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] flagDonation error: $e');
      return false;
    }
  }

  Future<bool> dismissAlert(String itemId) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/dismiss'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 6));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] dismissAlert error: $e');
      return false;
    }
  }
}
