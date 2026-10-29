import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart' show kDebugMode, kIsWeb, ValueNotifier;
import 'package:http/http.dart' as http;
import '../models/inventory_item.dart';
import '../models/waste_alert.dart';

class ApiService {
  http.Client client;

  ApiService({http.Client? client}) : client = client ?? http.Client();
  static final ApiService instance = ApiService();

  static void setMockClient(http.Client mockClient) {
    instance.client = mockClient;
  }

  static void resetClient() {
    instance.client = http.Client();
  }

  /// Reactive status for UI to display cold start wake-up progress
  static final ValueNotifier<bool> isWakingUpServer = ValueNotifier<bool>(false);
  static final ValueNotifier<String?> serverStatusMessage = ValueNotifier<String?>(null);

  bool _isFirstRequest = true;

  /// Default API base URL:
  static String get defaultBaseUrl {
    const definedUrl = String.fromEnvironment('API_BASE_URL');
    if (definedUrl.isNotEmpty) {
      return definedUrl;
    }

    if (kIsWeb) return 'http://127.0.0.1:8000/api/v1';

    // Default to the live cloud backend on Render for physical devices and production
    return 'https://restockiq-backend.onrender.com/api/v1';
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

  /// Core HTTP execution with exponential backoff retry and cold-start wake detection
  Future<http.Response> _executeWithRetry({
    required Future<http.Response> Function(Duration currentTimeout) requestFn,
    int maxTries = 3,
    Duration firstRequestTimeout = const Duration(seconds: 40),
    Duration normalTimeout = const Duration(seconds: 15),
  }) async {
    int attempt = 0;
    final timeoutToUse = _isFirstRequest ? firstRequestTimeout : normalTimeout;

    while (attempt < maxTries) {
      attempt++;
      final isColdStartPossibility = _isFirstRequest || attempt > 1;

      Timer? wakingTimer;
      if (isColdStartPossibility) {
        wakingTimer = Timer(const Duration(milliseconds: 2500), () {
          isWakingUpServer.value = true;
          serverStatusMessage.value = attempt > 1
              ? 'Waking up server (retrying $attempt/$maxTries)...'
              : 'Waking up server...';
        });
      }

      try {
        final response = await requestFn(timeoutToUse);
        _isFirstRequest = false;
        wakingTimer?.cancel();
        isWakingUpServer.value = false;
        serverStatusMessage.value = null;

        // If gateway cold-start status 502/503/504 is returned, retry
        if ((response.statusCode == 502 || response.statusCode == 503 || response.statusCode == 504) &&
            attempt < maxTries) {
          isWakingUpServer.value = true;
          serverStatusMessage.value = 'Waking up server...';
          await Future.delayed(Duration(seconds: attempt * 2));
          continue;
        }

        return response;
      } catch (e) {
        wakingTimer?.cancel();
        if (kDebugMode) print('[API] Attempt $attempt/$maxTries error: $e');

        if (attempt >= maxTries) {
          isWakingUpServer.value = false;
          serverStatusMessage.value = null;
          rethrow;
        }

        isWakingUpServer.value = true;
        serverStatusMessage.value = 'Waking up server...';
        await Future.delayed(Duration(seconds: attempt * 2));
      }
    }

    isWakingUpServer.value = false;
    serverStatusMessage.value = null;
    throw http.ClientException('Max retries exceeded');
  }

  // --------------------------------------------------------------------------
  // Authentication
  // --------------------------------------------------------------------------

  Future<bool> login(String email, String password) async {
    final cleanEmail = email.trim().toLowerCase();

    try {
      final response = await _executeWithRetry(
        requestFn: (timeout) => client
            .post(
              Uri.parse('$_baseUrl/auth/login'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'email': cleanEmail,
                'password': password,
              }),
            )
            .timeout(timeout),
        maxTries: 2,
        firstRequestTimeout: const Duration(seconds: 15),
        normalTimeout: const Duration(seconds: 10),
      );

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
      final response = await client
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
      final response = await _executeWithRetry(
        requestFn: (timeout) => client
            .get(
              Uri.parse('$_baseUrl/forecasts/today'),
              headers: _headers,
            )
            .timeout(timeout),
      );

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
      final response = await _executeWithRetry(
        requestFn: (timeout) => client
            .get(
              Uri.parse('$_baseUrl/items'),
              headers: _headers,
            )
            .timeout(timeout),
      );

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
      final response = await client
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
      final response = await client
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

      final response = await client
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
      final response = await client
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
      final response = await _executeWithRetry(
        requestFn: (timeout) => client
            .get(
              Uri.parse('$_baseUrl/waste-alerts'),
              headers: _headers,
            )
            .timeout(timeout),
      );

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
      final response = await client
          .post(
            Uri.parse('$_baseUrl/sales/intraday'),
            headers: _headers,
            body: jsonEncode({'item_id': itemId, 'quantity': quantity}),
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 201;
    } catch (e) {
      if (kDebugMode) print('[API] recordIntradaySale error: $e');
      return false;
    }
  }

  Future<bool> applyDiscount(String itemId, {double? discountPct}) async {
    try {
      final response = await client
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/apply-discount'),
            headers: _headers,
            body: jsonEncode({if (discountPct != null) 'discount_pct': discountPct}),
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] applyDiscount error: $e');
      return false;
    }
  }

