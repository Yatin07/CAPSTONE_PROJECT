import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../models/inventory_item.dart';
import '../providers/inventory_provider.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dotted_background.dart';
import '../widgets/sales_forecast_chart.dart';

class ItemDetailForecastScreen extends StatefulWidget {
  final InventoryItem item;

  const ItemDetailForecastScreen({
    super.key,
    required this.item,
  });

  @override
  State<ItemDetailForecastScreen> createState() =>
      _ItemDetailForecastScreenState();
}

class _ItemDetailForecastScreenState extends State<ItemDetailForecastScreen> {
  bool _isRestockConfirmed = false;

  int get _predictedDemand => widget.item.predictedDemand ?? 42;
  int get _safetyStock => widget.item.safetyStock ?? 6;
  int get _currentStock => widget.item.currentStock;

  bool get _hasActiveAlert =>
      widget.item.hasActiveAlert ||
      (widget.item.description != null &&
          widget.item.description!.contains('Restock held to 0'));

  int get _calculatedRestockQty {
    if (_hasActiveAlert) return 0;
    return widget.item.restockQuantity;
  }

  void _handleConfirmRestock() {
    if (_isRestockConfirmed) return;

    setState(() {
      _isRestockConfirmed = true;
    });

    // Sync live restock to MongoDB Atlas
    try {
      Provider.of<InventoryProvider>(context, listen: false)
          .confirmRestock(widget.item.id, quantity: _calculatedRestockQty);
    } catch (_) {}

    final unitLabel = widget.item.unit.toLowerCase();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Restock confirmed! $_calculatedRestockQty $unitLabel of ${widget.item.name} added to today\'s restock plan.',
        ),
        backgroundColor: AppColors.primary,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 0),
      body: DottedBackground(
        child: Column(
          children: [
            // Header Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: AppColors.primaryDark,
                      size: 20,
                    ),
                    onPressed: () {
                      if (Navigator.canPop(context)) {
                        Navigator.pop(context);
                      }
                    },
                    tooltip: 'Back',
                  ),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      widget.item.name,
                      style: AppTypography.headlineMd.copyWith(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primaryDark,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),

            // Scrollable Body
            Expanded(
              child: SingleChildScrollView(
                padding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Forecast Summary Card
                        _buildForecastSummaryCard(),
                        const SizedBox(height: 16),

                        // AI Assistant Card
                        _buildAIAssistantCard(),
                        const SizedBox(height: 16),

                        // Restock Formula Card
                        _buildRestockFormulaCard(),
                        const SizedBox(height: 16),

                        // Sales vs Prediction Graph Card
                        SalesForecastChart(item: widget.item),
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

  Widget _buildForecastSummaryCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
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
          color: AppColors.outlineVariant.withValues(alpha: 0.3),
        ),
      ),
      child: Column(
        children: [
          Text(
            'Predicted for Tomorrow',
            style: AppTypography.bodyMd.copyWith(
              color: AppColors.onSurfaceVariant,
              fontSize: 14,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            '$_predictedDemand ${widget.item.unit.toLowerCase()}',
            style: AppTypography.headlineLg.copyWith(
              fontSize: 32,
              fontWeight: FontWeight.w700,
              color: AppColors.primaryDark,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAIAssistantCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF7F2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.25),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Circular Icon Area
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.12),
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.auto_awesome_rounded,
              color: AppColors.primary,
              size: 20,
            ),
          ),
          const SizedBox(width: 12),

          // Assistant Text Area
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AI Assistant',
                  style: AppTypography.labelBold.copyWith(
                    fontSize: 14,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  (widget.item.description != null && widget.item.description!.isNotEmpty)
                      ? widget.item.description!
                      : (widget.item.isPerishable && widget.item.currentStock > _predictedDemand * 1.5)
                          ? 'Current stock of ${widget.item.currentStock} ${widget.item.unit.toLowerCase()} exceeds tomorrow\'s predicted demand of $_predictedDemand. High spoilage risk — monitor afternoon pace.'
                          : 'AI demand projection: $_predictedDemand ${widget.item.unit.toLowerCase()} forecasted tomorrow. Safety stock of $_safetyStock recommended to absorb peak sales swings.',
                  style: AppTypography.bodyMd.copyWith(
                    fontSize: 13,
                    height: 1.45,
                    color: AppColors.onSurface,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRestockFormulaCard() {
    return Container(
      padding: const EdgeInsets.all(20),
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
          color: AppColors.outlineVariant.withValues(alpha: 0.3),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (_hasActiveAlert) ...[
            Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF2F2),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFFFCA5A5)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, size: 20, color: Color(0xFFB91C1C)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Restock held to 0: active waste mitigation alert. Slow-selling inventory prioritized for clearance.',
                      style: GoogleFonts.inter(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: const Color(0xFFB91C1C),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          // Section Heading
          Text(
            'Restock Formula',
            style: AppTypography.headlineMd.copyWith(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.primaryDark,
            ),
          ),
          const SizedBox(height: 16),

          // Row 1: Predicted Demand
          _buildFormulaRow(
            icon: Icons.north_east_rounded,
            iconColor: AppColors.primary,
            label: 'Predicted Demand',
            value: '$_predictedDemand',
          ),
          const SizedBox(height: 12),

          // Row 2: Safety Stock
          _buildFormulaRow(
            icon: Icons.shield_outlined,
            iconColor: AppColors.secondaryAmber,
            label: '+ Safety Stock',
            value: '$_safetyStock',
          ),
          const SizedBox(height: 12),

          // Row 3: Current Stock
          _buildFormulaRow(
            icon: Icons.inventory_2_outlined,
            iconColor: AppColors.onSurfaceVariant,
            label: '- Current Stock',
            value: '$_currentStock',
          ),
          const SizedBox(height: 16),

          Divider(
            color: AppColors.outlineVariant.withValues(alpha: 0.3),
            thickness: 1,
          ),
          const SizedBox(height: 12),

          // Restock Qty Output Row
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text(
                'Restock Qty',
                style: AppTypography.labelBold.copyWith(
                  fontSize: 16,
                  color: AppColors.onSurface,
                ),
              ),
              Text(
                '$_calculatedRestockQty',
                style: AppTypography.headlineLg.copyWith(
                  fontSize: 32,
                  fontWeight: FontWeight.w700,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Restock Confirmed Pill Button
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: (_isRestockConfirmed || _hasActiveAlert || _calculatedRestockQty == 0)
                  ? null
                  : _handleConfirmRestock,
              style: ElevatedButton.styleFrom(
                backgroundColor: _isRestockConfirmed
                    ? AppColors.primary.withValues(alpha: 0.6)
                    : AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                shape: const StadiumBorder(),
                elevation: 0,
              ),
              icon: Icon(
                _isRestockConfirmed
                    ? Icons.check_circle_rounded
                    : Icons.check_rounded,
                size: 20,
              ),
              label: Text(
                _isRestockConfirmed
                    ? 'Restock Confirmed'
                    : (_hasActiveAlert || _calculatedRestockQty == 0
                        ? 'Restock Held to 0'
                        : '✓ Restock Confirmed'),
                style: AppTypography.buttonLabel.copyWith(
                  fontSize: 15,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormulaRow({
    required IconData icon,
    required Color iconColor,
    required String label,
    required String value,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 18,
          color: iconColor,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            label,
            style: AppTypography.bodyMd.copyWith(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: AppColors.onSurface,
            ),
          ),
        ),
        Text(
          value,
          style: AppTypography.labelBold.copyWith(
            fontSize: 16,
            color: AppColors.onSurface,
          ),
        ),
      ],
    );
  }
}
