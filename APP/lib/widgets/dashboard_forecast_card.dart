import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/inventory_item.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';

class DashboardForecastCard extends StatelessWidget {
  final InventoryItem item;
  final VoidCallback onTap;

  const DashboardForecastCard({
    super.key,
    required this.item,
    required this.onTap,
  });

  IconData _getItemIcon() {
    final lowerName = item.name.toLowerCase();
    if (lowerName.contains('croissant') || item.category.toLowerCase() == 'bakery') {
      return Icons.bakery_dining_rounded;
    } else if (lowerName.contains('espresso') || lowerName.contains('coffee') || lowerName.contains('bean')) {
      return Icons.coffee_maker_outlined;
    } else if (lowerName.contains('milk') || lowerName.contains('liquid')) {
      return Icons.water_drop_outlined;
    }
    return Icons.inventory_2_outlined;
  }

  Color _getProgressBarColor() {
    final lowerName = item.name.toLowerCase();
    if (item.riskLevel == 'high' || lowerName.contains('milk')) {
      return AppColors.tertiaryCoral;
    } else if (lowerName.contains('croissant')) {
      return AppColors.secondaryAmber;
    } else if (lowerName.contains('espresso') || lowerName.contains('coffee')) {
      return AppColors.primary;
    }
    return AppColors.primary;
  }

  bool _hasStatusDot() {
    final lowerName = item.name.toLowerCase();
    return item.riskLevel == 'high' ||
        lowerName.contains('croissant') ||
        lowerName.contains('milk');
  }

  String _getRestockLabel() {
    final unitUpper = item.unit.toUpperCase();
    if (unitUpper == 'UNITS' || unitUpper == 'UNIT' || unitUpper == 'PCS') {
      return 'RESTOCK';
    }
    return 'RESTOCK ($unitUpper)';
  }

  String _getDescriptionText() {
    if (item.description != null && item.description!.isNotEmpty) {
      return item.description!;
    }
    if (item.isPerishable) {
      return 'High spoilage risk\nbased on recent data';
    }
    return 'Steady consumption,\nlow stock approaching';
  }

  @override
  Widget build(BuildContext context) {
    final restockQty = item.restockQuantity;
    final progressVal = item.stockProgress;
    final progressColor = _getProgressBarColor();

    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(20),
          child: Container(
            padding: const EdgeInsets.all(18),
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
              border: Border.all(
                color: AppColors.outlineVariant.withValues(alpha: 0.25),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Row: Circular Icon + Item Name + Status Dot
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 42,
                      height: 42,
                      decoration: const BoxDecoration(
                        color: AppColors.inputFill,
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        _getItemIcon(),
                        size: 22,
                        color: AppColors.primaryDark,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          item.name,
                          style: GoogleFonts.montserrat(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                          ),
                        ),
                      ),
                    ),
                    if (_hasStatusDot())
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                            color: AppColors.tertiaryCoral,
                            shape: BoxShape.circle,
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),

                // Middle Row: Description (left) & Restock Qty (right)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      flex: 6,
                      child: Text(
                        _getDescriptionText(),
                        style: AppTypography.bodyMd.copyWith(
                          fontSize: 13,
                          height: 1.35,
                          color: AppColors.onSurfaceVariant,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      flex: 4,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            _getRestockLabel(),
                            style: GoogleFonts.inter(
                              fontSize: 10,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 0.5,
                              color: AppColors.onSurfaceVariant,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '$restockQty',
                            style: GoogleFonts.montserrat(
                              fontSize: 32,
                              fontWeight: FontWeight.w800,
                              height: 1.0,
                              color: AppColors.primary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                // Bottom Row: Custom Rounded Progress Indicator
                LayoutBuilder(
                  builder: (context, constraints) {
                    final totalWidth = constraints.maxWidth;
                    final progressWidth = (totalWidth * progressVal).clamp(16.0, totalWidth);

                    return Stack(
                      children: [
                        Container(
                          height: 5,
                          width: double.infinity,
                          decoration: BoxDecoration(
                            color: const Color(0xFFE5E0DA),
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                        Container(
                          height: 5,
                          width: progressWidth,
                          decoration: BoxDecoration(
                            color: progressColor,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
