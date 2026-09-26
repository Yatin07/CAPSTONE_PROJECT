import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
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
import 'package:app/screens/waste_alerts_screen.dart';

void main() {
  group('RestockIQ App Tests', () {
    testWidgets('Login screen loads successfully smoke test', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
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
      final provider = WasteAlertsProvider();

      expect(provider.activeAlerts.length, 2);
      expect(provider.activeAlerts[0].itemName, 'Almond Croissant');
      expect(provider.activeAlerts[1].itemName, 'Spinach Feta\nQuiche');

      final msg1 = provider.suggestRecommendation('1');
      expect(msg1, 'Discount suggested successfully.');
      expect(provider.activeAlerts[0].isRecommendedActionDone, true);

      final msg2 = provider.applyPrimaryAction('1');
      expect(msg2, 'Discount applied successfully.');
      expect(provider.activeAlerts[0].isPrimaryActionDone, true);

      provider.dismissAlert('1');
      expect(provider.activeAlerts.length, 1);
      expect(provider.activeAlerts[0].itemName, 'Spinach Feta\nQuiche');

      provider.dismissAlert('2');
      expect(provider.activeAlerts.isEmpty, true);

      provider.resetAlerts();
      expect(provider.activeAlerts.length, 2);
    });

    testWidgets('WasteAlertsScreen renders alerts and interactions', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
          ],
          child: const MaterialApp(
            home: WasteAlertsScreen(),
          ),
        ),
      );

      expect(find.text('RestockIQ'), findsOneWidget);
      expect(find.text('Items Needing\nAttention'), findsOneWidget);
      expect(find.text('Almond Croissant'), findsOneWidget);
      expect(find.text('Spinach Feta\nQuiche'), findsOneWidget);
      expect(find.text('Suggest 20% Discount'), findsOneWidget);
      expect(find.text('Apply Discount'), findsOneWidget);
      expect(find.text('Flag for Donation'), findsOneWidget);
      expect(find.text('Flag Item'), findsOneWidget);
      expect(find.text('Dismiss'), findsNWidgets(2));

      // Tap Suggest 20% Discount
      final suggestBtn = find.text('Suggest 20% Discount');
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

      // Dismiss Card 1
      final dismissBtn1 = find.text('Dismiss').first;
      await tester.ensureVisible(dismissBtn1);
      await tester.tap(dismissBtn1);
      await tester.pumpAndSettle();
      expect(find.text('Almond Croissant'), findsNothing);
      expect(find.text('Spinach Feta\nQuiche'), findsOneWidget);

      // Dismiss Card 2
      final dismissBtn2 = find.text('Dismiss').first;
      await tester.ensureVisible(dismissBtn2);
      await tester.tap(dismissBtn2);
      await tester.pumpAndSettle();
      expect(find.text('No waste alerts'), findsOneWidget);
      expect(find.text('All items are currently performing well.'), findsOneWidget);
    });

    test('InventoryProvider initial state and mutations', () {
      final provider = InventoryProvider();

      expect(provider.itemCount, 3);
      expect(provider.items.first.name, 'Croissants');
      expect(provider.items.first.isPerishable, true);
      expect(provider.items.first.restockQuantity, 45);

      provider.addItem(
        name: 'Blueberry Muffin',
        category: 'Bakery',
        unit: 'Units',
        currentStock: 10,
        isPerishable: true,
      );

      expect(provider.itemCount, 4);
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
      expect(provider.itemCount, 3);
    });

    test('StockCheckProvider initial state and mutations', () {
      final provider = StockCheckProvider();

      expect(provider.entries.length, 4);
      
      // Almond Milk
      final almond = provider.entries[0];
      expect(almond.name, 'Almond Milk (Barista)');
      expect(almond.actualQuantity, 5);
      expect(almond.isAutoCalculated, true);
      expect(almond.isManualOverride, false);

      // Croissants perishable reset daily
      final croissants = provider.entries[2];
      expect(croissants.name, 'Croissants (Butter)');
      expect(croissants.isPerishable, true);

      // Oat Milk manual override
      final oat = provider.entries[3];
      expect(oat.name, 'Oat Milk');
      expect(oat.actualQuantity, 8);
      expect(oat.isManualOverride, true);

      // Mutate Almond Milk quantity 5 -> 6
      provider.updateQuantity(almond.id, 6);
      final updatedAlmond = provider.entries[0];
      expect(updatedAlmond.actualQuantity, 6);
      expect(updatedAlmond.isAutoCalculated, false);
      expect(updatedAlmond.isManualOverride, true);

      // Confirm stock
      expect(provider.isConfirmed, false);
      provider.confirmStock();
      expect(provider.isConfirmed, true);
    });

    test('Restock Qty formula logic tests', () {
      int calculateRestock(int predicted, int safety, int current) {
        return max(0, predicted + safety - current);
      }

      // Croissants test: 50 + 5 - 10 = 45
      expect(calculateRestock(50, 5, 10), 45);

      // Espresso Beans test: 15 + 3 - 6 = 12
      expect(calculateRestock(15, 3, 6), 12);

      // Whole Milk test: 10 + 2 - 4 = 8
      expect(calculateRestock(10, 2, 4), 8);

      // Negative restock protection test: 10 + 5 - 20 = 0
      expect(calculateRestock(10, 5, 20), 0);
    });

    testWidgets('ItemSetupScreen renders items and form controls', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
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

    testWidgets('DashboardScreen renders header, badge, and forecast cards', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: DashboardScreen(),
          ),
        ),
      );

      expect(find.text('RestockIQ'), findsOneWidget);
      expect(find.text('Learning your patterns • Day 5 of 14'), findsOneWidget);
      expect(find.text("Today's Forecast"), findsOneWidget);
      expect(find.text('Croissants'), findsOneWidget);
      expect(find.text('Espresso Beans'), findsOneWidget);
      expect(find.text('Whole Milk'), findsOneWidget);
      expect(find.text('45'), findsOneWidget);
      expect(find.text('12'), findsOneWidget);
      expect(find.text('8'), findsOneWidget);
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
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
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

    testWidgets('InventoryCheckInScreen renders stock items, status badges, and confirm button', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: InventoryCheckInScreen(),
          ),
        ),
      );

      expect(find.text("Today's Stock Check"), findsOneWidget);
      expect(find.text('Verify auto-calculated quantities or adjust manually.'), findsOneWidget);
      expect(find.text('Almond Milk (Barista)'), findsOneWidget);
      expect(find.text('Espresso Beans (House)'), findsOneWidget);
      expect(find.text('Croissants (Butter)'), findsOneWidget);
      expect(find.text('Oat Milk'), findsOneWidget);
      expect(find.text('Auto-calculated'), findsNWidgets(2));
      expect(find.text('Resets daily'), findsOneWidget);
      expect(find.text('Manual Override'), findsOneWidget);
      expect(find.text("✓ Confirm Today's Stock"), findsOneWidget);
    });

    testWidgets('Editing Almond Milk quantity in InventoryCheckInScreen updates status to Manual Override', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: InventoryCheckInScreen(),
          ),
        ),
      );

      // Tap pencil edit icon on Almond Milk
      final editIconFinder = find.byIcon(Icons.edit_outlined).first;
      await tester.tap(editIconFinder);
      await tester.pumpAndSettle();

      // Tap plus button to increment 5 -> 6
      final plusFinder = find.byIcon(Icons.add);
      await tester.tap(plusFinder);
      await tester.pumpAndSettle();

      // Tap check icon to finish editing
      final checkFinder = find.byIcon(Icons.check_circle_rounded);
      await tester.tap(checkFinder);
      await tester.pumpAndSettle();

      // Expect Almond Milk now shows Manual Override
      expect(find.text('6'), findsOneWidget);
      expect(find.text('Manual Override'), findsNWidgets(2));
    });

    testWidgets('Confirming stock updates button state and shows snackbar', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
          ],
          child: const MaterialApp(
            home: InventoryCheckInScreen(),
          ),
        ),
      );

      final confirmBtnFinder = find.text("✓ Confirm Today's Stock");
      await tester.ensureVisible(confirmBtnFinder);
      await tester.tap(confirmBtnFinder);
      await tester.pump();

      expect(find.text('✓ Stock Confirmed'), findsOneWidget);
      expect(find.text("Today's stock confirmed successfully."), findsOneWidget);
    });

    testWidgets('SettingsScreen renders header, profile section, settings cards, and bottom nav', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
          ],
          child: const MaterialApp(
            home: SettingsScreen(),
          ),
        ),
      );

      expect(find.text('RestockIQ'), findsOneWidget);
      expect(find.text('The Corner Crumb'), findsOneWidget);
      expect(find.text('Owner Account'), findsOneWidget);
      expect(find.text('Manage Items'), findsOneWidget);
      expect(find.text('Manage Staff'), findsOneWidget);
      expect(find.text('Notifications'), findsOneWidget);
      expect(find.text('Low stock & forecast alerts'), findsOneWidget);
      expect(find.text('Log Out'), findsOneWidget);
      expect(find.byType(Switch), findsOneWidget);
    });

    testWidgets('SettingsScreen notification toggle switches state', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
          ],
          child: const MaterialApp(
            home: SettingsScreen(),
          ),
        ),
      );

      final switchFinder = find.byType(Switch);
      expect(tester.widget<Switch>(switchFinder).value, true);

      await tester.tap(switchFinder);
      await tester.pumpAndSettle();
      expect(tester.widget<Switch>(switchFinder).value, false);

      await tester.tap(switchFinder);
      await tester.pumpAndSettle();
      expect(tester.widget<Switch>(switchFinder).value, true);
    });

    testWidgets('SettingsScreen Log Out shows confirmation dialog and navigates on confirm', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
          ],
          child: const MaterialApp(
            home: SettingsScreen(),
          ),
        ),
      );

      // Tap Log Out
      final logOutFinder = find.text('Log Out');
      await tester.ensureVisible(logOutFinder);
      await tester.tap(logOutFinder);
      await tester.pumpAndSettle();

      expect(find.text('Log Out?'), findsOneWidget);
      expect(find.text('Are you sure you want to log out?'), findsOneWidget);

      // Tap Cancel
      final cancelFinder = find.text('Cancel');
      await tester.tap(cancelFinder);
      await tester.pumpAndSettle();

      expect(find.text('Log Out?'), findsNothing);

      // Tap Log Out again and confirm
      await tester.ensureVisible(logOutFinder);
      await tester.tap(logOutFinder);
      await tester.pumpAndSettle();

      final confirmLogOutFinder = find.widgetWithText(ElevatedButton, 'Log Out');
      await tester.tap(confirmLogOutFinder);
      await tester.pumpAndSettle();

      expect(find.text('Welcome Back'), findsOneWidget);
    });

    testWidgets('SettingsScreen Manage Items card navigates to ItemSetupScreen', (WidgetTester tester) async {
      await tester.pumpWidget(
        MultiProvider(
          providers: [
            ChangeNotifierProvider(create: (_) => InventoryProvider()),
            ChangeNotifierProvider(create: (_) => StockCheckProvider()),
            ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
          ],
          child: const MaterialApp(
            home: SettingsScreen(),
          ),
        ),
      );

      final manageItemsFinder = find.text('Manage Items');
      await tester.tap(manageItemsFinder);
      await tester.pumpAndSettle();

      expect(find.text('Your Menu Items'), findsOneWidget);
    });
  });
}
