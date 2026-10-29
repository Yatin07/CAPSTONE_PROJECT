import 'package:flutter/material.dart';
import '../models/inventory_item.dart';
import '../models/waste_alert.dart';
import '../services/api_service.dart';

/// Contract for data access in RestockIQ.
/// Two concrete implementations:
///   1. [LiveRepository]: Real API data only, connects to FastAPI/Atlas backend, starts empty.
///   2. [SampleRepository]: In-memory sample data for the first-time tour / replay tour.
abstract class AppRepository {
  bool get isDemoTour;
  String get modeLabel;

  Future<Map<String, dynamic>> fetchDashboard();
  Future<List<InventoryItem>> fetchItems();
  Future<InventoryItem?> createItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  });
  Future<bool> updateItem(
    String itemId, {
    String? name,
    String? category,
    String? unit,
    int? currentStock,
    bool? isPerishable,
    double? price,
  });
  Future<bool> deleteItem(String itemId);
  Future<bool> restockItem(String itemId, {int? quantity});
  Future<List<WasteAlert>> fetchWasteAlerts();
  Future<bool> applyDiscount(String itemId, {double? discountPct});
  Future<bool> applyBundle(String itemId, {String? partnerId, double? discountPct});
  Future<bool> dismissAlert(String itemId);
  Future<Map<String, dynamic>?> fetchTodayBriefing();
  Future<String?> askAssistant(String query);
  Future<Map<String, dynamic>> submitClosingCount(String? date, List<Map<String, dynamic>> counts);
  Future<Map<String, dynamic>> submitMiddayCount(List<Map<String, dynamic>> counts);
  Future<Map<String, dynamic>> fetchYesterdayReview();
  Future<Map<String, dynamic>?> fetchUserProfile();
  Future<bool> updateUserProfile({
    String? name,
    String? storeName,
    String? timezone,
    double? openingHour,
    double? closingHour,
    String? currency,
    bool? onboardingCompleted,
  });
}

/// Real backend repository implementation targeting FastAPI + MongoDB Atlas.
class LiveRepository implements AppRepository {
  final ApiService api;

  LiveRepository({ApiService? apiService}) : api = apiService ?? ApiService.instance;

  @override
  bool get isDemoTour => api.isDemoWorkspace;

  @override
  String get modeLabel => api.isDemoWorkspace ? 'DEMO' : 'LIVE';

  @override
  Future<Map<String, dynamic>> fetchDashboard() async {
    final result = await api.fetchTodayDashboard();
    if (result == null) {
      throw Exception('Failed to connect to backend server or fetch dashboard data.');
    }
    return result;
  }

  @override
  Future<List<InventoryItem>> fetchItems() async {
    final items = await api.fetchItems();
    if (items == null) {
      throw Exception('Failed to connect to backend server or fetch inventory items.');
    }
    return items;
  }

