import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/stock_check_entry.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import 'quantity_adjuster.dart';

class StockCheckCard extends StatefulWidget {
  final StockCheckEntry entry;
  final ValueChanged<int> onQuantityChanged;

  const StockCheckCard({
    super.key,
    required this.entry,
    required this.onQuantityChanged,
  });

  @override
  State<StockCheckCard> createState() => _StockCheckCardState();
}

class _StockCheckCardState extends State<StockCheckCard> {
  bool _isEditing = false;

  @override
  Widget build(BuildContext context) {
    final entry = widget.entry;
    final isManual = entry.isManualOverride;
    final isPerishable = entry.isPerishable;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isManual
              ? AppColors.primary
              : AppColors.outlineVariant.withValues(alpha: 0.35),
          width: isManual ? 1.5 : 1.0,
        ),
        boxShadow: const [
          BoxShadow(
            color: AppColors.ambientShadow,
            blurRadius: 10,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Left details: Name & Status
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    entry.name,
                    style: GoogleFonts.montserrat(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: AppColors.onSurface,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 4),
                  _buildStatusRow(entry),
                ],
              ),
            ),
            const SizedBox(width: 12),

            // Right side: Quantity & Action
            if (isPerishable)
              // Perishable item layout: No quantity input shown
              const SizedBox.shrink()
            else if (_isEditing)
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  QuantityAdjuster(
                    value: entry.actualQuantity,
                    onChanged: (newQty) {
                      widget.onQuantityChanged(newQty);
                    },
                  ),
                  const SizedBox(width: 4),
                  IconButton(
                    icon: const Icon(
                      Icons.check_circle_rounded,
                      color: AppColors.primary,
                      size: 24,
                    ),
                    onPressed: () {
                      setState(() {
                        _isEditing = false;
                      });
                    },
                    tooltip: 'Done editing',
                  ),
                ],
              )
            else
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${entry.actualQuantity}',
                    style: GoogleFonts.montserrat(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primaryDark,
                    ),
                  ),
                  const SizedBox(width: 4),
                  SizedBox(
                    width: 40,
                    height: 40,
                    child: IconButton(
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(
                        minWidth: 40,
                        minHeight: 40,
                      ),
                      icon: const Icon(
                        Icons.edit_outlined,
                        size: 20,
                        color: AppColors.primary,
                      ),
                      onPressed: () {
                        setState(() {
                          _isEditing = true;
                        });
                      },
                      tooltip: 'Edit quantity',
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusRow(StockCheckEntry entry) {
    if (entry.isPerishable) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (entry.category != null && entry.category!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 2),
              child: Text(
                entry.category!,
                style: AppTypography.bodyMd.copyWith(
                  fontSize: 13,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.restart_alt_rounded,
                size: 15,
                color: AppColors.onSurfaceVariant,
              ),
              const SizedBox(width: 4),
              Text(
                'Resets daily',
                style: AppTypography.bodyMd.copyWith(
                  fontSize: 13,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ],
      );
    }

    if (entry.isManualOverride) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.flash_on_outlined,
            size: 15,
            color: AppColors.primary,
          ),
          const SizedBox(width: 4),
          Text(
            'Manual Override',
            style: AppTypography.bodyMd.copyWith(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: AppColors.primary,
            ),
          ),
        ],
      );
    }

    // Default: Auto-calculated
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(
          Icons.auto_awesome,
          size: 15,
          color: Color(0xFF8A6A00),
        ),
        const SizedBox(width: 4),
        Text(
          'Auto-calculated',
          style: AppTypography.bodyMd.copyWith(
            fontSize: 13,
            color: AppColors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
