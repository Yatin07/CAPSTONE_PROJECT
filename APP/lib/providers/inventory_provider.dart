import 'package:flutter/foundation.dart';
import '../models/inventory_item.dart';

class InventoryProvider extends ChangeNotifier {
  final List<InventoryItem> _items = [
    InventoryItem(
      id: '1',
      name: 'Croissants',
      category: 'Bakery',
      unit: 'Units',
      currentStock: 10,
      isPerishable: true,
      price: 3.50,
      predictedDemand: 50,
      safetyStock: 5,
      description: 'Demand rising — weekend ahead',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(hours: 24)),
    ),
    InventoryItem(
      id: '2',
      name: 'Espresso Beans',
      category: 'Beverage',
      unit: 'LBS',
      currentStock: 6,
      isPerishable: false,
      price: 12.00,
      predictedDemand: 15,
      safetyStock: 3,
      description: 'Steady consumption,\nlow stock\napproaching',
      riskLevel: 'normal',
      updatedAt: DateTime.now().subtract(const Duration(days: 5)),
    ),
    InventoryItem(
      id: '3',
      name: 'Whole Milk',
      category: 'Beverage',
      unit: 'GAL',
      currentStock: 4,
      isPerishable: true,
      price: 4.50,
      predictedDemand: 10,
      safetyStock: 2,
      description: 'High spoilage risk\nbased on recent data',
      riskLevel: 'high',
      updatedAt: DateTime.now().subtract(const Duration(hours: 2)),
    ),
  ];

  InventoryItem? _editingItem;

  List<InventoryItem> get items => List.unmodifiable(_items);

  int get itemCount => _items.length;

  InventoryItem? get editingItem => _editingItem;

  bool get isEditing => _editingItem != null;

  void startEditing(InventoryItem item) {
    _editingItem = item;
    notifyListeners();
  }

  void clearEditing() {
    _editingItem = null;
    notifyListeners();
  }

  void addItem({
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
  }) {
    final newItem = InventoryItem(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      name: name,
      category: category,
      unit: unit,
      currentStock: currentStock,
      isPerishable: isPerishable,
      predictedDemand: currentStock + 15,
      safetyStock: 5,
      description: 'Demand steady — standard restocking pattern',
      updatedAt: DateTime.now(),
    );
    _items.add(newItem);
    notifyListeners();
  }

  void updateItem({
    required String id,
    required String name,
    required String category,
    required String unit,
    required int currentStock,
    required bool isPerishable,
  }) {
    final index = _items.indexWhere((item) => item.id == id);
    if (index != -1) {
      _items[index] = _items[index].copyWith(
        name: name,
        category: category,
        unit: unit,
        currentStock: currentStock,
        isPerishable: isPerishable,
        updatedAt: DateTime.now(),
      );
      if (_editingItem?.id == id) {
        _editingItem = null;
      }
      notifyListeners();
    }
  }

  void deleteItem(String id) {
    _items.removeWhere((item) => item.id == id);
    if (_editingItem?.id == id) {
      _editingItem = null;
    }
    notifyListeners();
  }
}
