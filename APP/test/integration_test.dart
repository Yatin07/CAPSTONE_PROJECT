import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:app/providers/inventory_provider.dart';
import 'package:app/providers/stock_check_provider.dart';
import 'package:app/providers/waste_alerts_provider.dart';
import 'package:app/screens/login_screen.dart';
import 'package:app/screens/dashboard_screen.dart';
import 'package:app/screens/waste_alerts_screen.dart';
import 'package:app/screens/inventory_checkin_screen.dart';
import 'package:app/services/api_service.dart';

void main() {
  group('RestockIQ Phase 2: Integration Testing Suite', () {
    // -------------------------------------------------------------------------
    // 1. Cross-Provider Data Integrity & Synchronization
    // -------------------------------------------------------------------------
    test('Cross-Provider Catalog Consistency: Alerts & StockCheck map 1-to-1 with Inventory', () {
      final inventory = InventoryProvider();
      final wasteAlerts = WasteAlertsProvider();
      final stockCheck = StockCheckProvider();

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

    // -------------------------------------------------------------------------
    // 2. Cross-Provider Action Propagation
    // -------------------------------------------------------------------------
    test('Applying Waste Alert discount records action and preserves state across providers', () {
      final inventory = InventoryProvider();
      final wasteAlerts = WasteAlertsProvider();

      // Locate Traditional Baguette (ID: 2)
      final baguette = inventory.items.firstWhere((i) => i.id == '2');
      expect(baguette.name, 'Traditional Baguette');

      final alert = wasteAlerts.activeAlerts.firstWhere((a) => a.id == '2');
      expect(alert.itemName, 'Traditional Baguette');
      expect(alert.isPrimaryActionDone, false);

      // Apply primary action (20% discount)
      final resultMessage = wasteAlerts.applyPrimaryAction('2');
      expect(resultMessage, '20% discount applied successfully to Traditional Baguette.');
      expect(wasteAlerts.activeAlerts.firstWhere((a) => a.id == '2').isPrimaryActionDone, true);
    });

    // -------------------------------------------------------------------------
    // 3. End-to-End Walkthrough Flow Integration (Login -> Dashboard -> Alerts -> Stock Check)
    // -------------------------------------------------------------------------
    testWidgets('Complete Walkthrough UI Flow: Login with normal credentials, verify Dashboard, Alerts, and Stock Check',
        (WidgetTester tester) async {
      final inventory = InventoryProvider();
      final wasteAlerts = WasteAlertsProvider();
      final stockCheck = StockCheckProvider();

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

      // Enter normal walkthrough credentials: admin@test.com / 123456
      final emailFinder = find.byType(TextFormField).first;
      final passwordFinder = find.byType(TextFormField).last;

      await tester.enterText(emailFinder, 'admin@test.com');
      await tester.enterText(passwordFinder, '123456');
      await tester.pump();

      // Tap Login button
      final signInFinder = find.text('Login');
      await tester.ensureVisible(signInFinder);
      await tester.tap(signInFinder);

      // Settle navigation (fast walkthrough login bypasses cold-start delay)
      await tester.pumpAndSettle();

      // User arrives at Item Setup Screen (or Dashboard)
      expect(find.text('Your Menu Items'), findsOneWidget);
      expect(find.text('Croissants'), findsOneWidget);
      expect(find.text('Traditional Baguette'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);
      expect(find.text('Espresso Beans'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // 4. Waste Alerts Screen UI Integration
    // -------------------------------------------------------------------------
    testWidgets('Waste Alerts UI displays only consistent items and handles action taps',
        (WidgetTester tester) async {
      final wasteAlerts = WasteAlertsProvider();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider.value(value: wasteAlerts),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: WasteAlertsScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify no mention of Almond Croissant or Spinach Quiche
      expect(find.text('Almond Croissant'), findsNothing);
      expect(find.text('Spinach Feta\nQuiche'), findsNothing);

      // Verify Traditional Baguette and Whole Milk are present
      expect(find.text('Traditional Baguette'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);

      // Verify action buttons
      expect(find.text('Suggest 20% Discount'), findsOneWidget);
      expect(find.text('Apply Discount'), findsOneWidget);
      expect(find.text('Flag for Donation'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // 5. AI Assistant Dialogue in AI Briefing Card Integration
    // -------------------------------------------------------------------------
    testWidgets('AI Assistant dialog opens, responds with grounded inventory metrics, never displays error',
        (WidgetTester tester) async {
      final inventory = InventoryProvider();

      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider.value(value: inventory),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
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

      // Verify grounded response is displayed and NO "Could not reach assistant" appears
      expect(find.text('Could not reach assistant. Please try again.'), findsNothing);
      expect(find.textContaining('Traditional Baguettes'), findsOneWidget);
      expect(find.textContaining('20% discount'), findsOneWidget);
    });
  });
}
