import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/demo_banner.dart';
import '../widgets/dotted_background.dart';
import '../widgets/waste_alert_card.dart';
import 'dashboard_screen.dart';

class WasteAlertsScreen extends StatefulWidget {
  const WasteAlertsScreen({super.key});

  @override
  State<WasteAlertsScreen> createState() => _WasteAlertsScreenState();
}

class _WasteAlertsScreenState extends State<WasteAlertsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        Provider.of<WasteAlertsProvider>(context, listen: false).fetchCloudWasteAlerts();
      }
    });
  }

  void _showSnackBar(BuildContext context, String message) {
    if (message.isEmpty) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          message,
          style: GoogleFonts.inter(
            color: Colors.white,
            fontWeight: FontWeight.w500,
          ),
        ),
        backgroundColor: AppColors.primaryDark,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final alertsProvider = Provider.of<WasteAlertsProvider>(context);
    final activeAlerts = alertsProvider.activeAlerts;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 2),
      body: DottedBackground(
        child: Column(
          children: [
            const DemoBanner(),
            // Top Header Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(
                      Icons.arrow_back_rounded,
                      color: AppColors.primaryDark,
                      size: 22,
                    ),
                    onPressed: () {
                      if (Navigator.canPop(context)) {
                        Navigator.pop(context);
                      } else {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const DashboardScreen(),
                          ),
                        );
                      }
                    },
                    tooltip: 'Back',
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
                ],
              ),
            ),

            // Main Scrollable Body
            Expanded(
              child: RefreshIndicator(
                color: AppColors.primary,
                onRefresh: () => alertsProvider.fetchCloudWasteAlerts(),
                child: SingleChildScrollView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 480),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Main Title (2 lines)
                          Text(
                            'Items Needing\nAttention',
                            style: GoogleFonts.montserrat(
                              fontSize: 28,
                              fontWeight: FontWeight.w700,
                              color: AppColors.primaryDark,
                              height: 1.2,
                            ),
                          ),
                          const SizedBox(height: 10),

                          // Description
                          Text(
                            'Review these items to minimize waste before\nclosing.',
                            style: GoogleFonts.inter(
                              fontSize: 14,
                              fontWeight: FontWeight.w400,
                              color: AppColors.onSurfaceVariant,
                              height: 1.4,
                            ),
                          ),
                          const SizedBox(height: 24),

                          // Active Alert Cards or Empty State
                          if (alertsProvider.isLoading && activeAlerts.isEmpty)
                            const Center(
                              child: Padding(
                                padding: EdgeInsets.all(40),
                                child: CircularProgressIndicator(color: AppColors.primary),
                              ),
                            )
                          else if (activeAlerts.isEmpty)
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(32),
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
                                  if (alertsProvider.storeStatus == 'closed') ...[
                                    const Icon(
                                      Icons.nightlight_round,
                                      size: 56,
                                      color: Color(0xFFD97706),
                                    ),
                                    const SizedBox(height: 16),
                                    Text(
                                      'Store Currently Closed',
                                      style: AppTypography.headlineLg.copyWith(
                                        fontSize: 22,
                                        color: AppColors.primaryDark,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      alertsProvider.storeMessage ??
                                          'Store operating hours: 08:00 - 20:00 local time.\nIntraday pace monitoring will resume when the store opens at 08:00 AM.',
                                      style: AppTypography.bodyMd,
                                      textAlign: TextAlign.center,
                                    ),
                                  ] else ...[
                                    const Icon(
                                      Icons.check_circle_outline_rounded,
                                      size: 56,
                                      color: AppColors.primary,
                                    ),
                                    const SizedBox(height: 16),
                                    Text(
                                      'No waste alerts',
                                      style: AppTypography.headlineLg.copyWith(
                                        fontSize: 22,
                                        color: AppColors.primaryDark,
                                      ),
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      'All items are currently performing well.',
                                      style: AppTypography.bodyMd,
                                      textAlign: TextAlign.center,
                                    ),
                                  ],
                                  const SizedBox(height: 20),
                                  // Only show Reset Demo Alerts during demo tour
                                  if (Provider.of<InventoryProvider>(context, listen: false).isDemoTour)
                                    OutlinedButton.icon(
                                      onPressed: () async {
                                        final sm = ScaffoldMessenger.of(context);
                                        sm.showSnackBar(const SnackBar(
                                          content: Text('Syncing demo alerts...'),
                                          duration: Duration(seconds: 1),
                                        ));
                                        try {
                                          await ApiService.instance.setDemoClock(14.0);
                                          await alertsProvider.fetchCloudWasteAlerts();
                                          alertsProvider.resetAlerts();
                                          sm.showSnackBar(const SnackBar(
                                            content: Text('Demo alerts active (simulated 14:00 store time)'),
                                            backgroundColor: Color(0xFF2E7D32),
                                            duration: Duration(seconds: 2),
                                          ));
                                        } catch (e) {
                                          alertsProvider.resetAlerts();
                                        }
                                      },
                                      icon: const Icon(Icons.refresh_rounded),
                                      label: const Text('Reset Demo Alerts'),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor: AppColors.primary,
                                        side: const BorderSide(
                                          color: AppColors.primary,
                                        ),
                                        shape: const StadiumBorder(),
                                      ),
                                    ),
                                ],
                              ),
                            )
                          else
                            ...activeAlerts.map((alert) {
                              return WasteAlertCard(
                                alert: alert,
                                onRecommendTap: () {
                                  final msg = alertsProvider.suggestRecommendation(alert.id);
                                  _showSnackBar(context, msg);
                                },
                                onPrimaryTap: () {
                                  final msg = alertsProvider.applyPrimaryAction(alert.id);
                                  _showSnackBar(context, msg);
                                },
                                onDismissTap: () {
                                  alertsProvider.dismissAlert(alert.id);
                                },
                              );
                            }),
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
