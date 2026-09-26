import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';

class CustomDropdown<T> extends StatelessWidget {
  final String label;
  final String hintText;
  final T? value;
  final List<T> items;
  final String Function(T) itemLabelBuilder;
  final ValueChanged<T?> onChanged;
  final String? Function(T?)? validator;

  const CustomDropdown({
    super.key,
    required this.label,
    required this.hintText,
    required this.value,
    required this.items,
    required this.itemLabelBuilder,
    required this.onChanged,
    this.validator,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTypography.labelBold,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 6),
        DropdownButtonFormField<T>(
          initialValue: value,
          items: items.map((item) {
            return DropdownMenuItem<T>(
              value: item,
              child: Text(
                itemLabelBuilder(item),
                style: AppTypography.bodyMd.copyWith(color: AppColors.onSurface),
              ),
            );
          }).toList(),
          onChanged: onChanged,
          validator: validator,
          icon: const Icon(
            Icons.keyboard_arrow_down_rounded,
            color: AppColors.onSurfaceVariant,
            size: 24,
          ),
          dropdownColor: AppColors.cardSurface,
          style: AppTypography.bodyMd.copyWith(color: AppColors.onSurface),
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: AppTypography.bodyMd.copyWith(
              color: AppColors.outlineVariant,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
        ),
      ],
    );
  }
}
