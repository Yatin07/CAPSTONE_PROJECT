import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../utils/string_extensions.dart';
import 'package:provider/provider.dart';
import '../models/stock_check_entry.dart';
import '../providers/inventory_provider.dart';
import '../providers/stock_check_provider.dart';
import '../theme/app_colors.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/demo_banner.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import 'dashboard_screen.dart';

class InventoryCheckInScreen extends StatefulWidget {
  const InventoryCheckInScreen({super.key});

  @override
  State<InventoryCheckInScreen> createState() => _InventoryCheckInScreenState();
}

class _InventoryCheckInScreenState extends State<InventoryCheckInScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String _dateMode = 'today'; // 'today' or 'yesterday'
  final Map<String, TextEditingController> _controllers = {};
  final Map<String, TextEditingController> _middayControllers = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final invProvider = Provider.of<InventoryProvider>(context, listen: false);
      final stockProvider = Provider.of<StockCheckProvider>(context, listen: false);
      stockProvider.syncWithInventoryItems(invProvider.items);
      stockProvider.fetchYesterdayReviewRoutine();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    for (final c in _controllers.values) {
      c.dispose();
    }
    for (final c in _middayControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  TextEditingController _getController(StockCheckEntry entry) {
    if (!_controllers.containsKey(entry.id)) {
      final initialVal = entry.closingUnitsLeft ?? entry.availableStock;
      _controllers[entry.id] = TextEditingController(text: initialVal.toString());
    }
    return _controllers[entry.id]!;
  }

  TextEditingController _getMiddayController(StockCheckEntry entry) {
    if (!_middayControllers.containsKey(entry.id)) {
      _middayControllers[entry.id] = TextEditingController(text: entry.actualQuantity.toString());
    }
    return _middayControllers[entry.id]!;
  }

  @override
  Widget build(BuildContext context) {
    final stockCheckProvider = Provider.of<StockCheckProvider>(context);
    final entries = stockCheckProvider.entries;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 1),
      body: DottedBackground(
        child: Column(
          children: [
            const DemoBanner(),
            // Top Header Bar
            SafeArea(
              bottom: false,
              child: Padding(
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
                      'Daily Inventory Routines',
                      style: GoogleFonts.montserrat(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primaryDark,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Tab bar
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFF3ECE1),
                borderRadius: BorderRadius.circular(14),
              ),
              child: TabBar(
                controller: _tabController,
                isScrollable: true,
                tabAlignment: TabAlignment.start,
                labelPadding: const EdgeInsets.symmetric(horizontal: 14),
                indicatorSize: TabBarIndicatorSize.tab,
                indicator: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(12),
                ),
                labelColor: Colors.white,
                unselectedLabelColor: AppColors.primaryDark,
                labelStyle: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600),
                tabs: const [
                  Tab(text: 'Closing Count'),
                  Tab(text: 'Mid-Day Pace'),
                  Tab(text: 'Yesterday Review'),
                ],
              ),
            ),

            // Tab Views
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildClosingCountTab(stockCheckProvider, entries),
                  _buildMiddayTab(stockCheckProvider, entries),
                  _buildYesterdayReviewTab(stockCheckProvider),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildClosingCountTab(StockCheckProvider provider, List<StockCheckEntry> entries) {
    if (entries.isEmpty) {
      return Center(
        child: Text(
          'No catalog items found. Add items to submit closing counts.',
          style: GoogleFonts.inter(fontSize: 14, color: AppColors.onSurfaceVariant),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Date Mode Selector: Today vs Yesterday
              Wrap(
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 8,
                runSpacing: 8,
                children: [
                  Text(
                    'Target Date:',
                    style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.primaryDark),
                  ),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      ChoiceChip(
                        label: const Text('Today'),
                        selected: _dateMode == 'today',
                        selectedColor: AppColors.primary.withValues(alpha: 0.15),
                        onSelected: (val) {
                          if (val) setState(() => _dateMode = 'today');
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: const Text('Yesterday (Backfill)'),
                        selected: _dateMode == 'yesterday',
                        selectedColor: AppColors.primary.withValues(alpha: 0.15),
                        onSelected: (val) {
                          if (val) setState(() => _dateMode = 'yesterday');
                        },
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),

              Text(
                'Record leftover units at closing. Perishable leftovers become waste; non-perishables carry over.',
                style: GoogleFonts.inter(fontSize: 12, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 16),

              if (provider.submissionMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFA5D6A7)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.check_circle_rounded, color: Color(0xFF2E7D32), size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          provider.submissionMessage!,
                          style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: const Color(0xFF2E7D32)),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              if (provider.submissionError != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.error.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          provider.submissionError!,
                          style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.error),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Item Cards
              ...entries.map((entry) {
                final ctrl = _getController(entry);
                final hasError = entry.validationError != null;

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.cardSurface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: hasError
                          ? AppColors.error
                          : AppColors.outlineVariant.withValues(alpha: 0.3),
                      width: hasError ? 1.5 : 1.0,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: AppColors.ambientShadow,
                        blurRadius: 10,
                        offset: Offset(0, 3),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              entry.name.toTitleCase(),
                              style: GoogleFonts.montserrat(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: AppColors.primaryDark,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: entry.isPerishable
                                  ? const Color(0xFFFFEBEE)
                                  : const Color(0xFFE8F5E9),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              entry.isPerishable ? 'Perishable' : 'Non-perishable',
                              style: GoogleFonts.inter(
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                                color: entry.isPerishable ? Colors.red.shade800 : Colors.green.shade800,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Available: ${entry.availableStock} (Opening: ${entry.openingStock} + Added: ${entry.producedOrRestocked})',
                        style: GoogleFonts.inter(fontSize: 12, color: AppColors.onSurfaceVariant),
                      ),
                      const SizedBox(height: 10),

                      Row(
                        children: [
                          Expanded(
                            flex: 5,
                            child: TextField(
                              controller: ctrl,
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                labelText: 'Units Left at Close',
                                labelStyle: const TextStyle(fontSize: 12),
                                floatingLabelBehavior: FloatingLabelBehavior.always,
                                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                                border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                                errorText: entry.validationError,
                              ),
                              onChanged: (val) {
                                final parsed = int.tryParse(val.trim()) ?? 0;
                                provider.updateClosingUnitsLeft(entry.id, parsed);
                              },
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            flex: 4,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Sold: ${entry.soldUnits ?? 0}', style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w600)),
                                Text('Waste: ${entry.wasteUnits ?? 0}', style: GoogleFonts.inter(fontSize: 12, color: entry.wasteUnits != null && entry.wasteUnits! > 0 ? Colors.red.shade700 : AppColors.onSurfaceVariant)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                );
              }),

              const SizedBox(height: 16),
              PrimaryButton(
                label: 'Submit Closing Routine',
                icon: Icons.check_circle_outline_rounded,
                isLoading: provider.isSubmitting,
                onPressed: provider.hasValidationErrors
                    ? null
                    : () {
                        provider.submitClosingRoutine(
                          targetDate: _dateMode == 'yesterday' ? 'yesterday' : null,
                        );
                      },
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMiddayTab(StockCheckProvider provider, List<StockCheckEntry> entries) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Mid-Day Count & Pace Check',
                style: GoogleFonts.montserrat(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
              ),
              const SizedBox(height: 6),
              Text(
                'Input current remaining stock mid-day to measure sales pace against expected store hours.',
                style: GoogleFonts.inter(fontSize: 12, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 16),

              if (provider.middayResult != null) ...[
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE3F2FD),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF90CAF9)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Pace Evaluated Successfully',
                        style: GoogleFonts.inter(fontSize: 14, fontWeight: FontWeight.w700, color: const Color(0xFF1565C0)),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Elapsed Store Hours Fraction: ${((provider.middayResult!['elapsed_fraction'] as num?)?.toDouble() ?? 0.5 * 100).toStringAsFixed(1)}%',
                        style: GoogleFonts.inter(fontSize: 12, color: const Color(0xFF1565C0)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              ...entries.map((entry) {
                final ctrl = _getMiddayController(entry);
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.cardSurface,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          entry.name.toTitleCase(),
                          style: GoogleFonts.montserrat(fontSize: 15, fontWeight: FontWeight.w600),
                        ),
                      ),
                      SizedBox(
                        width: 100,
                        child: TextField(
                          controller: ctrl,
                          keyboardType: TextInputType.number,
                          decoration: InputDecoration(
                            labelText: 'Remaining',
                            labelStyle: const TextStyle(fontSize: 11),
                            floatingLabelBehavior: FloatingLabelBehavior.always,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }),

              const SizedBox(height: 16),
              PrimaryButton(
                label: 'Calculate Mid-Day Pace',
                icon: Icons.speed_rounded,
                isLoading: provider.isMiddaySubmitting,
                onPressed: () {
                  final map = <String, int>{};
                  for (final e in entries) {
                    final ctrl = _getMiddayController(e);
                    map[e.id] = int.tryParse(ctrl.text.trim()) ?? e.actualQuantity;
                  }
                  provider.submitMiddayRoutine(map);
                },
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildYesterdayReviewTab(StockCheckProvider provider) {
    if (provider.isReviewLoading) {
      return const Center(child: CircularProgressIndicator(color: AppColors.primary));
    }

    final review = provider.yesterdayReview;
    if (review == null || review['items'] == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.history_rounded, size: 48, color: AppColors.outlineVariant),
            const SizedBox(height: 12),
            Text('No yesterday review available yet', style: GoogleFonts.inter(fontSize: 14, color: AppColors.onSurfaceVariant)),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: () => provider.fetchYesterdayReviewRoutine(),
              child: const Text('Refresh Review'),
            ),
          ],
        ),
      );
    }

    final reviewItems = (review['items'] as List).cast<Map<String, dynamic>>();

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 480),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Yesterday Performance Review',
                style: GoogleFonts.montserrat(fontSize: 18, fontWeight: FontWeight.w700, color: AppColors.primaryDark),
              ),
              const SizedBox(height: 4),
              Text(
                'Sell-through = sold / available. Thresholds: High (>90%), Normal (70-90%), Low (<70%), Critical (<35%).',
                style: GoogleFonts.inter(fontSize: 12, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 16),

              ...reviewItems.map((item) {
                final isMissing = item['status'] == 'missing';
                final label = item['label']?.toString() ?? (isMissing ? 'no data' : 'Normal');
                final sellThroughPct = item['sellThroughPct'];
                final available = item['availableStock'] ?? 0;
                final sold = item['soldUnits'];

                Color badgeColor = Colors.grey;
                if (label == 'High') badgeColor = const Color(0xFF10B981);
                if (label == 'Normal') badgeColor = const Color(0xFF3B82F6);
                if (label == 'Low') badgeColor = const Color(0xFFF59E0B);
                if (label == 'Critical') badgeColor = const Color(0xFFEF4444);

                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.cardSurface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                    boxShadow: const [
                      BoxShadow(color: AppColors.ambientShadow, blurRadius: 10, offset: Offset(0, 3)),
                    ],
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              item['itemName']?.toString() ?? 'Item',
                              style: GoogleFonts.montserrat(fontSize: 16, fontWeight: FontWeight.w700),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              isMissing
                                  ? 'No closing count recorded'
                                  : 'Available: $available • Sold: $sold',
                              style: GoogleFonts.inter(fontSize: 12, color: AppColors.onSurfaceVariant),
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: badgeColor.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: badgeColor.withValues(alpha: 0.4)),
                        ),
                        child: Column(
                          children: [
                            Text(
                              label,
                              style: GoogleFonts.inter(fontSize: 11, fontWeight: FontWeight.w700, color: badgeColor),
                            ),
                            if (sellThroughPct != null)
                              Text(
                                '$sellThroughPct%',
                                style: GoogleFonts.inter(fontSize: 12, fontWeight: FontWeight.w800, color: badgeColor),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
