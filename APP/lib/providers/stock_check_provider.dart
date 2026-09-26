import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/stock_check_entry.dart';

class StockCheckProvider extends ChangeNotifier {
  final List<StockCheckEntry> _entries = [
    StockCheckEntry(
      id: '1',
      name: 'Almond Milk (Barista)',
      suggestedQuantity: 5,
      actualQuantity: 5,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: false,
    ),
    StockCheckEntry(
      id: '2',
      name: 'Espresso Beans (House)',
      suggestedQuantity: 12,
      actualQuantity: 12,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: false,
    ),
    StockCheckEntry(
      id: '3',
      name: 'Croissants (Butter)',
      category: 'Pastries',
      suggestedQuantity: 0,
      actualQuantity: 0,
      isAutoCalculated: true,
      isManualOverride: false,
      isPerishable: true,
    ),
    StockCheckEntry(
      id: '4',
      name: 'Oat Milk',
      suggestedQuantity: 8,
      actualQuantity: 8,
      isAutoCalculated: false,
      isManualOverride: true,
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
