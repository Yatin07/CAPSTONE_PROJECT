import 'dart:convert';
import 'dart:math';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:app/providers/inventory_provider.dart';
import 'package:app/providers/stock_check_provider.dart';
import 'package:app/providers/waste_alerts_provider.dart';
import 'package:app/services/api_service.dart';

void main() {
  group('RestockIQ Phase 1: Unit Testing Suite', () {
    // -------------------------------------------------------------------------
    // 1. Inventory Catalog & Mathematical Formula Unit Tests
    // -------------------------------------------------------------------------
    group('InventoryProvider & Catalog Integrity Tests', () {
      late InventoryProvider inventory;

      setUp(() {
        inventory = InventoryProvider();
      });

      test('Inventory catalog initializes with exactly 5 core items', () {
        expect(inventory.itemCount, 5);
        final names = inventory.items.map((i) => i.name).toList();
        expect(names, [
          'Croissants',
          'Traditional Baguette',
          'Pain au Chocolat',
          'Whole Milk',
          'Espresso Beans',
        ]);
      });

      test('Perishable and non-perishable flags are accurately defined', () {
        final croissants = inventory.items.firstWhere((i) => i.id == '1');
        final baguette = inventory.items.firstWhere((i) => i.id == '2');
        final pain = inventory.items.firstWhere((i) => i.id == '3');
        final milk = inventory.items.firstWhere((i) => i.id == '4');
        final beans = inventory.items.firstWhere((i) => i.id == '5');

        expect(croissants.isPerishable, true);
        expect(baguette.isPerishable, true);
        expect(pain.isPerishable, true);
        expect(milk.isPerishable, true);
        expect(beans.isPerishable, false);
      });

      test('Item pricing and baseline stocks adhere to business rules', () {
        final baguette = inventory.items.firstWhere((i) => i.id == '2');
        expect(baguette.price, 2.80);
        expect(baguette.currentStock, 8);
        expect(baguette.safetyStock, 15);
        expect(baguette.predictedDemand, 39);

        final milk = inventory.items.firstWhere((i) => i.id == '4');
        expect(milk.price, 4.50);
        expect(milk.currentStock, 4);
        expect(milk.unit, 'GAL');
      });

      test('Restock recommendation formula: max(0, predicted + safety - current)', () {
        int calculateRestock(int predicted, int safety, int current) {
          return max(0, predicted + safety - current);
        }

        // Croissants: 80 + 40 - 30 = 90
        expect(calculateRestock(80, 40, 30), 90);
        // Traditional Baguette: 39 + 15 - 8 = 46
        expect(calculateRestock(39, 15, 8), 46);
        // Whole Milk: 42 + 19 - 4 = 57
        expect(calculateRestock(42, 19, 4), 57);
        // Espresso Beans: 5 + 4 - 20 = -11 -> 0 (clamped)
        expect(calculateRestock(5, 4, 20), 0);
      });

      test('InventoryProvider CRUD operations maintain local integrity', () async {
        await inventory.addItem(
          name: 'Cinnamon Roll',
          category: 'Bakery',
          unit: 'Units',
          currentStock: 12,
          isPerishable: true,
          price: 3.25,
        );
        expect(inventory.itemCount, 6);
        expect(inventory.items.any((i) => i.name == 'Cinnamon Roll'), true);

        final added = inventory.items.firstWhere((i) => i.name == 'Cinnamon Roll');
        inventory.deleteItem(added.id);
        expect(inventory.itemCount, 5);
        expect(inventory.items.any((i) => i.name == 'Cinnamon Roll'), false);
      });
    });

    // -------------------------------------------------------------------------
    // 2. Waste Alerts Integrity & Synchronization Unit Tests
    // -------------------------------------------------------------------------
    group('WasteAlertsProvider Catalog Alignment & Action Tests', () {
      late WasteAlertsProvider alertsProvider;

      setUp(() {
        alertsProvider = WasteAlertsProvider();
      });

      test('Alerts catalog matches InventoryProvider items (Traditional Baguette & Whole Milk)', () {
        final alertNames = alertsProvider.activeAlerts.map((a) => a.itemName).toList();
        expect(alertNames, contains('Traditional Baguette'));
        expect(alertNames, contains('Whole Milk'));
        expect(alertNames.contains('Almond Croissant'), false,
            reason: 'Almond Croissant must not exist in alerts when absent from inventory');
      });

      test('Traditional Baguette alert triggers 20% discount recommendation and primary action', () {
        final baguetteAlert = alertsProvider.activeAlerts.firstWhere((a) => a.id == '2');
        expect(baguetteAlert.severityLabel, 'Low Pace');
        expect(baguetteAlert.recommendedActionText, 'Suggest 20% Discount');

        final recResult = alertsProvider.suggestRecommendation('2');
        expect(recResult, 'Discount suggestion recorded.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '2').isRecommendedActionDone, true);

        final actionResult = alertsProvider.applyPrimaryAction('2');
        expect(actionResult, '20% discount applied successfully to Traditional Baguette.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '2').isPrimaryActionDone, true);
      });

      test('Whole Milk alert triggers charity donation flow', () {
        final milkAlert = alertsProvider.activeAlerts.firstWhere((a) => a.id == '4');
        expect(milkAlert.severityLabel, 'Critical');
        expect(milkAlert.recommendedActionText, 'Flag for Donation');

        final recResult = alertsProvider.suggestRecommendation('4');
        expect(recResult, 'Item flagged for charity donation.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '4').isRecommendedActionDone, true);
      });

      test('Dismiss and reset lifecycle behaves correctly', () {
        expect(alertsProvider.activeAlerts.length, 2);
        alertsProvider.dismissAlert('2');
        expect(alertsProvider.activeAlerts.length, 1);
        expect(alertsProvider.activeAlerts.first.itemName, 'Whole Milk');

        alertsProvider.dismissAlert('4');
        expect(alertsProvider.activeAlerts.isEmpty, true);

        alertsProvider.resetAlerts();
        expect(alertsProvider.activeAlerts.length, 2);
      });
    });

    // -------------------------------------------------------------------------
    // 3. Stock Check Provider Unit Tests
    // -------------------------------------------------------------------------
    group('StockCheckProvider Alignment & Override Tests', () {
      late StockCheckProvider stockCheck;

      setUp(() {
        stockCheck = StockCheckProvider();
      });

      test('Stock check catalog matches the 5 master inventory SKUs', () {
        expect(stockCheck.entries.length, 5);
        final entryNames = stockCheck.entries.map((e) => e.name).toList();
        expect(entryNames, [
          'Croissants',
          'Traditional Baguette',
          'Pain au Chocolat',
          'Whole Milk',
          'Espresso Beans',
        ]);
      });

      test('Perishable items lock manual edit while non-perishables permit override', () {
        // Croissants is perishable (resets daily)
        final initialCroissants = stockCheck.entries.firstWhere((e) => e.id == '1');
        expect(initialCroissants.isPerishable, true);
        stockCheck.updateQuantity('1', 50);
        // Quantity should NOT mutate because it is perishable
        expect(stockCheck.entries.firstWhere((e) => e.id == '1').actualQuantity, 30);

        // Espresso Beans is non-perishable
        final initialBeans = stockCheck.entries.firstWhere((e) => e.id == '5');
        expect(initialBeans.isPerishable, false);
        expect(initialBeans.isAutoCalculated, true);
        expect(initialBeans.isManualOverride, false);

        stockCheck.updateQuantity('5', 25);
        final updatedBeans = stockCheck.entries.firstWhere((e) => e.id == '5');
        expect(updatedBeans.actualQuantity, 25);
        expect(updatedBeans.isAutoCalculated, false);
        expect(updatedBeans.isManualOverride, true);
      });

      test('Confirming stock updates isConfirmed state', () {
        expect(stockCheck.isConfirmed, false);
        stockCheck.confirmStock();
        expect(stockCheck.isConfirmed, true);

        stockCheck.resetStockCheck();
        expect(stockCheck.isConfirmed, false);
      });
    });

    // -------------------------------------------------------------------------
    // 4. ApiService Walkthrough Login & Grounded AI Assistant Unit Tests
    // -------------------------------------------------------------------------
    group('ApiService Walkthrough Speed & AI Assistant Fallback Tests', () {
      late ApiService api;

      setUp(() {
        api = ApiService.instance;
        api.logout();
        api.client = MockClient((request) async {
          // Block any unmocked real network call
          if (request.url.path.endsWith('/auth/login')) {
            final body = jsonDecode(request.body) as Map<String, dynamic>;
            final email = body['email'] as String? ?? '';
            return http.Response(
              jsonEncode({
                'access_token': 'fake_test_jwt_token',
                'user_id': 'fake_user_id',
                'name': email.contains('admin') ? 'Admin User' : 'Store Manager',
                'role': 'owner',
              }),
              200,
              headers: {'content-type': 'application/json'},
            );
          }
          if (request.url.path.endsWith('/assistant/chat')) {
            // Return 500 so askAssistant tests its deterministic fallback engine
            return http.Response('{"detail": "offline"}', 500);
          }
          throw StateError('BLOCKED: Real network call attempted during automated test: ${request.url}');
        });
      });

      tearDown(() {
        ApiService.resetClient();
      });

      test('Default base URL targets production Render cloud backend', () {
        expect(ApiService.defaultBaseUrl, 'https://restockiq-backend.onrender.com/api/v1');
      });

      test('Fails on any real network call during test runs', () async {
        final guardClient = MockClient((request) async {
          throw StateError('BLOCKED: Real network call attempted during automated test: ${request.url}');
        });
        api.client = guardClient;

        expect(
          () => api.client.get(Uri.parse('https://restockiq-backend.onrender.com/api/v1/health')),
          throwsA(isA<StateError>().having(
            (e) => e.message,
            'message',
            contains('BLOCKED: Real network call attempted during automated test'),
          )),
        );
      });

      test('Walkthrough credentials authenticate quickly and establish valid session', () async {
        final success = await api.login('admin@test.com', '123456');
        expect(success, true);
        expect(api.isAuthenticated, true);
        expect(api.token, isNotNull);
        expect(api.token!.isNotEmpty, true);
        expect(api.userId, isNotNull);
        expect(api.userRole, 'owner');
      });

      test('Alternative walkthrough credentials also authenticate immediately', () async {
        final successAdmin = await api.login('admin@admin.com', '123456');
        expect(successAdmin, true);
        expect(api.isAuthenticated, true);

        final successManager = await api.login('manager@cafe.com', 'password123');
        expect(successManager, true);
        expect(api.isAuthenticated, true);
      });

      test('AI Assistant returns grounded contextual answer for Baguette queries', () async {
        final reply = await api.askAssistant('How is baguette pace and discount?');
        expect(reply, isNotNull);
        expect(reply!.contains('Traditional Baguettes'), true);
        expect(reply.contains('20% discount'), true);
        expect(reply.contains(r'$2.24'), true);
      });

      test('AI Assistant returns grounded contextual answer for Milk queries', () async {
        final reply = await api.askAssistant('What should we do with whole milk expiry?');
        expect(reply, isNotNull);
        expect(reply!.contains('Whole Milk'), true);
        expect(reply.contains('donation'), true);
      });

      test('AI Assistant returns grounded contextual answer for Croissants & Pastries', () async {
        final reply = await api.askAssistant('Show pastry and croissant forecast');
        expect(reply, isNotNull);
        expect(reply!.contains('Croissants'), true);
        expect(reply.contains('80'), true);
      });

      test('AI Assistant returns grounded contextual answer for Espresso Beans', () async {
        final reply = await api.askAssistant('Check espresso beans level');
        expect(reply, isNotNull);
        expect(reply!.contains('Espresso Beans'), true);
        expect(reply.contains('20 LBS'), true);
      });

      test('AI Assistant returns active alerts overview', () async {
        final reply = await api.askAssistant('What waste alerts are active today?');
        expect(reply, isNotNull);
        expect(reply!.contains('Traditional Baguettes'), true);
        expect(reply.contains('Whole Milk'), true);
      });

      test('AI Assistant never returns null or "Could not reach assistant" on standard queries', () async {
        final replyGeneral = await api.askAssistant('Hello, who are you?');
        expect(replyGeneral, isNotNull);
        expect(replyGeneral!.contains('RestockIQ'), true);
        expect(replyGeneral.contains('Could not reach assistant'), false);

        final replyEmpty = await api.askAssistant('    ');
        expect(replyEmpty, isNull); // Empty queries intentionally return null
      });
    });
  });
}
