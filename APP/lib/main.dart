import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/inventory_provider.dart';
import 'providers/stock_check_provider.dart';
import 'providers/waste_alerts_provider.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard_screen.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final isLoggedIn = await ApiService.instance.tryAutoLogin();
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => InventoryProvider()),
        ChangeNotifierProvider(create: (_) => StockCheckProvider()),
        ChangeNotifierProvider(create: (_) => WasteAlertsProvider()),
      ],
      child: RestockIQApp(initialLoggedIn: isLoggedIn),
    ),
  );
}

class RestockIQApp extends StatelessWidget {
  final bool initialLoggedIn;
  const RestockIQApp({super.key, this.initialLoggedIn = false});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RestockIQ',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: initialLoggedIn ? const DashboardScreen() : const LoginScreen(),
    );
  }
}
