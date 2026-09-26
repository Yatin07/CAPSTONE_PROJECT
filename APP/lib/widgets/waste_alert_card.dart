import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/waste_alert.dart';
import '../theme/app_colors.dart';

class WasteAlertCard extends StatelessWidget {
  final WasteAlert alert;
  final VoidCallback onRecommendTap;
  final VoidCallback onPrimaryTap;
  final VoidCallback onDismissTap;

  const WasteAlertCard({
    super.key,
    required this.alert,
    required this.onRecommendTap,
    required this.onPrimaryTap,
    required this.onDismissTap,
  });

  @override
  Widget build(BuildContext context) {
    final isStacked = alert.layoutStyle == WasteAlertCardLayoutStyle.stacked;

    return Padding(
      padding: const EdgeInsets.only(bottom: 20.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // White Alert Card Container
          Container(
            padding: const EdgeInsets.all(20.0),
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
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ROW 1: Item Name (left) + Food Image (right)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        alert.itemName,
                        style: GoogleFonts.montserrat(
                          fontSize: 22,
                          fontWeight: FontWeight.w700,
                          color: AppColors.primaryDark,
                          height: 1.25,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    _buildFoodImage(alert.foodType),
                  ],
                ),
                const SizedBox(height: 8),

                // ROW 2: Expected sales text
                Text(
                  alert.salesText,
                  style: GoogleFonts.inter(
                    fontSize: 14,
                    fontWeight: FontWeight.w400,
                    color: AppColors.onSurfaceVariant,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 16),

                // ROW 3: Progress bar + Severity Label
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: LinearProgressIndicator(
                          value: alert.progress,
                          minHeight: 7,
                          backgroundColor: const Color(0xFFEFECE6),
                          valueColor: AlwaysStoppedAnimation<Color>(
                            alert.severityColor,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      alert.severityLabel,
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        fontWeight: FontWeight.w600,
                        color: alert.severityColor,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // ROW 4: Recommended Action Pill Button
                Align(
                  alignment: Alignment.centerLeft,
                  child: InkWell(
                    onTap: alert.isRecommendedActionDone ? null : onRecommendTap,
                    borderRadius: BorderRadius.circular(24),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 9,
                      ),
                      decoration: BoxDecoration(
                        color: alert.isRecommendedActionDone
                            ? alert.recommendedActionColor.withValues(alpha: 0.85)
                            : alert.recommendedActionColor,
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            alert.isRecommendedActionDone
                                ? Icons.check_circle_outline_rounded
                                : alert.recommendedActionIcon,
                            size: 16,
                            color: alert.recommendedActionColor == const Color(0xFFFFB702)
                                ? const Color(0xFF4A3400)
                                : Colors.white,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            alert.isRecommendedActionDone
                                ? alert.recommendedDoneText
                                : alert.recommendedActionText,
                            style: GoogleFonts.inter(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: alert.recommendedActionColor == const Color(0xFFFFB702)
                                  ? const Color(0xFF4A3400)
                                  : Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          // Action Buttons Below Card
          if (isStacked)
            Column(
              children: [
                _buildPrimaryButton(
                  text: alert.isPrimaryActionDone
                      ? alert.primaryDoneText
                      : alert.primaryActionText,
                  isDone: alert.isPrimaryActionDone,
                  onPressed: alert.isPrimaryActionDone ? null : onPrimaryTap,
                ),
                const SizedBox(height: 8),
                _buildOutlinedButton(
                  text: 'Dismiss',
                  onPressed: onDismissTap,
                ),
              ],
            )
          else
            Row(
              children: [
                Expanded(
                  child: _buildPrimaryButton(
                    text: alert.isPrimaryActionDone
                        ? alert.primaryDoneText
                        : alert.primaryActionText,
                    isDone: alert.isPrimaryActionDone,
                    onPressed: alert.isPrimaryActionDone ? null : onPrimaryTap,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildOutlinedButton(
                    text: 'Dismiss',
                    onPressed: onDismissTap,
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildFoodImage(String foodType) {
    return Container(
      width: 52,
      height: 52,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: const Color(0xFFF7F3EC),
        border: Border.all(
          color: const Color(0xFFE5DFC9),
          width: 1.5,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color.fromRGBO(0, 0, 0, 0.04),
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Center(
        child: foodType == 'croissant'
            ? const Icon(
                Icons.bakery_dining_rounded,
                size: 28,
                color: Color(0xFFB45309),
              )
            : const Icon(
                Icons.pie_chart_outline_rounded,
                size: 28,
                color: Color(0xFFD97706),
              ),
      ),
    );
  }

  Widget _buildPrimaryButton({
    required String text,
    required bool isDone,
    required VoidCallback? onPressed,
  }) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ElevatedButton.styleFrom(
        backgroundColor: isDone ? const Color(0xFF2D5F47) : AppColors.primary,
        foregroundColor: AppColors.onPrimary,
        minimumSize: const Size.fromHeight(48),
        shape: const StadiumBorder(),
        elevation: 0,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (isDone) ...[
            const Icon(Icons.check_rounded, size: 18),
            const SizedBox(width: 6),
          ],
          Text(
            text,
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOutlinedButton({
    required String text,
    required VoidCallback onPressed,
  }) {
    return OutlinedButton(
      onPressed: onPressed,
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.primaryDark,
        minimumSize: const Size.fromHeight(48),
        side: const BorderSide(color: AppColors.primary, width: 1.2),
        shape: const StadiumBorder(),
      ),
      child: Text(
        text,
        style: GoogleFonts.inter(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: AppColors.primaryDark,
        ),
      ),
    );
  }
}