  Future<bool> applyBundle(String itemId, {String? partnerId, double? bundleDiscountPct}) async {
    try {
      final response = await client
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/apply-bundle'),
            headers: _headers,
            body: jsonEncode({
              if (partnerId != null) 'partner_item_id': partnerId,
              'bundle_discount_pct': bundleDiscountPct ?? 20.0,
            }),
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] applyBundle error: $e');
      return false;
    }
  }

  Future<bool> dismissAlert(String itemId) async {
    try {
      final response = await client
          .post(
            Uri.parse('$_baseUrl/waste-alerts/$itemId/dismiss'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] dismissAlert error: $e');
      return false;
    }
  }

  // --------------------------------------------------------------------------
  // Daily Operations (Closing Count, Midday Count, Yesterday Review)
  // --------------------------------------------------------------------------

  Future<Map<String, dynamic>> submitClosingCount({
    String? date,
    required List<Map<String, dynamic>> counts,
  }) async {
    final response = await client
        .post(
          Uri.parse('$_baseUrl/closing-count'),
          headers: _headers,
          body: jsonEncode({
            if (date != null) 'date': date,
            'counts': counts,
          }),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    final err = jsonDecode(response.body);
    throw Exception(err['detail'] ?? 'Failed to submit closing count');
  }

  Future<Map<String, dynamic>> submitMiddayCount({
    required List<Map<String, dynamic>> counts,
  }) async {
    final response = await client
        .post(
          Uri.parse('$_baseUrl/midday-count'),
          headers: _headers,
          body: jsonEncode({'counts': counts}),
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    final err = jsonDecode(response.body);
    throw Exception(err['detail'] ?? 'Failed to submit midday count');
  }

  Future<Map<String, dynamic>> fetchYesterdayReview() async {
    final response = await client
        .get(
          Uri.parse('$_baseUrl/review/yesterday'),
          headers: _headers,
        )
        .timeout(const Duration(seconds: 15));

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception('Failed to load yesterday review');
  }

  // --------------------------------------------------------------------------
  // User Profile
  // --------------------------------------------------------------------------

  Future<Map<String, dynamic>?> fetchUserProfile() async {
    try {
      final response = await client
          .get(
            Uri.parse('$_baseUrl/me'),
            headers: _headers,
          )
          .timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      if (kDebugMode) print('[API] fetchUserProfile error: $e');
    }
    return null;
  }

  Future<bool> updateUserProfile({
    String? name,
    String? storeName,
    String? timezone,
    double? openingHour,
    double? closingHour,
    String? currency,
    bool? onboardingCompleted,
  }) async {
    try {
      final payload = <String, dynamic>{
        if (name != null) 'name': name,
        if (storeName != null) 'store_name': storeName,
        if (timezone != null) 'timezone': timezone,
        if (openingHour != null) 'opening_hour': openingHour,
        if (closingHour != null) 'closing_hour': closingHour,
        if (currency != null) 'currency': currency,
        if (onboardingCompleted != null) 'onboarding_completed': onboardingCompleted,
      };

      final response = await client
          .patch(
            Uri.parse('$_baseUrl/me'),
            headers: _headers,
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 10));

      return response.statusCode == 200;
    } catch (e) {
      if (kDebugMode) print('[API] updateUserProfile error: $e');
      return false;
    }
  }

  // --------------------------------------------------------------------------
  // AI Executive Briefing & Manager Assistant (Google Gemini)
  // --------------------------------------------------------------------------

  Future<Map<String, dynamic>?> fetchTodayBriefing() async {
    try {
      final response = await _executeWithRetry(
        requestFn: (timeout) => client
            .get(
              Uri.parse('$_baseUrl/briefing/today'),
              headers: _headers,
            )
            .timeout(timeout),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['briefing'] as Map<String, dynamic>?;
      }
      return null;
    } catch (e) {
      if (kDebugMode) print('[API] fetchTodayBriefing error: $e');
      return null;
    }
  }

  Future<String?> askAssistant(String query) async {
    final cleanQuery = query.trim();
    if (cleanQuery.isEmpty) return null;

    try {
      final response = await client
          .post(
            Uri.parse('$_baseUrl/assistant/chat'),
            headers: _headers,
            body: jsonEncode({'query': cleanQuery}),
          )
          .timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final reply = data['reply'] as String?;
        if (reply != null && reply.trim().isNotEmpty) {
          return reply.trim();
        }
      }
    } catch (e) {
      if (kDebugMode) print('[API] askAssistant network error: $e');
    }

    // No canned responses: return null so UI renders honest error / retry state
    return null;
  }
}
