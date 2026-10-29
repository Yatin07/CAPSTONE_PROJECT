import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';
import 'package:app/models/inventory_item.dart';
import 'package:app/providers/inventory_provider.dart';
import 'package:app/providers/stock_check_provider.dart';
import 'package:app/providers/waste_alerts_provider.dart';
import 'package:app/screens/dashboard_screen.dart';
import 'package:app/screens/inventory_checkin_screen.dart';
import 'package:app/screens/item_detail_forecast_screen.dart';
import 'package:app/screens/item_setup_screen.dart';
import 'package:app/screens/login_screen.dart';
import 'package:app/screens/settings_screen.dart';
import 'package:app/screens/tour_screen.dart';
import 'package:app/screens/waste_alerts_screen.dart';
import 'package:app/services/api_service.dart';
import 'package:app/widgets/ai_briefing_card.dart';

void main() {
  group('RestockIQ App Tests', () {
    setUp(() {
      ApiService.resetClient();
      ApiService.setMockClient(MockClient((request) async {
        if (request.url.path.endsWith('/me')) {
          return http.Response(
            jsonEncode({
              'id': 'test_user',
              'name': 'Store Owner',
              'email': 'owner@test.com',
              'role': 'owner',
              'store_name': 'Corner Crumb Bakery',
              'timezone': 'Asia/Kolkata',
              'opening_hour': 8.0,
              'closing_hour': 20.0,
              'currency': '₹',
              'onboarding_completed': true,
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/forecasts/today')) {
          return http.Response(
            jsonEncode({
              'source': 'test',
              'summary': 'Test forecast summary',
              'items': [],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/briefing/today')) {
          return http.Response(
            jsonEncode({
              'source': 'test',
              'executive_summary': 'Test operational briefing',
              'actions': ['Sample action'],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/review/yesterday')) {
          return http.Response(
            jsonEncode({
              'status': 'success',
              'date': 'yesterday',
              'items': [
                {
                  'itemId': '1',
                  'itemName': 'Croissants',
                  'category': 'Bakery',
                  'status': 'completed',
                  'sellThroughPct': 92,
                  'label': 'High',
                  'availableStock': 80,
                  'soldUnits': 74,
                },
              ],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        throw StateError('BLOCKED: Real network call attempted during automated test: ${request.url}');
      }));
    });

    tearDown(() {
      ApiService.resetClient();
    });

    // -------------------------------------------------------------------------
    // Guard Test: No Network in Tests
    // -------------------------------------------------------------------------
    test('Guard test: Fails on any real network call during test runs', () async {
      final guardClient = MockClient((request) async {
        throw StateError('BLOCKED: Real network call attempted during automated test: ${request.url}');
      });
      ApiService.instance.client = guardClient;

      expect(
        () => ApiService.instance.client.get(Uri.parse('https://restockiq-backend.onrender.com/api/v1/health')),
        throwsA(isA<StateError>().having(
          (e) => e.message,
          'message',
          contains('BLOCKED: Real network call attempted during automated test'),
        )),
      );
    });

    testWidgets('Login screen loads successfully smoke test', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
          ],
          child: const MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      expect(find.text('Welcome Back'), findsOneWidget);
      expect(find.text('Email Address'), findsOneWidget);
      expect(find.text('Password'), findsOneWidget);
    });

    test('WasteAlertsProvider initial state and actions', () {
      final provider = WasteAlertsProvider(autoFetch: false);
      provider.initForTestingWithSampleData();

      expect(provider.activeAlerts.length, 2);
      expect(provider.activeAlerts[0].itemName, 'Traditional Baguette');
      expect(provider.activeAlerts[1].itemName, 'Whole Milk');

      final msg1 = provider.suggestRecommendation('2');
      expect(msg1, '10% discount suggestion recorded.');
      expect(provider.activeAlerts[0].isRecommendedActionDone, true);

      final msg2 = provider.applyPrimaryAction('2');
      expect(msg2, '10% discount applied successfully to Traditional Baguette.');
      expect(provider.activeAlerts[0].isPrimaryActionDone, true);

      provider.dismissAlert('2');
      expect(provider.activeAlerts.length, 1);
      expect(provider.activeAlerts[0].itemName, 'Whole Milk');

      provider.dismissAlert('4');
      expect(provider.activeAlerts.isEmpty, true);

      provider.resetAlerts();
      expect(provider.activeAlerts.length, 2);
    });

    testWidgets('WasteAlertsScreen renders alerts and interactions', (WidgetTester tester) async {
      final wasteProvider = WasteAlertsProvider(autoFetch: false);
      wasteProvider.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider.value(value: wasteProvider),
          ],
          child: const MaterialApp(
            home: WasteAlertsScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('RestockIQ'), findsOneWidget);
      expect(find.text('Items Needing\nAttention'), findsOneWidget);
      expect(find.text('Traditional Baguette'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);
      expect(find.text('Suggest 10% Discount'), findsOneWidget);
      expect(find.text('Apply Discount'), findsOneWidget);
      expect(find.text('Apply 20% Bundle'), findsOneWidget);
      expect(find.text('Dismiss'), findsNWidgets(2));

      // Tap Suggest 10% Discount
      final suggestBtn = find.text('Suggest 10% Discount');
      await tester.ensureVisible(suggestBtn);
      await tester.tap(suggestBtn);
      await tester.pumpAndSettle();
      expect(find.text('Discount Suggested'), findsOneWidget);

      // Tap Apply Discount
      final applyBtn = find.text('Apply Discount');
      await tester.ensureVisible(applyBtn);
      await tester.tap(applyBtn);
      await tester.pumpAndSettle();
      expect(find.text('Discount Applied'), findsOneWidget);

      // Dismiss Card 1 (Traditional Baguette)
      wasteProvider.dismissAlert('2');
      await tester.pumpAndSettle();
      expect(find.text('Traditional Baguette'), findsNothing);
      expect(find.text('Whole Milk'), findsOneWidget);

      // Dismiss Card 2 (Whole Milk)
      wasteProvider.dismissAlert('4');
      await tester.pumpAndSettle();
      expect(find.text('No waste alerts'), findsOneWidget);
      expect(find.text('All items are currently performing well.'), findsOneWidget);
    });

    test('InventoryProvider initial state and mutations', () {
      final provider = InventoryProvider(autoFetch: false);
      provider.initForTestingWithSampleData();

      expect(provider.itemCount, 5);
      expect(provider.items.first.name, 'Croissants');
      expect(provider.items.first.isPerishable, true);

      provider.addItem(
        name: 'Blueberry Muffin',
        category: 'Bakery',
        unit: 'Units',
        currentStock: 10,
        isPerishable: true,
      );

      expect(provider.itemCount, 6);
      expect(provider.items.last.name, 'Blueberry Muffin');
      expect(provider.items.last.isPerishable, true);

      final addedId = provider.items.last.id;
      provider.updateItem(
        id: addedId,
        name: 'Blueberry Muffin Large',
        category: 'Bakery',
        unit: 'Units',
        currentStock: 15,
        isPerishable: true,
      );

      expect(provider.items.last.name, 'Blueberry Muffin Large');
      expect(provider.items.last.currentStock, 15);

      provider.deleteItem(addedId);
      expect(provider.itemCount, 5);
    });

    test('StockCheckProvider initial state and mutations', () {
      final provider = StockCheckProvider();
      provider.initForTestingWithSampleData();

      expect(provider.entries.length, 5);

      final croissants = provider.entries[0];
      expect(croissants.name, 'Croissants');
      expect(croissants.actualQuantity, 30);
      expect(croissants.isPerishable, true);

      final beans = provider.entries[4];
      expect(beans.name, 'Espresso Beans');
      expect(beans.actualQuantity, 20);
      expect(beans.isPerishable, false);

      provider.updateQuantity(beans.id, 22);
      final updatedBeans = provider.entries[4];
      expect(updatedBeans.actualQuantity, 22);
      expect(updatedBeans.isManualOverride, true);

      expect(provider.isConfirmed, false);
      provider.confirmStock();
      expect(provider.isConfirmed, true);
    });

    test('Restock Qty formula logic tests', () {
      int calculateRestock(int predicted, int safety, int current) {
        return max(0, predicted + safety - current);
      }

      expect(calculateRestock(50, 5, 10), 45);
      expect(calculateRestock(15, 3, 6), 12);
      expect(calculateRestock(10, 2, 4), 8);
      expect(calculateRestock(10, 5, 20), 0);
    });

    testWidgets('ItemSetupScreen renders items and form controls', (WidgetTester tester) async {
      final inv = InventoryProvider(autoFetch: false);
      inv.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inv),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: ItemSetupScreen(),
          ),
        ),
      );

      expect(find.text('Your Menu Items'), findsOneWidget);
      expect(find.text('Add New Item'), findsOneWidget);
      expect(find.text('Highly Perishable?'), findsOneWidget);
      expect(find.text('Croissants'), findsOneWidget);
      expect(find.text('Espresso Beans'), findsOneWidget);
      expect(find.text('Save & Continue →'), findsOneWidget);
    });

    testWidgets('DashboardScreen renders header, LIVE badge, and forecast cards', (WidgetTester tester) async {
      final inv = InventoryProvider(autoFetch: false);
      inv.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inv),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      expect(find.text('RestockIQ'), findsOneWidget);
      expect(find.text('LIVE'), findsOneWidget);
      expect(find.text("Today's Forecast"), findsOneWidget);
      expect(find.text('Croissants'), findsOneWidget);
      expect(find.text('Espresso Beans'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // Required Test: Empty Store Dashboard Rendering
    // -------------------------------------------------------------------------
    testWidgets('Empty store dashboard rendering shows empty state card and action button', (WidgetTester tester) async {
      final emptyInventory = InventoryProvider(autoFetch: false);

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: emptyInventory),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      expect(find.text('Catalog is empty'), findsOneWidget);
      expect(find.text('Add Menu Item'), findsOneWidget);
      expect(find.text('Add your first item to begin generating AI demand forecasts and replenishment orders.'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // Required Test: Tour Flow with SampleRepository
    // -------------------------------------------------------------------------
    testWidgets('Tour flow with SampleRepository renders DEMO TOUR badge and walkthrough steps', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
          ],
          child: const MaterialApp(
            home: TourScreen(isReplay: false),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('DEMO TOUR'), findsOneWidget);
      expect(find.text('Interactive Tour'), findsOneWidget);
      expect(find.text('Intelligent Daily Forecasts'), findsOneWidget);
      expect(find.text('PREDICTIVE REPLENISHMENT'), findsOneWidget);

      // Tap Next to advance
      final nextBtn = find.text('Next');
      expect(nextBtn, findsOneWidget);
      await tester.tap(nextBtn);
      await tester.pumpAndSettle();

      expect(find.text('Proactive Waste Mitigation'), findsOneWidget);
      expect(find.text('SMART BUNDLE ACTIONS'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // Required Test: Closing Count Validation
    // -------------------------------------------------------------------------
    testWidgets('Closing count validation rejects units left > available stock', (WidgetTester tester) async {
      final stockProvider = StockCheckProvider();
      stockProvider.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider.value(value: stockProvider),
          ],
          child: const MaterialApp(
            home: InventoryCheckInScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Daily Inventory Routines'), findsOneWidget);
      expect(find.text('Closing Count'), findsOneWidget);

      // Find first units left input field (Croissants, available: 40)
      final textFields = find.byType(TextField);
      expect(textFields, findsWidgets);

      // Enter 50 (> 40 available)
      await tester.enterText(textFields.first, '50');
      await tester.pumpAndSettle();

      // Check validation error appears
      expect(find.textContaining('cannot exceed available'), findsOneWidget);
      expect(stockProvider.hasValidationErrors, true);
    });

    testWidgets('ItemDetailForecastScreen renders item detail and formula', (WidgetTester tester) async {
      final item = InventoryItem(
        id: '3',
        name: 'Sourdough Loaf',
        category: 'Bakery',
        unit: 'Units',
        currentStock: 8,
        isPerishable: true,
        predictedDemand: 42,
        safetyStock: 6,
        updatedAt: DateTime.now(),
      );

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: MaterialApp(
            home: ItemDetailForecastScreen(item: item),
          ),
        ),
      );

      expect(find.text('Sourdough Loaf'), findsOneWidget);
      expect(find.text('Predicted for Tomorrow'), findsOneWidget);
      expect(find.text('42 units'), findsOneWidget);
      expect(find.text('AI Assistant'), findsOneWidget);
      expect(find.text('Restock Formula'), findsOneWidget);
      expect(find.text('40'), findsOneWidget);
      expect(find.text('✓ Restock Confirmed'), findsOneWidget);
      expect(find.text('Sales vs Prediction'), findsOneWidget);
    });

    testWidgets('SettingsScreen renders profile and options', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
          ],
          child: const MaterialApp(
            home: SettingsScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Settings'), findsNWidgets(2));
      expect(find.text('Manage Inventory Items'), findsOneWidget);
      expect(find.text('Store Configuration'), findsOneWidget);
      expect(find.text('Replay Tour'), findsOneWidget);
      expect(find.text('Log Out'), findsOneWidget);
    });

    testWidgets('LoginScreen displays Waking up server... when cold start flag is active', (WidgetTester tester) async {
      ApiService.isWakingUpServer.value = true;
      ApiService.serverStatusMessage.value = 'Waking up server...';

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
          ],
          child: const MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      expect(find.text('Waking up server...'), findsOneWidget);

      ApiService.isWakingUpServer.value = false;
      ApiService.serverStatusMessage.value = null;
      await tester.pump();
      expect(find.text('Waking up server...'), findsNothing);
    });

    testWidgets('AiBriefingCard displays Fallback Mode label when briefing source is fallback', (WidgetTester tester) async {
      final inventoryProvider = InventoryProvider(autoFetch: false);
      inventoryProvider.setAiBriefingForTest({
        'source': 'fallback',
        'provider': 'deterministic-fallback',
        'executive_summary': 'Fallback summary for testing',
        'actions': ['Action 1', 'Action 2'],
      });

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inventoryProvider),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: SingleChildScrollView(
                child: AiBriefingCard(),
              ),
            ),
          ),
        ),
      );

      expect(find.text('Fallback Mode'), findsOneWidget);
    });
  });
}
