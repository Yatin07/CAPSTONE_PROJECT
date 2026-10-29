import 'dart:math';
import 'package:flutter/foundation.dart';
import '../models/inventory_item.dart';
import '../models/stock_check_entry.dart';
import '../repositories/app_repository.dart';

class StockCheckProvider extends ChangeNotifier {
  AppRepository _repository;
  final List<StockCheckEntry> _entries = [];
  bool _isConfirmed = false;
  bool _isSubmitting = false;
  String? _submissionMessage;
  String? _submissionError;

  // Midday state
  bool _isMiddaySubmitting = false;
  Map<String, dynamic>? _middayResult;

  // Yesterday review state
  bool _isReviewLoading = false;
  Map<String, dynamic>? _yesterdayReview;

  AppRepository get repository => _repository;
  List<StockCheckEntry> get entries => List.unmodifiable(_entries);
  bool get isConfirmed => _isConfirmed;
  bool get isSubmitting => _isSubmitting;
  String? get submissionMessage => _submissionMessage;
  String? get submissionError => _submissionError;

  bool get isMiddaySubmitting => _isMiddaySubmitting;
  Map<String, dynamic>? get middayResult => _middayResult;

  bool get isReviewLoading => _isReviewLoading;
  Map<String, dynamic>? get yesterdayReview => _yesterdayReview;

  bool get hasValidationErrors => _entries.any((e) => e.validationError != null);

  StockCheckProvider({AppRepository? repository})
      : _repository = repository ?? LiveRepository();

  void setRepository(AppRepository newRepo) {
    _repository = newRepo;
    _entries.clear();
    _yesterdayReview = null;
    _middayResult = null;
    _isConfirmed = false;
    notifyListeners();
  }

  void syncWithInventoryItems(List<InventoryItem> items) {
    if (items.isEmpty) {
      return;
    }

    // Preserve existing entries or create from items
    final updated = <StockCheckEntry>[];
    for (final it in items) {
      final existingIndex = _entries.indexWhere((e) => e.id == it.id);
      if (existingIndex != -1) {
        updated.add(_entries[existingIndex]);
      } else {
        final opening = max(0, it.currentStock);
        updated.add(
          StockCheckEntry(
            id: it.id,
            name: it.name,
            category: it.category,
            suggestedQuantity: opening,
            actualQuantity: opening,
            isAutoCalculated: true,
            isManualOverride: false,
            isPerishable: it.isPerishable,
            openingStock: opening,
            producedOrRestocked: 0,
            closingUnitsLeft: opening,
            soldUnits: 0,
            wasteUnits: it.isPerishable ? opening : 0,
          ),
        );
      }
    }
    _entries.clear();
    _entries.addAll(updated);
    notifyListeners();
  }

  void initForTestingWithSampleData() {
    _entries.clear();
    _entries.addAll([
      StockCheckEntry(
        id: '1',
        name: 'Croissants',
        category: 'Bakery',
        suggestedQuantity: 30,
        actualQuantity: 30,
        isAutoCalculated: true,
        isManualOverride: false,
        isPerishable: true,
        openingStock: 25,
        producedOrRestocked: 15,
        closingUnitsLeft: 10,
        soldUnits: 30,
        wasteUnits: 10,
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
        openingStock: 20,
        producedOrRestocked: 10,
        closingUnitsLeft: 6,
        soldUnits: 24,
        wasteUnits: 6,
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
        openingStock: 15,
        producedOrRestocked: 15,
        closingUnitsLeft: 8,
        soldUnits: 22,
        wasteUnits: 8,
      ),
      StockCheckEntry(
        id: '4',
        name: 'Whole Milk',
        category: 'Beverage',
        suggestedQuantity: 4,
        actualQuantity: 4,
        isAutoCalculated: true,
        isManualOverride: false,
        isPerishable: true,
        openingStock: 10,
        producedOrRestocked: 5,
        closingUnitsLeft: 4,
        soldUnits: 11,
        wasteUnits: 4,
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
        openingStock: 25,
        producedOrRestocked: 0,
        closingUnitsLeft: 20,
        soldUnits: 5,
        wasteUnits: 0,
      ),
    ]);
    _isConfirmed = false;
    notifyListeners();
  }