  @override
  Future<InventoryItem?> createItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  }) {
    return api.createItem(
      name: name,
      category: category,
      unit: unit,
      currentStock: currentStock,
      isPerishable: isPerishable,
      price: price,
    );
  }

  @override
  Future<bool> updateItem(
    String itemId, {
    String? name,
    String? category,
    String? unit,
    int? currentStock,
    bool? isPerishable,
    double? price,
  }) {
    return api.updateItem(
      itemId,
      name: name,
      category: category,
      unit: unit,
      currentStock: currentStock,
      isPerishable: isPerishable,
      price: price,
    );
  }

  @override
  Future<bool> deleteItem(String itemId) => api.deleteItem(itemId);

  @override
  Future<bool> restockItem(String itemId, {int? quantity}) =>
      api.restockItem(itemId, quantity: quantity);

  @override
  Future<List<WasteAlert>> fetchWasteAlerts() async {
    final alerts = await api.fetchWasteAlerts();
    if (alerts == null) {
      throw Exception('Failed to connect to backend server or fetch waste alerts.');
    }
    return alerts;
  }

  @override
  Future<bool> applyDiscount(String itemId, {double? discountPct}) =>
      api.applyDiscount(itemId, discountPct: discountPct);

  @override
  Future<bool> applyBundle(String itemId, {String? partnerId, double? discountPct}) =>
      api.applyBundle(itemId, partnerId: partnerId, bundleDiscountPct: discountPct);

  @override
  Future<bool> dismissAlert(String itemId) => api.dismissAlert(itemId);

  @override
  Future<Map<String, dynamic>?> fetchTodayBriefing() => api.fetchTodayBriefing();

  @override
  Future<String?> askAssistant(String query) => api.askAssistant(query);

  @override
  Future<Map<String, dynamic>> submitClosingCount(String? date, List<Map<String, dynamic>> counts) =>
      api.submitClosingCount(date: date, counts: counts);

  @override
  Future<Map<String, dynamic>> submitMiddayCount(List<Map<String, dynamic>> counts) =>
      api.submitMiddayCount(counts: counts);

  @override
  Future<Map<String, dynamic>> fetchYesterdayReview() => api.fetchYesterdayReview();

  @override
  Future<Map<String, dynamic>?> fetchUserProfile() => api.fetchUserProfile();

  @override
  Future<bool> updateUserProfile({
    String? name,
    String? storeName,
    String? timezone,
    double? openingHour,
    double? closingHour,
    String? currency,
    bool? onboardingCompleted,
  }) =>
      api.updateUserProfile(
        name: name,
        storeName: storeName,
        timezone: timezone,
        openingHour: openingHour,
        closingHour: closingHour,
        currency: currency,
        onboardingCompleted: onboardingCompleted,
      );
}

