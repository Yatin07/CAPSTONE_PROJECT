import 'package:flutter/material.dart';
import '../models/waste_alert.dart';
import '../services/api_service.dart';

class WasteAlertsProvider extends ChangeNotifier {
  final List<WasteAlert> _alerts = [
    WasteAlert(
      id: '1',
      itemName: 'Almond Croissant',
      salesText: '40% of expected sales so far\ntoday',
      progress: 0.40,
      severityLabel: 'Low Pace',
      severityColor: const Color(0xFFB91C1C),
      recommendedActionText: 'Suggest 20% Discount',
      recommendedActionIcon: Icons.local_offer_outlined,
      recommendedActionColor: const Color(0xFF8B1E22),
      recommendedDoneText: 'Discount Suggested',
      primaryActionText: 'Apply Discount',
      primaryDoneText: 'Discount Applied',
      layoutStyle: WasteAlertCardLayoutStyle.stacked,
      foodType: 'croissant',
    ),
    WasteAlert(
      id: '2',
      itemName: 'Spinach Feta\nQuiche',
      salesText: '25% of expected sales so far\ntoday',
      progress: 0.25,
      severityLabel: 'Critical',
      severityColor: const Color(0xFFD97706),
      recommendedActionText: 'Flag for Donation',
      recommendedActionIcon: Icons.volunteer_activism_outlined,
      recommendedActionColor: const Color(0xFFFFB702),
      recommendedDoneText: 'Flagged for Donation',
      primaryActionText: 'Flag Item',
      primaryDoneText: 'Item Flagged',
      layoutStyle: WasteAlertCardLayoutStyle.sideBySide,
      foodType: 'quiche',
    ),
  ];

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  List<WasteAlert> get activeAlerts =>
      _alerts.where((alert) => !alert.isDismissed).toList();

  List<WasteAlert> get allAlerts => List.unmodifiable(_alerts);

  WasteAlertsProvider() {
    fetchCloudWasteAlerts();
  }

  Future<void> fetchCloudWasteAlerts() async {
    _isLoading = true;
    notifyListeners();

    try {
      final cloudAlerts = await ApiService.instance.fetchWasteAlerts();
      if (cloudAlerts != null && cloudAlerts.isNotEmpty) {
        _alerts.clear();
        _alerts.addAll(cloudAlerts);
      }
    } catch (_) {
      // Graceful fallback to initial alerts
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

      // Sync donation flag to Atlas
      ApiService.instance.flagDonation(id);

      if (alert.recommendedActionText.toLowerCase().contains('donation')) {
        return 'Item flagged for charity donation.';
      } else {
        return 'Discount suggestion recorded.';
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

      // Sync 20% discount to Atlas
      ApiService.instance.applyDiscount(id);

      return '20% discount applied successfully to ${alert.itemName}.';
    }
    return '';
  }

  void dismissAlert(String id) {
    final index = _alerts.indexWhere((a) => a.id == id);
    if (index != -1) {
      _alerts[index] = _alerts[index].copyWith(isDismissed: true);
      notifyListeners();

      // Sync dismiss to Atlas
      ApiService.instance.dismissAlert(id);
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