  void updateProducedQuantity(String id, int produced) {
    final idx = _entries.indexWhere((e) => e.id == id);
    if (idx != -1) {
      final entry = _entries[idx];
      final newProduced = max(0, produced);
      _entries[idx] = entry.copyWith(
        producedOrRestocked: newProduced,
      );
      // Re-validate closing count
      if (entry.closingUnitsLeft != null) {
        updateClosingUnitsLeft(id, entry.closingUnitsLeft!);
      } else {
        notifyListeners();
      }
    }
  }

  void updateClosingUnitsLeft(String id, int unitsLeft) {
    final idx = _entries.indexWhere((e) => e.id == id);
    if (idx != -1) {
      final entry = _entries[idx];
      final available = entry.availableStock;
      String? error;
      if (unitsLeft > available) {
        error = 'Left ($unitsLeft) cannot exceed available ($available)';
      } else if (unitsLeft < 0) {
        error = 'Cannot be negative';
      }

      final sold = max(0, available - unitsLeft);
      final waste = entry.isPerishable ? unitsLeft : 0;

      _entries[idx] = entry.copyWith(
        closingUnitsLeft: unitsLeft,
        soldUnits: error == null ? sold : entry.soldUnits,
        wasteUnits: error == null ? waste : entry.wasteUnits,
        validationError: error,
      );
      notifyListeners();
    }
  }

  void updateQuantity(String id, int newQuantity) {
    final index = _entries.indexWhere((entry) => entry.id == id);
    if (index != -1) {
      final entry = _entries[index];
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

  Future<bool> submitClosingRoutine({required String? targetDate}) async {
    if (hasValidationErrors) return false;

    _isSubmitting = true;
    _submissionError = null;
    _submissionMessage = null;
    notifyListeners();

    try {
      final countsPayload = _entries.map((e) {
        return {
          'item_id': e.id,
          'item_name': e.name,
          'units_left': e.closingUnitsLeft ?? e.actualQuantity,
          'produced_or_restocked': e.producedOrRestocked,
        };
      }).toList();

      final res = await _repository.submitClosingCount(targetDate, countsPayload);
      if (res['status'] == 'success') {
        _isConfirmed = true;
        _submissionMessage = 'Closing count recorded successfully for ${res['date'] ?? 'today'}.';
        _isSubmitting = false;
        notifyListeners();
        return true;
      } else {
        _submissionError = res['message'] ?? 'Failed to record closing count';
      }
    } catch (e) {
      _submissionError = 'Network error recording closing count: $e';
    }

    _isSubmitting = false;
    notifyListeners();
    return false;
  }

  Future<bool> submitMiddayRoutine(Map<String, int> remainingCounts) async {
    _isMiddaySubmitting = true;
    notifyListeners();

    try {
      final countsPayload = remainingCounts.entries.map((entry) {
        return {
          'item_id': entry.key,
          'remaining_count': entry.value,
        };
      }).toList();

      final res = await _repository.submitMiddayCount(countsPayload);
      _middayResult = res;
      _isMiddaySubmitting = false;
      notifyListeners();
      return true;
    } catch (e) {
      if (kDebugMode) print('[Midday] Error: $e');
    }

    _isMiddaySubmitting = false;
    notifyListeners();
    return false;
  }

  Future<void> fetchYesterdayReviewRoutine() async {
    _isReviewLoading = true;
    notifyListeners();

    try {
      final res = await _repository.fetchYesterdayReview();
      _yesterdayReview = res;
    } catch (e) {
      if (kDebugMode) print('[YesterdayReview] Error: $e');
    } finally {
      _isReviewLoading = false;
      notifyListeners();
    }
  }

  void confirmStock() {
    _isConfirmed = true;
    notifyListeners();
  }

  void resetStockCheck() {
    _isConfirmed = false;
    _submissionMessage = null;
    _submissionError = null;
    notifyListeners();
  }
}