/// In-memory sample repository used strictly for the interactive app tour.
/// Makes zero network calls and saves nothing to the backend.
class SampleRepository implements AppRepository {
  final List<InventoryItem> _sampleItems = [
    InventoryItem(
      id: 'tour_1',
      name: 'Croissants',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 30,
      isPerishable: true,
      price: 3.50,
      predictedDemand: 80,
      safetyStock: 40,
      daysOfData: 45,
      maturity: 'Mature',
      maturityLabel: 'Mature (45 days)',
      description: 'High weekend demand pattern detected based on historical seasonality.',
      riskLevel: 'medium',
      updatedAt: DateTime.now().subtract(const Duration(hours: 4)),
    ),
    InventoryItem(
      id: 'tour_2',
      name: 'Traditional Baguette',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 8,
      isPerishable: true,
      price: 2.80,
      predictedDemand: 39,
      safetyStock: 15,
      daysOfData: 32,
      maturity: 'Mature',
      maturityLabel: 'Mature (32 days)',
      description: 'Demand rising — standard restocking pattern',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(hours: 1)),
    ),
    InventoryItem(
      id: 'tour_3',
      name: 'Pain au Chocolat',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 15,
      isPerishable: true,
      price: 3.75,
      predictedDemand: 62,
      safetyStock: 27,
      daysOfData: 21,
      maturity: 'Improving',
      maturityLabel: 'Improving (21/28 days)',
      description: 'Steady consumption approaching minimum safety threshold',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    InventoryItem(
      id: 'tour_4',
      name: 'Whole Milk',
      category: 'Beverage',
      unit: 'GAL',
      currentStock: 4,
      isPerishable: true,
      price: 4.50,
      predictedDemand: 42,
      safetyStock: 19,
      daysOfData: 18,
      maturity: 'Improving',
      maturityLabel: 'Improving (18/28 days)',
      description: 'High spoilage risk — consumption pace below forecast',
      riskLevel: 'high',
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    InventoryItem(
      id: 'tour_5',
      name: 'Espresso Beans',
      category: 'Beverage',
      unit: 'LBS',
      currentStock: 20,
      isPerishable: false,
      price: 14.00,
      predictedDemand: 5,
      safetyStock: 4,
      daysOfData: 60,
      maturity: 'Mature',
      maturityLabel: 'Mature (60 days)',
      description: 'Stock optimal — stable baseline consumption',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
  ];

  late final List<WasteAlert> _sampleAlerts = [
    const WasteAlert(
      id: 'tour_2',
      itemName: 'Traditional Baguette',
      salesText: '40% of expected sales so far\ntoday',
      progress: 0.40,
      severityLabel: 'Low Pace',
      severityColor: Color(0xFFB91C1C),
      recommendedActionText: 'Suggest 10% Discount',
      recommendedActionIcon: Icons.local_offer_outlined,
      recommendedActionColor: Color(0xFF8B1E22),
      recommendedDoneText: 'Discount Suggested',
      primaryActionText: 'Apply Discount',
      primaryDoneText: 'Discount Applied',
      layoutStyle: WasteAlertCardLayoutStyle.stacked,
      foodType: 'baguette',
    ),
    const WasteAlert(
      id: 'tour_4',
      itemName: 'Whole Milk',
      salesText: '25% of expected sales so far\ntoday',
      progress: 0.25,
      severityLabel: 'Critical',
      severityColor: Color(0xFFD97706),
      recommendedActionText: 'Apply 20% Bundle',
      recommendedActionIcon: Icons.local_offer_outlined,
      recommendedActionColor: Color(0xFFFFB702),
      recommendedDoneText: 'Bundle Applied',
      primaryActionText: 'Apply Bundle',
      primaryDoneText: 'Bundle Active',
      layoutStyle: WasteAlertCardLayoutStyle.sideBySide,
      foodType: 'milk',
      partnerItem: {
        'id': 'tour_1',
        'name': 'Croissants',
        'category': 'Bakery',
        'price': 3.50,
        'comboOriginalPrice': 8.00,
        'bundlePrice': 6.40,
        'discountPct': 20,
      },
      bundleDiscountPct: 20,
    ),
  ];

  @override
  bool get isDemoTour => true;

  @override
  String get modeLabel => 'DEMO TOUR';

  @override
  Future<Map<String, dynamic>> fetchDashboard() async {
    return {
      'summary': 'DEMO TOUR: Sample bakery dataset loaded. AI models trained on 60 days.',
      'total_items': _sampleItems.length,
      'action_required_count': 2,
      'items': List<InventoryItem>.from(_sampleItems),
    };
  }

  @override
  Future<List<InventoryItem>> fetchItems() async => List<InventoryItem>.from(_sampleItems);

  @override
  Future<InventoryItem?> createItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  }) async {
    final newItem = InventoryItem(
      id: 'tour_${DateTime.now().millisecondsSinceEpoch}',
      name: name,
      category: category,
      unit: unit,
      currentStock: currentStock,
      isPerishable: isPerishable,
      price: price,
      predictedDemand: currentStock + 10,
      safetyStock: 5,
      daysOfData: 0,
      maturity: 'Learning',
      maturityLabel: 'Learning (0/7 days)',
      description: 'Cold-start sample item',
      updatedAt: DateTime.now(),
    );
    _sampleItems.add(newItem);
    return newItem;
  }

  @override
  Future<bool> updateItem(
    String itemId, {
    String? name,
    String? category,
    String? unit,
    int? currentStock,
    bool? isPerishable,
    double? price,
  }) async {
    final idx = _sampleItems.indexWhere((it) => it.id == itemId);
    if (idx != -1) {
      _sampleItems[idx] = _sampleItems[idx].copyWith(
        name: name,
        category: category,
        unit: unit,
        currentStock: currentStock,
        isPerishable: isPerishable,
        price: price,
      );
      return true;
    }
    return false;
  }

  @override
  Future<bool> deleteItem(String itemId) async {
    _sampleItems.removeWhere((it) => it.id == itemId);
    return true;
  }

  @override
  Future<bool> restockItem(String itemId, {int? quantity}) async {
    final idx = _sampleItems.indexWhere((it) => it.id == itemId);
    if (idx != -1) {
      final qty = quantity ?? 10;
      _sampleItems[idx] = _sampleItems[idx].copyWith(
        currentStock: _sampleItems[idx].currentStock + qty,
      );
      return true;
    }
    return false;
  }

  @override
  Future<List<WasteAlert>> fetchWasteAlerts() async => List<WasteAlert>.from(_sampleAlerts);

  @override
  Future<bool> applyDiscount(String itemId, {double? discountPct}) async {
    final idx = _sampleAlerts.indexWhere((a) => a.id == itemId);
    if (idx != -1) {
      _sampleAlerts[idx] = _sampleAlerts[idx].copyWith(isPrimaryActionDone: true);
      return true;
    }
    return false;
  }

