import 'package:flutter/foundation.dart';
import '../models/inventory_item.dart';
import '../services/api_service.dart';

class InventoryProvider extends ChangeNotifier {
  final List<InventoryItem> _items = [
    InventoryItem(
      id: '1',
      name: 'Croissants',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 30,
      isPerishable: true,
      price: 3.50,
      predictedDemand: 80,
      safetyStock: 40,
      description: 'High weekend demand pattern detected based on historical seasonality.',
      riskLevel: 'medium',
      updatedAt: DateTime.now().subtract(const Duration(hours: 4)),
    ),
    InventoryItem(
      id: '2',
      name: 'Traditional Baguette',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 8,
      isPerishable: true,
      price: 2.80,
      predictedDemand: 39,
      safetyStock: 15,
      description: 'Demand rising — standard restocking pattern',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(hours: 1)),
    ),
    InventoryItem(
      id: '3',
      name: 'Pain au Chocolat',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 15,
      isPerishable: true,
      price: 3.75,
      predictedDemand: 62,
      safetyStock: 27,
      description: 'Steady consumption approaching minimum safety threshold',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    InventoryItem(
      id: '4',
      name: 'Whole Milk',
      category: 'Dairy',
      unit: 'GAL',
      currentStock: 4,
      isPerishable: true,
      price: 4.50,
      predictedDemand: 42,
      safetyStock: 19,
      description: 'High spoilage risk based on recent data',
      riskLevel: 'high',
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
    InventoryItem(
      id: '5',
      name: 'Espresso Beans',
      category: 'Beverage',
      unit: 'LBS',
      currentStock: 20,
      isPerishable: false,
      price: 14.00,
      predictedDemand: 5,
      safetyStock: 4,
      description: 'Stock optimal — stable baseline consumption',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
  ];

  InventoryItem? _editingItem;
  bool _isLoading = false;
  String? _errorMessage;
  String _dashboardSummary = "Restock needed for active items. Cold-start engine tracking new inventory.";
  int _actionRequiredCount = 3;
  Map<String, dynamic>? _aiBriefing;
  bool _isAiBriefingLoading = false;

  List<InventoryItem> get items => List.unmodifiable(_items);
  int get itemCount => _items.length;
  InventoryItem? get editingItem => _editingItem;
  bool get isEditing => _editingItem != null;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String get dashboardSummary => _dashboardSummary;
  int get actionRequiredCount => _actionRequiredCount;
  Map<String, dynamic>? get aiBriefing => _aiBriefing;
  bool get isAiBriefingLoading => _isAiBriefingLoading;
  List<String> get aiActions {
    if (_aiBriefing != null && _aiBriefing!['actions'] is List) {
      return List<String>.from(_aiBriefing!['actions']);
    }
    return [];
  }

  InventoryProvider() {
    // Automatically fetch live items from MongoDB Atlas upon initialization
    fetchDashboardItems();
  }

  void startEditing(InventoryItem item) {
    _editingItem = item;
    notifyListeners();
  }

  void clearEditing() {
    _editingItem = null;
    notifyListeners();
  }

  /// Fetches real, live forecast & inventory state from FastAPI / MongoDB Atlas
  Future<void> fetchDashboardItems() async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final dashboardData = await ApiService.instance.fetchTodayDashboard();
      if (dashboardData != null && dashboardData['items'] != null) {
        final liveItems = dashboardData['items'] as List<InventoryItem>;
        _items.clear();
        _items.addAll(liveItems);
        _dashboardSummary = dashboardData['summary']?.toString() ?? 
            (liveItems.isEmpty ? "No inventory items found. Add items to enable AI forecasting." : _dashboardSummary);
        _actionRequiredCount = (dashboardData['action_required_count'] as num?)?.toInt() ?? 0;
        if (kDebugMode) print('[Provider] Successfully synced ${_items.length} items from Atlas.');
      }
    } catch (e) {
      _errorMessage = 'Could not sync with cloud. Displaying cached inventory.';
      if (kDebugMode) print('[Provider] fetchDashboardItems error: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }

    // Simultaneously fetch AI briefing in background
    fetchAiBriefing();
  }

  /// Fetches executive AI daily operational briefing from Gemini
  Future<void> fetchAiBriefing() async {
    _isAiBriefingLoading = true;
    notifyListeners();

    try {
      final briefing = await ApiService.instance.fetchTodayBriefing();
      if (briefing != null) {
        _aiBriefing = briefing;
        final summary = briefing['executive_summary']?.toString();
        if (summary != null && summary.isNotEmpty) {
          _dashboardSummary = summary;
        }
        if (kDebugMode) print('[Provider] Successfully loaded Gemini AI Briefing.');
      }
    } catch (e) {
      if (kDebugMode) print('[Provider] fetchAiBriefing error: $e');
    } finally {
      _isAiBriefingLoading = false;
      notifyListeners();
    }
  }

  void setAiBriefingForTest(Map<String, dynamic> briefing) {
    _aiBriefing = briefing;
    notifyListeners();
  }

  Future<void> addItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  }) async {
    final tempId = DateTime.now().millisecondsSinceEpoch.toString();
    final localItem = InventoryItem(
      id: tempId,
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

    _items.add(localItem);
    notifyListeners();

    // Persist to MongoDB Atlas asynchronously
    try {
      final cloudItem = await ApiService.instance.createItem(
        name: name,
        category: category,
        unit: unit,
        currentStock: currentStock,
        isPerishable: isPerishable,
        price: price,
      );

      if (cloudItem != null) {
        final idx = _items.indexWhere((it) => it.id == tempId);
        if (idx != -1) {
          _items[idx] = cloudItem;
          notifyListeners();
        }
      }
    } catch (e) {
      if (kDebugMode) print('[Provider] Cloud addItem error: $e');
    }
  }

  Future<void> updateItem({
    required String id,
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
    double? price,
  }) async {
    final index = _items.indexWhere((item) => item.id == id);
    if (index != -1) {
      _items[index] = _items[index].copyWith(
        name: name,
        category: category,
        unit: unit,
        currentStock: currentStock,
        isPerishable: isPerishable,
        price: price,
        updatedAt: DateTime.now(),
      );
      if (_editingItem?.id == id) {
        _editingItem = null;
      }
      notifyListeners();

      // Sync to Atlas
      await ApiService.instance.updateItem(
        id,
        name: name,
        category: category,
        unit: unit,
        currentStock: currentStock,
        isPerishable: isPerishable,
        price: price,
      );
    }
  }

  Future<void> deleteItem(String id) async {
    _items.removeWhere((item) => item.id == id);
    if (_editingItem?.id == id) {
      _editingItem = null;
    }
    notifyListeners();

    // Delete in Atlas
    await ApiService.instance.deleteItem(id);
  }

  Future<bool> confirmRestock(String itemId, {int? quantity}) async {
    final index = _items.indexWhere((it) => it.id == itemId);
    if (index != -1) {
      final item = _items[index];
      final qtyToAdd = quantity ?? item.restockQuantity;
      final newStock = item.currentStock + qtyToAdd;

      _items[index] = item.copyWith(
        currentStock: newStock,
        updatedAt: DateTime.now(),
      );
      notifyListeners();

      // Sync restock to Atlas
      return await ApiService.instance.restockItem(itemId, quantity: quantity);
    }
    return false;
  }
}
