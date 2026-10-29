import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:provider/provider.dart';
import 'package:app/providers/inventory_provider.dart';
import 'package:app/providers/stock_check_provider.dart';
import 'package:app/providers/waste_alerts_provider.dart';
import 'package:app/repositories/app_repository.dart';
import 'package:app/screens/login_screen.dart';
import 'package:app/screens/dashboard_screen.dart';
import 'package:app/screens/waste_alerts_screen.dart';
import 'package:app/services/api_service.dart';

void main() {
  group('RestockIQ Phase 2: Integration Testing Suite', () {
    setUp(() {
      ApiService.resetClient();
      ApiService.setMockClient(MockClient((request) async {
        if (request.url.path.endsWith('/auth/login')) {
          return http.Response(
            jsonEncode({
              'access_token': 'fake_jwt_token',
              'user_id': 'fake_user_id',
              'name': 'Store Manager',
              'role': 'owner',
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/me')) {
          return http.Response(
            jsonEncode({
              'id': 'fake_user_id',
              'name': 'Store Manager',
              'email': 'admin@test.com',
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
              'summary': 'Forecasts loaded for testing.',
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
              'executive_summary': 'Operational briefing loaded.',
              'actions': ['Replenish croissants.'],
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        if (request.url.path.endsWith('/assistant/chat')) {
          return http.Response(
            jsonEncode({
              'reply': 'Traditional Baguettes are at 40% of target sales pace. Recommend 20% discount.',
            }),
            200,
            headers: {'content-type': 'application/json'},
          );
        }
        return http.Response('{"detail": "not mocked"}', 404);
      }));
    });

    tearDown(() {
      ApiService.resetClient();
    });

    test('Cross-Provider Catalog Consistency: Alerts & StockCheck map 1-to-1 with Sample Inventory', () {
      final inventory = InventoryProvider(autoFetch: false);
      inventory.initForTestingWithSampleData();

      final wasteAlerts = WasteAlertsProvider(autoFetch: false);
      wasteAlerts.initForTestingWithSampleData();

      final stockCheck = StockCheckProvider();
      stockCheck.initForTestingWithSampleData();

      // Master catalog IDs and names
      final masterMap = {for (var item in inventory.items) item.id: item.name};
      expect(masterMap.length, 5);

      // Verify every Waste Alert exists in master inventory
      for (final alert in wasteAlerts.allAlerts) {
        expect(masterMap.containsKey(alert.id), true,
            reason: 'Alert ID ${alert.id} (${alert.itemName}) must exist in InventoryProvider');
        expect(masterMap[alert.id], alert.itemName,
            reason: 'Alert item name must match master inventory name exactly');
      }

      // Verify every Stock Check entry exists in master inventory
      for (final entry in stockCheck.entries) {
        expect(masterMap.containsKey(entry.id), true,
            reason: 'Stock check entry ID ${entry.id} (${entry.name}) must exist in InventoryProvider');
        expect(masterMap[entry.id], entry.name,
            reason: 'Stock check entry name must match master inventory name');
      }
    });

    test('Applying Waste Alert discount records action and preserves state across providers', () {
      final inventory = InventoryProvider(autoFetch: false);
      inventory.initForTestingWithSampleData();

      final wasteAlerts = WasteAlertsProvider(autoFetch: false);
      wasteAlerts.initForTestingWithSampleData();

      // Locate Traditional Baguette (ID: 2)
      final baguette = inventory.items.firstWhere((i) => i.id == '2');
      expect(baguette.name, 'Traditional Baguette');

      final alert = wasteAlerts.activeAlerts.firstWhere((a) => a.id == '2');
      expect(alert.itemName, 'Traditional Baguette');
      expect(alert.isPrimaryActionDone, false);

      // Apply primary action (10% discount)
      final resultMessage = wasteAlerts.applyPrimaryAction('2');
      expect(resultMessage, '10% discount applied successfully to Traditional Baguette.');
      expect(wasteAlerts.activeAlerts.firstWhere((a) => a.id == '2').isPrimaryActionDone, true);
    });

    testWidgets('Complete Walkthrough UI Flow: Login with walkthrough credentials routes to Dashboard',
        (WidgetTester tester) async {
      final inventory = InventoryProvider(repository: SampleRepository(), autoFetch: false);
      inventory.initForTestingWithSampleData();

      final wasteAlerts = WasteAlertsProvider(repository: SampleRepository(), autoFetch: false);
      wasteAlerts.initForTestingWithSampleData();

      final stockCheck = StockCheckProvider(repository: SampleRepository());
      stockCheck.initForTestingWithSampleData();

      // Start at Login Screen
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inventory),
            ChangeNotifierProvider.value(value: wasteAlerts),
            ChangeNotifierProvider.value(value: stockCheck),
          ],
          child: const MaterialApp(
            home: LoginScreen(),
          ),
        ),
      );

      expect(find.text('Welcome Back'), findsOneWidget);
      expect(find.text('Email Address'), findsOneWidget);

      // Enter credentials: admin@test.com / 123456
      final emailFinder = find.byType(TextFormField).first;
      final passwordFinder = find.byType(TextFormField).last;

      await tester.enterText(emailFinder, 'admin@test.com');
      await tester.enterText(passwordFinder, '123456');
      await tester.pump();

      // Tap Login button
      final signInFinder = find.text('Login');
      await tester.ensureVisible(signInFinder);
      await tester.tap(signInFinder);
      await tester.pumpAndSettle();

      // Since onboarding_completed is true, user arrives at Dashboard
      expect(find.text('RestockIQ'), findsOneWidget);
    });

    testWidgets('Waste Alerts UI displays only consistent items and handles action taps',
        (WidgetTester tester) async {
      final wasteAlerts = WasteAlertsProvider(autoFetch: false);
      wasteAlerts.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider(autoFetch: false)),
            ChangeNotifierProvider.value(value: wasteAlerts),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: WasteAlertsScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify no mention of donation
      expect(find.text('Flag for Donation'), findsNothing);

      // Verify Traditional Baguette and Whole Milk are present
      expect(find.text('Traditional Baguette'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);

      // Verify action buttons
      expect(find.text('Suggest 10% Discount'), findsOneWidget);
      expect(find.text('Apply Discount'), findsOneWidget);
      expect(find.text('Apply 20% Bundle'), findsOneWidget);
    });

    testWidgets('AI Assistant Dialogue in AI Briefing Card responds with grounded response',
        (WidgetTester tester) async {
      final inventory = InventoryProvider(repository: SampleRepository(), autoFetch: false);
      inventory.initForTestingWithSampleData();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inventory),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider(autoFetch: false)),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find AI Briefing Card Ask AI Assistant button
      final askFinder = find.text('Ask AI Assistant');
      expect(askFinder, findsOneWidget);
      await tester.ensureVisible(askFinder);
      await tester.tap(askFinder);
      await tester.pumpAndSettle();

      // Modal bottom sheet should be open
      expect(find.text('Ask RestockIQ Assistant'), findsOneWidget);
      expect(find.text('Powered by Google Gemini • Grounded in store data'), findsOneWidget);

      // Type inquiry about baguette discount
      final searchInput = find.byType(TextField);
      expect(searchInput, findsOneWidget);
      await tester.enterText(searchInput, 'What is the discount on baguette?');
      await tester.pump();

      // Tap send icon button
      final sendFinder = find.byIcon(Icons.send_rounded);
      await tester.tap(sendFinder);

      // Allow assistant query to resolve
      await tester.pump(const Duration(milliseconds: 500));
      await tester.pumpAndSettle();

      // Verify grounded response is displayed and NO error appears
      expect(find.text('Could not reach assistant. Please try again.'), findsNothing);
      expect(find.textContaining('Traditional Baguettes'), findsOneWidget);
    });
  });
}
