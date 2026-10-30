import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../providers/stock_check_provider.dart';
import '../repositories/app_repository.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dashboard_forecast_card.dart';
import '../widgets/ai_briefing_card.dart';
import '../widgets/demo_banner.dart';
import '../widgets/dotted_background.dart';
import 'item_detail_forecast_screen.dart';
import 'item_setup_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Future<void> _showWorkspaceDialog(BuildContext context, bool isDemo) async {
    final scaffoldMessenger = ScaffoldMessenger.of(context);
    final inv = Provider.of<InventoryProvider>(context, listen: false);
    final waste = Provider.of<WasteAlertsProvider>(context, listen: false);
    final stock = Provider.of<StockCheckProvider>(context, listen: false);

    await showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(
              isDemo ? Icons.science_rounded : Icons.storefront_rounded,
              color: isDemo ? const Color(0xFFD97706) : const Color(0xFF2E7D32),
              size: 26,
            ),
            const SizedBox(width: 10),
            Text(
              isDemo ? 'Demo Sandbox' : 'My Store (Live)',
              style: GoogleFonts.montserrat(
                fontWeight: FontWeight.w700,
                fontSize: 18,
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isDemo
                  ? 'Currently using the replayed French bakery dataset with 7 sample items and simulated midday waste alerts.'
                  : 'Currently connected to your live personal store inventory and real tracking.',
              style: GoogleFonts.inter(fontSize: 13, color: Colors.grey.shade800),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: isDemo ? const Color(0xFFFFF7ED) : const Color(0xFFF0FDF4),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: isDemo ? const Color(0xFFFFD8A8) : const Color(0xFFBBF7D0),
                ),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: 18,
                    color: isDemo ? const Color(0xFFB45309) : const Color(0xFF15803D),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      isDemo
                          ? 'Demo data is completely isolated. You can switch to My Store or reset sample bakery data at any time.'
                          : 'You can test the app with 60 days of replayed bakery sales by switching to Demo Sandbox.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        color: isDemo ? const Color(0xFF92400E) : const Color(0xFF166534),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx),
            child: const Text('Close'),
          ),
          if (isDemo) ...[
            OutlinedButton.icon(
              onPressed: () async {
                Navigator.pop(dialogCtx);
                scaffoldMessenger.showSnackBar(
                  const SnackBar(
                    content: Text('Resetting demo sandbox...'),
                    duration: Duration(seconds: 1),
                  ),
                );
                try {
                  await ApiService.instance.resetDemo();
                  if (!context.mounted) return;
                  await inv.fetchDashboardItems();
                  await waste.fetchCloudWasteAlerts();
                  stock.syncWithInventoryItems(inv.items);
                  await stock.fetchYesterdayReviewRoutine();
                  scaffoldMessenger.showSnackBar(
                    const SnackBar(
                      content: Text('Demo sandbox reset! 7 demo bakery items & active alerts loaded.'),
                      backgroundColor: Color(0xFF2E7D32),
                      duration: Duration(seconds: 3),
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
              },
              icon: const Icon(Icons.refresh_rounded, size: 16),
              label: const Text('Reset Demo'),
            ),
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF2E7D32),
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                Navigator.pop(dialogCtx);
                scaffoldMessenger.showSnackBar(
                  const SnackBar(
                    content: Text('Switching to My Store...'),
                    duration: Duration(seconds: 1),
                  ),
                );
                try {
                  await ApiService.instance.exitDemo();
                } catch (_) {
                  ApiService.instance.setWorkspace(null);
                }
                if (!context.mounted) return;
                inv.setRepository(LiveRepository());
                waste.setRepository(LiveRepository());
                stock.setRepository(LiveRepository());
                await inv.fetchDashboardItems();
                await waste.fetchCloudWasteAlerts();
                scaffoldMessenger.showSnackBar(
                  const SnackBar(
                    content: Text('Switched to My Store (Live Mode)'),
                    backgroundColor: Color(0xFF2E7D32),
                    duration: Duration(seconds: 2),
                  ),
                );
              },
              icon: const Icon(Icons.storefront_rounded, size: 16),
              label: const Text('Go to My Store'),
            ),
          ] else ...[
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFD97706),
                foregroundColor: Colors.white,
              ),
              onPressed: () async {
                Navigator.pop(dialogCtx);
                scaffoldMessenger.showSnackBar(
                  const SnackBar(
                    content: Text('Starting Demo Sandbox...'),
                    duration: Duration(seconds: 1),
                  ),
                );
                try {
                  await ApiService.instance.startDemo();
                  if (!context.mounted) return;
                  inv.setRepository(LiveRepository());
                  waste.setRepository(LiveRepository());
                  stock.setRepository(LiveRepository());
                  await inv.fetchDashboardItems();
                  await waste.fetchCloudWasteAlerts();
                  stock.syncWithInventoryItems(inv.items);
                  await stock.fetchYesterdayReviewRoutine();
                  scaffoldMessenger.showSnackBar(
                    const SnackBar(
                      content: Text('Demo Sandbox Ready! 7 French bakery items loaded.'),
                      backgroundColor: Color(0xFF2E7D32),
                      duration: Duration(seconds: 3),
                    ),
                  );
                } catch (e) {
                  scaffoldMessenger.showSnackBar(
                    SnackBar(
                      content: Text('Failed to start demo: $e'),
                      backgroundColor: Colors.red.shade700,
                    ),
                  );
                }
              },
              icon: const Icon(Icons.science_rounded, size: 16),
              label: const Text('Try Demo Mode'),
            ),
          ],
        ],
      ),
    );
  }

  String _formatTime(DateTime? dt) {
    if (dt == null) return 'Synchronized';
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return 'Data as of $h:$m';
  }

  @override
  Widget build(BuildContext context) {
    final inventoryProvider = Provider.of<InventoryProvider>(context);
    final items = inventoryProvider.items;
    final isDemo = inventoryProvider.isDemoTour;
    final modeLabel = inventoryProvider.modeLabel;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 0),
      body: DottedBackground(
        child: Column(
          children: [
            // Top Header Bar
            SafeArea(
              bottom: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const DemoBanner(),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(
                        Icons.store_rounded,
                        color: AppColors.primaryDark,
                        size: 24,
                      ),
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const ItemSetupScreen(),
                          ),
                        );
                      },
                      tooltip: 'Catalog',
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'RestockIQ',
                      style: GoogleFonts.montserrat(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primaryDark,
                      ),
                    ),
                    const Spacer(),

                    // LIVE / DEMO Badge (Interactive Switcher)
                    InkWell(
                      onTap: () => _showWorkspaceDialog(context, isDemo),
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3.5),
                        decoration: BoxDecoration(
                          color: isDemo
                              ? const Color(0xFFFFF3E0)
                              : const Color(0xFFE8F5E9),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: isDemo
                                ? const Color(0xFFFFB74D)
                                : const Color(0xFFA5D6A7),
                            width: 1.0,
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 6,
                              height: 6,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: isDemo
                                    ? const Color(0xFFE65100)
                                    : const Color(0xFF2E7D32),
                              ),
                            ),
                            const SizedBox(width: 5),
                            Text(
                              modeLabel,
                              style: GoogleFonts.inter(
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                color: isDemo
                                    ? const Color(0xFFE65100)
                                    : const Color(0xFF2E7D32),
                              ),
                            ),
                            const SizedBox(width: 2),
                            Icon(
                              Icons.arrow_drop_down_rounded,
                              size: 14,
                              color: isDemo
                                  ? const Color(0xFFE65100)
                                  : const Color(0xFF2E7D32),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              ],
              ),
            ),

            // Waking Server Notification Banner
            ValueListenableBuilder<bool>(
              valueListenable: ApiService.isWakingUpServer,
              builder: (context, isWaking, _) {
                if (!isWaking) return const SizedBox.shrink();
                return Container(
                  width: double.infinity,
                  color: const Color(0xFFFFF3E0),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const SizedBox(
                        width: 12,
                        height: 12,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Color(0xFFE65100),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Waking cloud backend server on Render...',
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: const Color(0xFFE65100),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),

            // Main Scrollable Area with Pull-To-Refresh
            Expanded(
              child: RefreshIndicator(
                color: AppColors.primary,
                onRefresh: () async {
                  await inventoryProvider.fetchDashboardItems();
                },
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 480),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Operational Status / Timestamp Pill
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                _formatTime(inventoryProvider.lastSyncedAt),
                                style: GoogleFonts.inter(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500,
                                  color: AppColors.onSurfaceVariant,
                                ),
                              ),
                              if (inventoryProvider.isLoading)
                                Row(
                                  children: [
                                    const SizedBox(
                                      width: 10,
                                      height: 10,
                                      child: CircularProgressIndicator(strokeWidth: 1.5, color: AppColors.primary),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'Syncing...',
                                      style: GoogleFonts.inter(fontSize: 11, color: AppColors.primary),
                                    ),
                                  ],
                                ),
                            ],
                          ),
                          const SizedBox(height: 10),

                          // Executive AI Briefing Card
                          const AiBriefingCard(),
                          const SizedBox(height: 16),

                          // Main Section Heading
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                "Today's Forecast",
                                style: GoogleFonts.montserrat(
                                  fontSize: 22,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.primaryDark,
                                ),
                              ),
                              Text(
                                '${items.length} items',
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.onSurfaceVariant,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),

                          // Forecast Items List or Empty State
                          if (items.isEmpty && !inventoryProvider.isLoading)
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(28),
                              decoration: BoxDecoration(
                                color: AppColors.cardSurface,
                                borderRadius: BorderRadius.circular(20),
                                boxShadow: const [
                                  BoxShadow(
                                    color: AppColors.ambientShadow,
                                    blurRadius: 16,
                                    offset: Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Column(
                                children: [
                                  const Icon(
                                    Icons.storefront_outlined,
                                    size: 48,
                                    color: AppColors.outlineVariant,
                                  ),
                                  const SizedBox(height: 12),
                                  Text(
                                    'Catalog is empty',
                                    style: AppTypography.headlineMd.copyWith(
                                      fontSize: 18,
                                      color: AppColors.primaryDark,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Text(
                                    'Add your first item to begin generating AI demand forecasts and replenishment orders.',
                                    style: AppTypography.bodyMd,
                                    textAlign: TextAlign.center,
                                  ),
                                  const SizedBox(height: 18),
                                  ElevatedButton.icon(
                                    onPressed: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => const ItemSetupScreen(),
                                        ),
                                      );
                                    },
                                    icon: const Icon(Icons.add_rounded),
                                    label: const Text('Add Menu Item'),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: AppColors.primary,
                                      foregroundColor: AppColors.onPrimary,
                                      shape: const StadiumBorder(),
                                    ),
                                  ),
                                ],
                              ),
                            )
                          else
                            ...items.map((item) {
                              return DashboardForecastCard(
                                item: item,
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) =>
                                          ItemDetailForecastScreen(item: item),
                                    ),
                                  );
                                },
                              );
                            }),
                          if (items.any((item) => item.isReplayedDataset)) ...[
                            const SizedBox(height: 12),
                            Center(
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 6),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF1F5F9),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                      color: const Color(0xFFCBD5E1)),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(
                                      Icons.history_edu_rounded,
                                      size: 14,
                                      color: Color(0xFF64748B),
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      'Replayed dataset',
                                      style: GoogleFonts.inter(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: const Color(0xFF475569),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                          const SizedBox(height: 16),
                        ],
                      ),
                    ),
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
