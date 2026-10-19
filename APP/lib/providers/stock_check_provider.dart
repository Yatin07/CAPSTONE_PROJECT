import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/stock_check_entry.dart';

class StockCheckProvider extends ChangeNotifier {
  final List<StockCheckEntry> _entries = [
    StockCheckEntry(
      id: '1',
      name: 'Croissants',
      category: 'Bakery',
      suggestedQuantity: 30,
      actualQuantity: 30,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: true,
    ),
    StockCheckEntry(
      id: '2',
      name: 'Traditional Baguette',
      category: 'Bakery',
      suggestedQuantity: 8,
      actualQuantity: 8,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: true,
    ),
    StockCheckEntry(
      id: '3',
      name: 'Pain au Chocolat',
      category: 'Bakery',
      suggestedQuantity: 15,
      actualQuantity: 15,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: true,
    ),
    StockCheckEntry(
      id: '4',
      name: 'Whole Milk',
      category: 'Dairy',
      suggestedQuantity: 4,
      actualQuantity: 4,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: true,
    ),
    StockCheckEntry(
      id: '5',
      name: 'Espresso Beans',
      category: 'Beverage',
      suggestedQuantity: 20,
      actualQuantity: 20,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: false,
    ),
  ];

  bool _isConfirmed = false;

  List<StockCheckEntry> get entries => List.unmodifiable(_entries);

  bool get isConfirmed => _isConfirmed;

  void updateQuantity(String id, int newQuantity) {
    final index = _entries.indexWhere((entry) => entry.id == id);
    if (index != -1) {
      final entry = _entries[index];
      if (entry.isPerishable) return;

      final updatedQty = max(0, newQuantity);
      _entries[index] = entry.copyWith(
        actualQuantity: updatedQty,
        isAutoCalculated: false,
        isManualOverride: true,
      );
      _isConfirmed = false;
      notifyListeners();
    }
  }

  void confirmStock() {
    _isConfirmed = true;
    notifyListeners();
  }

  void resetStockCheck() {
    _isConfirmed = false;
    notifyListeners();
  }
}
