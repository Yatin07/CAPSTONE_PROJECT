import 'package:flutter/material.dart';
import '../models/waste_alert.dart';
import '../repositories/app_repository.dart';
import '../services/api_service.dart';

class WasteAlertsProvider extends ChangeNotifier {
  AppRepository _repository;
  final List<WasteAlert> _alerts = [];

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _storeStatus;
  String? _storeMessage;
  String? get storeStatus => _storeStatus;
  String? get storeMessage => _storeMessage;

  List<WasteAlert> get activeAlerts =>
      _alerts.where((alert) => !alert.isDismissed).toList();

  List<WasteAlert> get allAlerts => List.unmodifiable(_alerts);

  WasteAlertsProvider({AppRepository? repository, bool autoFetch = true})
      : _repository = repository ?? LiveRepository() {
    if (autoFetch) {
      fetchCloudWasteAlerts();
    }
  }

  void setRepository(AppRepository newRepo) {
    _repository = newRepo;
    _alerts.clear();
    notifyListeners();
    fetchCloudWasteAlerts();
  }

  void initForTestingWithSampleData() {
    _alerts.clear();
    _alerts.addAll([
      const WasteAlert(
        id: '2',
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
        id: '4',
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
          'id': '1',
          'name': 'Croissants',
          'category': 'Bakery',
          'price': 3.50,
          'comboOriginalPrice': 8.00,
          'bundlePrice': 6.40,
          'discountPct': 20,
        },
        bundleDiscountPct: 20,
      ),
    ]);
    notifyListeners();
  }

  Future<void> fetchCloudWasteAlerts() async {
    _isLoading = true;
    notifyListeners();

    try {
      final cloudAlerts = await _repository.fetchWasteAlerts();
      _storeStatus = ApiService.instance.lastStoreStatus;
      _storeMessage = ApiService.instance.lastStoreMessage;
      _alerts.clear();
      _alerts.addAll(cloudAlerts);
    } catch (_) {
      // Graceful fallback: maintain current state
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  String suggestRecommendation(String id) {
    final index = _alerts.indexWhere((a) => a.id == id);
    if (index != -1) {
      final alert = _alerts[index];
      _alerts[index] = alert.copyWith(isRecommendedActionDone: true);
      notifyListeners();

      if (alert.partnerItem != null) {
        _repository.applyBundle(
          id,
          partnerId: alert.partnerItem?['id']?.toString(),
          discountPct: 0.20,
        );
        return 'Bundle recommendation recorded.';
      } else {
        _repository.applyDiscount(id, discountPct: 0.10);
        return '10% discount suggestion recorded.';
      }
    }
    return '';
  }

  String applyPrimaryAction(String id) {
    final index = _alerts.indexWhere((a) => a.id == id);
    if (index != -1) {
      final alert = _alerts[index];
      _alerts[index] = alert.copyWith(isPrimaryActionDone: true);
      notifyListeners();

      if (alert.partnerItem != null) {
        _repository.applyBundle(
          id,
          partnerId: alert.partnerItem?['id']?.toString(),
          discountPct: 0.20,
        );
        return '20% bundle applied with ${alert.partnerItem?['name'] ?? 'partner item'}.';
      } else {
        _repository.applyDiscount(id, discountPct: 0.10);
        return '10% discount applied successfully to ${alert.itemName}.';
      }
    }
    return '';
  }

  void dismissAlert(String id) {
    final index = _alerts.indexWhere((a) => a.id == id);
    if (index != -1) {
      _alerts[index] = _alerts[index].copyWith(isDismissed: true);
      notifyListeners();

      _repository.dismissAlert(id);
    }
  }

  void resetAlerts() {
    for (int i = 0; i < _alerts.length; i++) {
      _alerts[i] = _alerts[i].copyWith(
        isRecommendedActionDone: false,
        isPrimaryActionDone: false,
        isDismissed: false,
      );
    }
    notifyListeners();
  }
}
