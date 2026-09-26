import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dashboard_forecast_card.dart';
import '../widgets/dotted_background.dart';
import 'item_detail_forecast_screen.dart';
import 'item_setup_screen.dart';

class DashboardScreen extends StatefulWidget {
  final int learningDay;
  final int learningTotalDays;

  const DashboardScreen({
    super.key,
    this.learningDay = 5,
    this.learningTotalDays = 14,
  });

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  Widget build(BuildContext context) {
    final inventoryProvider = Provider.of<InventoryProvider>(context);
    final items = inventoryProvider.items;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 0),
      body: DottedBackground(
        child: Column(
          children: [
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
                            builder: (context) => const ItemSetupScreen(),
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

            // Main Scrollable Area
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Learning Badge Pill
                        Center(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 14,
                              vertical: 7,
                            ),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFFE8B0),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  width: 18,
                                  height: 18,
                                  decoration: const BoxDecoration(
                                    color: Color(0xFF8A5A00),
                                    shape: BoxShape.circle,
                                  ),
                                  child: const Center(
                                    child: Icon(
                                      Icons.lightbulb_rounded,
                                      size: 11,
                                      color: Color(0xFFFFE8B0),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Flexible(
                                  child: Text(
                                    'Learning your patterns • Day ${widget.learningDay} of ${widget.learningTotalDays}',
                                    style: GoogleFonts.inter(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      color: const Color(0xFF4A3400),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),

                        // Subtitle Text
                        Center(
                          child: Text(
                            '${items.length} items need attention today • overall demand trending up this week',
                            style: GoogleFonts.inter(
                              fontSize: 12,
                              fontStyle: FontStyle.italic,
                              color: AppColors.onSurfaceVariant,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Main Section Heading
                        Text(
                          "Today's Forecast",
                          style: GoogleFonts.montserrat(
                            fontSize: 22,
                            fontWeight: FontWeight.w700,
                            color: AppColors.primaryDark,
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Forecast Items List or Empty State
                        if (items.isEmpty)
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
                                  Icons.inventory_2_outlined,
                                  size: 48,
                                  color: AppColors.outlineVariant,
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  'No menu items yet',
                                  style: AppTypography.headlineMd.copyWith(
                                    fontSize: 18,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'Add your first menu item to start generating forecasts.',
                                  style: AppTypography.bodyMd,
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 18),
                                ElevatedButton.icon(
                                  onPressed: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) =>
                                            const ItemSetupScreen(),
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
                        const SizedBox(height: 16),
                      ],
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
