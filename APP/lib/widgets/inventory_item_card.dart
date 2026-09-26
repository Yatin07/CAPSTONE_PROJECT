import 'package:flutter/material.dart';
import '../models/inventory_item.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';

class InventoryItemCard extends StatelessWidget {
  final InventoryItem item;
  final VoidCallback onEdit;
  final VoidCallback? onTap;

  const InventoryItemCard({
    super.key,
    required this.item,
    required this.onEdit,
    this.onTap,
  });

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'bakery':
        return Icons.bakery_dining_rounded;
      case 'beverage':
        return Icons.local_cafe_rounded;
      case 'food':
        return Icons.restaurant_rounded;
      case 'dessert':
        return Icons.cake_rounded;
      case 'snack':
        return Icons.cookie_rounded;
      default:
        return Icons.inventory_2_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(
            color: AppColors.ambientShadow,
            blurRadius: 12,
            offset: Offset(0, 3),
          ),
        ],
        border: Border.all(
          color: AppColors.outlineVariant.withValues(alpha: 0.3),
        ),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                // Icon Container
                Container(
                  width: 46,
                  height: 46,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    _getCategoryIcon(item.category),
                    color: AppColors.primary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 14),

                // Details Column
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: Text(
                              item.name,
                              style: AppTypography.labelBold.copyWith(
                                fontSize: 16,
                                color: AppColors.onSurface,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          if (item.isPerishable)
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 6,
                                vertical: 2,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.tertiaryCoral
                                    .withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                'Perishable',
                                style: AppTypography.bodyMd.copyWith(
                                  fontSize: 10,
                                  fontWeight: FontWeight.w600,
                                  color: const Color(0xFFD32F2F),
                                ),
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          // Category Chip
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.inputFill,
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              item.category,
                              style: AppTypography.bodyMd.copyWith(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: AppColors.onSurfaceVariant,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '•',
                            style: AppTypography.bodyMd.copyWith(
                              color: AppColors.outlineVariant,
                              fontSize: 12,
                            ),
                          ),
                          const SizedBox(width: 8),
                          // Stock count
                          Text(
                            '${item.currentStock} ${item.unit}',
                            style: AppTypography.bodyMd.copyWith(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: AppColors.primaryDark,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        item.formattedUpdatedTime,
                        style: AppTypography.bodyMd.copyWith(
                          fontSize: 11,
                          color: AppColors.outlineVariant,
                        ),
                      ),
                    ],
                  ),
                ),

                // Edit Button
                IconButton(
                  onPressed: onEdit,
                  icon: const Icon(
                    Icons.edit_outlined,
                    color: AppColors.primary,
                    size: 20,
                  ),
                  tooltip: 'Edit Item',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
