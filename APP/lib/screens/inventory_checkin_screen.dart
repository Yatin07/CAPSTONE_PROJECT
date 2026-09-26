import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/stock_check_provider.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import '../widgets/stock_check_card.dart';
import 'dashboard_screen.dart';
import 'item_setup_screen.dart';

class InventoryCheckInScreen extends StatefulWidget {
  const InventoryCheckInScreen({super.key});

  @override
  State<InventoryCheckInScreen> createState() => _InventoryCheckInScreenState();
}

class _InventoryCheckInScreenState extends State<InventoryCheckInScreen> {
  @override
  Widget build(BuildContext context) {
    final stockCheckProvider = Provider.of<StockCheckProvider>(context);
    final entries = stockCheckProvider.entries;
    final isConfirmed = stockCheckProvider.isConfirmed;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 1),
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

            // Scrollable Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Main Title
                        Text(
                          "Today's Stock Check",
                          style: GoogleFonts.montserrat(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: AppColors.primaryDark,
                          ),
                        ),
                        const SizedBox(height: 6),

                        // Subtitle / Description
                        Text(
                          'Verify auto-calculated quantities or adjust manually.',
                          style: AppTypography.bodyMd.copyWith(
                            color: AppColors.onSurfaceVariant,
                            fontSize: 14,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Stock Item List or Empty State
                        if (entries.isEmpty)
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
                                  'No stock items to check.',
                                  style: AppTypography.headlineMd.copyWith(
                                    fontSize: 18,
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  'Add menu items first to start checking stock.',
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
                                  label: const Text('Go to Menu Items'),
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
                          ...entries.map(
                            (entry) => StockCheckCard(
                              entry: entry,
                              onQuantityChanged: (newQty) {
                                stockCheckProvider.updateQuantity(
                                  entry.id,
                                  newQty,
                                );
                              },
                            ),
                          ),

                        const SizedBox(height: 20),

                        // Confirm Today's Stock Button
                        if (entries.isNotEmpty)
                          PrimaryButton(
                            label: isConfirmed
                                ? '✓ Stock Confirmed'
                                : '✓ Confirm Today\'s Stock',
                            onPressed: isConfirmed
                                ? null
                                : () {
                                    stockCheckProvider.confirmStock();
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text(
                                          'Today\'s stock confirmed successfully.',
                                        ),
                                        backgroundColor: AppColors.primary,
                                        duration: Duration(seconds: 2),
                                      ),
                                    );
                                  },
                          ),

                        const SizedBox(height: 24),
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
