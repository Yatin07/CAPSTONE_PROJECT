import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/stock_check_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../repositories/app_repository.dart';
import '../services/api_service.dart';
import '../screens/store_setup_screen.dart';
import '../screens/dashboard_screen.dart';

class DemoBanner extends StatelessWidget {
  const DemoBanner({super.key});

  Future<void> _handleReset(BuildContext context) async {
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    try {
      await ApiService.instance.resetDemo();
      if (!context.mounted) return;
      final inv = Provider.of<InventoryProvider>(context, listen: false);
      final waste = Provider.of<WasteAlertsProvider>(context, listen: false);
      final stock = Provider.of<StockCheckProvider>(context, listen: false);

      await inv.fetchDashboardItems();
      await waste.fetchCloudWasteAlerts();
      stock.syncWithInventoryItems(inv.items);
      await stock.fetchYesterdayReviewRoutine();
      scaffoldMessenger.showSnackBar(
        const SnackBar(
          content: Text('Demo sandbox reset to initial 60-day replayed state.'),
          backgroundColor: Color(0xFF2E7D32),
          duration: Duration(seconds: 2),
        ),
      );
    } catch (e) {
      scaffoldMessenger.showSnackBar(
        SnackBar(
          content: Text('Reset failed: $e'),
          backgroundColor: Colors.red.shade700,
        ),
      );
    }
  }

  Future<void> _handleExit(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: Text(
          'Start My Store',
          style: GoogleFonts.montserrat(fontWeight: FontWeight.w700),
        ),
        content: const Text(
          'Starting your store will delete all sample bakery data. Your live store will start fresh and empty.\n\nReady to set up your real store?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFD97706),
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Start My Store'),
          ),
        ],
      ),
    );

    if (confirmed != true || !context.mounted) return;

    try {
      await ApiService.instance.exitDemo();
    } catch (_) {
      // Fallback: clear local workspace even if server call fails
      ApiService.instance.setWorkspace(null);
    }

    if (!context.mounted) return;

    // Switch providers to live repository, clear caches
    final inv = Provider.of<InventoryProvider>(context, listen: false);
    final waste = Provider.of<WasteAlertsProvider>(context, listen: false);
    final stock = Provider.of<StockCheckProvider>(context, listen: false);

    inv.setRepository(LiveRepository());
    waste.setRepository(LiveRepository());
    stock.setRepository(LiveRepository());

    // Check if onboarding completed
    final profile = await ApiService.instance.fetchUserProfile();
    final onboardingDone = profile?['onboarding_completed'] == true;

    if (!context.mounted) return;

    if (onboardingDone) {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const DashboardScreen()),
        (route) => false,
      );
    } else {
      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(builder: (_) => const StoreSetupScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!ApiService.instance.isDemoWorkspace) {
      return const SizedBox.shrink();
    }

    return Container(
      width: double.infinity,
      color: const Color(0xFFFFF7ED), // amber-50
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: SafeArea(
        top: false,
        bottom: false,
        child: Row(
          children: [
            const Icon(
              Icons.science_rounded,
              color: Color(0xFFD97706), // amber-600
              size: 18,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'DEMO - sample bakery (replayed dataset). Not your data.',
                style: GoogleFonts.inter(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF92400E), // amber-800
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 6),
            InkWell(
              onTap: () => _handleReset(context),
              borderRadius: BorderRadius.circular(4),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                child: Text(
                  'Reset',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: const Color(0xFFB45309),
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 4),
            InkWell(
              onTap: () => _handleExit(context),
              borderRadius: BorderRadius.circular(4),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFD97706),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  'Exit',
                  style: GoogleFonts.inter(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