  @override
  Future<bool> applyBundle(String itemId, {String? partnerId, double? discountPct}) async {
    final idx = _sampleAlerts.indexWhere((a) => a.id == itemId);
    if (idx != -1) {
      _sampleAlerts[idx] = _sampleAlerts[idx].copyWith(
        isRecommendedActionDone: true,
        isPrimaryActionDone: true,
      );
      return true;
    }
    return false;
  }

  @override
  Future<bool> dismissAlert(String itemId) async {
    final idx = _sampleAlerts.indexWhere((a) => a.id == itemId);
    if (idx != -1) {
      _sampleAlerts[idx] = _sampleAlerts[idx].copyWith(isDismissed: true);
      return true;
    }
    return false;
  }

  @override
  Future<Map<String, dynamic>?> fetchTodayBriefing() async {
    return {
      'source': 'tour-demo',
      'executive_summary':
          'Welcome to RestockIQ Tour! Whole Milk has high waste risk (sales pace 0.28); pair with Croissants for a 20% combo discount. Traditional Baguettes require 46 units replenishment.',
      'actions': [
        'Restock 46 units of Traditional Baguette to prevent stockout.',
        'Apply 20% combo bundle pairing Whole Milk with Croissants.',
        'Apply 10% promotional discount to afternoon baguette batch.',
      ],
    };
  }

  @override
  Future<String?> askAssistant(String query) async {
    return "This is Tour Demo Mode. In live mode, your questions are grounded in real MongoDB Atlas inventory data and answered with zero-math precision by Google Gemini.";
  }

  @override
  Future<Map<String, dynamic>> submitClosingCount(String? date, List<Map<String, dynamic>> counts) async {
    return {
      'status': 'success',
      'date': date ?? 'today',
      'processed_count': counts.length,
      'items': counts,
    };
  }

  @override
  Future<Map<String, dynamic>> submitMiddayCount(List<Map<String, dynamic>> counts) async {
    return {
      'status': 'success',
      'elapsed_fraction': 0.5,
      'items': counts,
    };
  }

  @override
  Future<Map<String, dynamic>> fetchYesterdayReview() async {
    return {
      'status': 'success',
      'date': 'yesterday',
      'summary': {'total_items': 5, 'completed_count': 5, 'missing_count': 0},
      'items': [
        {
          'itemId': 'tour_1',
          'itemName': 'Croissants',
          'category': 'Bakery',
          'status': 'completed',
          'sellThrough': 0.92,
          'sellThroughPct': 92,
          'label': 'High',
          'color': '#10B981',
          'openingStock': 50,
          'producedOrRestocked': 30,
          'availableStock': 80,
          'soldUnits': 74,
          'wasteUnits': 6,
          'closingCount': 6,
          'date': 'yesterday',
        },
        {
          'itemId': 'tour_2',
          'itemName': 'Traditional Baguette',
          'category': 'Bakery',
          'status': 'completed',
          'sellThrough': 0.78,
          'sellThroughPct': 78,
          'label': 'Normal',
          'color': '#3B82F6',
          'openingStock': 40,
          'producedOrRestocked': 10,
          'availableStock': 50,
          'soldUnits': 39,
          'wasteUnits': 11,
          'closingCount': 11,
          'date': 'yesterday',
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>?> fetchUserProfile() async {
    return {
      'id': 'tour_user',
      'name': 'Demo Manager',
      'email': 'tour@restockiq.com',
      'role': 'owner',
      'store_name': 'Corner Crumb Bakery (Demo)',
      'timezone': 'Asia/Kolkata',
      'opening_hour': 8.0,
      'closing_hour': 20.0,
      'currency': '₹',
      'onboarding_completed': false,
      'created_at': DateTime.now().toIso8601String(),
    };
  }

  @override
  Future<bool> updateUserProfile({
    String? name,
    String? storeName,
    String? timezone,
    double? openingHour,
    double? closingHour,
    String? currency,
    bool? onboardingCompleted,
  }) async {
    return true;
  }
}
