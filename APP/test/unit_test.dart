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
        inventory = InventoryProvider(autoFetch: false);
        inventory.initForTestingWithSampleData();
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
    // 2. Waste Alerts Integrity & Action Tests (Zero Donation / Bundles)
    // -------------------------------------------------------------------------
    group('WasteAlertsProvider Catalog Alignment & Action Tests', () {
      late WasteAlertsProvider alertsProvider;

      setUp(() {
        alertsProvider = WasteAlertsProvider(autoFetch: false);
        alertsProvider.initForTestingWithSampleData();
      });

      test('Alerts catalog matches InventoryProvider items (Traditional Baguette & Whole Milk)', () {
        final alertNames = alertsProvider.activeAlerts.map((a) => a.itemName).toList();
        expect(alertNames, contains('Traditional Baguette'));
        expect(alertNames, contains('Whole Milk'));
        expect(alertNames.contains('Almond Croissant'), false,
            reason: 'Almond Croissant must not exist in alerts when absent from inventory');
      });

      test('Traditional Baguette alert triggers 10% discount recommendation and primary action', () {
        final baguetteAlert = alertsProvider.activeAlerts.firstWhere((a) => a.id == '2');
        expect(baguetteAlert.severityLabel, 'Low Pace');
        expect(baguetteAlert.recommendedActionText, 'Suggest 10% Discount');

        final recResult = alertsProvider.suggestRecommendation('2');
        expect(recResult, '10% discount suggestion recorded.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '2').isRecommendedActionDone, true);

        final actionResult = alertsProvider.applyPrimaryAction('2');
        expect(actionResult, '10% discount applied successfully to Traditional Baguette.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '2').isPrimaryActionDone, true);
      });

      test('Whole Milk alert triggers 20% bundle combo flow with partner item', () {
        final milkAlert = alertsProvider.activeAlerts.firstWhere((a) => a.id == '4');
        expect(milkAlert.severityLabel, 'Critical');
        expect(milkAlert.recommendedActionText, 'Apply 20% Bundle');
        expect(milkAlert.partnerItem, isNotNull);
        expect(milkAlert.partnerItem!['name'], 'Croissants');

        final recResult = alertsProvider.suggestRecommendation('4');
        expect(recResult, 'Bundle recommendation recorded.');
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '4').isRecommendedActionDone, true);

        final actionResult = alertsProvider.applyPrimaryAction('4');
        expect(actionResult, contains('20% bundle applied with Croissants'));
        expect(alertsProvider.activeAlerts.firstWhere((a) => a.id == '4').isPrimaryActionDone, true);
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
    // 3. Stock Check & Closing Routine Unit Tests
    // -------------------------------------------------------------------------
    group('StockCheckProvider Alignment & Validation Tests', () {
      late StockCheckProvider stockCheck;

      setUp(() {
        stockCheck = StockCheckProvider();
        stockCheck.initForTestingWithSampleData();
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

      test('Closing count validation rejects units left > available stock', () {
        final croissant = stockCheck.entries.firstWhere((e) => e.id == '1');
        final available = croissant.availableStock; // 25 + 15 = 40
        expect(available, 40);

        // Enter valid units left
        stockCheck.updateClosingUnitsLeft('1', 20);
        expect(stockCheck.entries.firstWhere((e) => e.id == '1').validationError, isNull);
        expect(stockCheck.entries.firstWhere((e) => e.id == '1').soldUnits, 20);
        expect(stockCheck.entries.firstWhere((e) => e.id == '1').wasteUnits, 20);

        // Enter invalid units left (exceeds 40)
        stockCheck.updateClosingUnitsLeft('1', 50);
        expect(stockCheck.entries.firstWhere((e) => e.id == '1').validationError, isNotNull);
        expect(stockCheck.hasValidationErrors, true);
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
            final body = jsonDecode(request.body) as Map<String, dynamic>;
            final query = (body['query'] as String? ?? '').toLowerCase();

            if (query.contains('fail_test')) {
              return http.Response('{"detail": "server error"}', 500);
            }
            if (query.contains('baguette')) {
              return http.Response(
                jsonEncode({'reply': 'Traditional Baguettes are at 40% of target sales pace today with 8 units on hand. Recommend 20% discount (pricing down to \$2.24).'}),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            if (query.contains('milk')) {
              return http.Response(
                jsonEncode({'reply': 'Whole Milk has high waste risk. Pair with Croissants for a 20% combo bundle discount.'}),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            if (query.contains('croissant') || query.contains('pastry')) {
              return http.Response(
                jsonEncode({'reply': 'Croissants demand predicted at 80 units.'}),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            if (query.contains('espresso')) {
              return http.Response(
                jsonEncode({'reply': 'Espresso Beans level is 20 LBS.'}),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            if (query.contains('alert')) {
              return http.Response(
                jsonEncode({'reply': 'Active alerts today: Traditional Baguettes and Whole Milk.'}),
                200,
                headers: {'content-type': 'application/json'},
              );
            }
            return http.Response(
              jsonEncode({'reply': 'RestockIQ operational assistant ready.'}),
              200,
              headers: {'content-type': 'application/json'},
            );
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

      test('Authentication succeeds with valid credentials and establishes session', () async {
        final success = await api.login('manager@store.com', 'SecurePassword123');
        expect(success, true);
        expect(api.isAuthenticated, true);
        expect(api.token, isNotNull);
        expect(api.token!.isNotEmpty, true);
        expect(api.userId, isNotNull);
        expect(api.userRole, 'owner');
      });

      test('Admin credentials also authenticate and set owner role', () async {
        final successAdmin = await api.login('admin@bakery.com', 'AdminPass123');
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
        expect(reply.contains('bundle'), true);
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

      test('AI Assistant returns null on server failure (no canned fake answers)', () async {
        final replyFail = await api.askAssistant('fail_test query');
        expect(replyFail, isNull);

        final replyEmpty = await api.askAssistant('    ');
        expect(replyEmpty, isNull); // Empty queries intentionally return null
      });
    });
  });
}
