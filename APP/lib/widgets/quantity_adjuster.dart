import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../theme/app_colors.dart';

class QuantityAdjuster extends StatelessWidget {
  final int value;
  final ValueChanged<int> onChanged;
  final int minValue;

  const QuantityAdjuster({
    super.key,
    required this.value,
    required this.onChanged,
    this.minValue = 0,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF3EFEA),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppColors.outlineVariant.withValues(alpha: 0.5),
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          _buildButton(
            icon: Icons.remove,
            onPressed: value > minValue
                ? () => onChanged(value - 1)
                : null,
            tooltip: 'Decrease quantity',
          ),
          Container(
            constraints: const BoxConstraints(minWidth: 32),
            alignment: Alignment.center,
            child: Text(
              '$value',
              style: GoogleFonts.montserrat(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: AppColors.primaryDark,
              ),
            ),
          ),
          _buildButton(
            icon: Icons.add,
            onPressed: () => onChanged(value + 1),
            tooltip: 'Increase quantity',
          ),
        ],
      ),
    );
  }

  Widget _buildButton({
    required IconData icon,
    required VoidCallback? onPressed,
    required String tooltip,
  }) {
    return SizedBox(
      width: 36,
      height: 36,
      child: IconButton(
        padding: EdgeInsets.zero,
        constraints: const BoxConstraints(
          minWidth: 36,
          minHeight: 36,
        ),
        icon: Icon(
          icon,
          size: 18,
          color: onPressed != null
              ? AppColors.primary
              : AppColors.outlineVariant,
        ),
        onPressed: onPressed,
        tooltip: tooltip,
      ),
    );
  }
}
