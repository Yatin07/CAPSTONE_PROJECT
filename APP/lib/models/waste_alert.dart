import 'package:flutter/material.dart';

enum WasteAlertCardLayoutStyle {
  stacked,
  sideBySide,
}

class WasteAlert {
  final String id;
  final String itemName;
  final String salesText;
  final double progress;
  final String severityLabel;
  final Color severityColor;
  final String recommendedActionText;
  final IconData recommendedActionIcon;
  final Color recommendedActionColor;
  final String recommendedDoneText;
  final bool isRecommendedActionDone;
  final String primaryActionText;
  final String primaryDoneText;
  final bool isPrimaryActionDone;
  final bool isDismissed;
  final WasteAlertCardLayoutStyle layoutStyle;
  final String foodType;

  const WasteAlert({
    required this.id,
    required this.itemName,
    required this.salesText,
    required this.progress,
    required this.severityLabel,
    required this.severityColor,
    required this.recommendedActionText,
    required this.recommendedActionIcon,
    required this.recommendedActionColor,
    required this.recommendedDoneText,
    this.isRecommendedActionDone = false,
    required this.primaryActionText,
    required this.primaryDoneText,
    this.isPrimaryActionDone = false,
    this.isDismissed = false,
    required this.layoutStyle,
    required this.foodType,
  });

  WasteAlert copyWith({
    String? id,
    String? itemName,
    String? salesText,
    double? progress,
    String? severityLabel,
    Color? severityColor,
    String? recommendedActionText,
    IconData? recommendedActionIcon,
    Color? recommendedActionColor,
    String? recommendedDoneText,
    bool? isRecommendedActionDone,
    String? primaryActionText,
    String? primaryDoneText,
    bool? isPrimaryActionDone,
    bool? isDismissed,
    WasteAlertCardLayoutStyle? layoutStyle,
    String? foodType,
  }) {
    return WasteAlert(
      id: id ?? this.id,
      itemName: itemName ?? this.itemName,
      salesText: salesText ?? this.salesText,
      progress: progress ?? this.progress,
      severityLabel: severityLabel ?? this.severityLabel,
      severityColor: severityColor ?? this.severityColor,
      recommendedActionText: recommendedActionText ?? this.recommendedActionText,
      recommendedActionIcon: recommendedActionIcon ?? this.recommendedActionIcon,
      recommendedActionColor: recommendedActionColor ?? this.recommendedActionColor,
      recommendedDoneText: recommendedDoneText ?? this.recommendedDoneText,
      isRecommendedActionDone: isRecommendedActionDone ?? this.isRecommendedActionDone,
      primaryActionText: primaryActionText ?? this.primaryActionText,
      primaryDoneText: primaryDoneText ?? this.primaryDoneText,
      isPrimaryActionDone: isPrimaryActionDone ?? this.isPrimaryActionDone,
      isDismissed: isDismissed ?? this.isDismissed,
      layoutStyle: layoutStyle ?? this.layoutStyle,
      foodType: foodType ?? this.foodType,
    );
  }

  factory WasteAlert.fromJson(Map<String, dynamic> json) {
    Color parseColor(dynamic colorVal, Color defaultColor) {
      if (colorVal == null) return defaultColor;
      final str = colorVal.toString().replaceAll('#', '');
      try {
        if (str.length == 6) {
          return Color(int.parse('0xFF$str'));
        } else if (str.length == 8) {
          return Color(int.parse('0x$str'));
        }
      } catch (_) {}
      return defaultColor;
    }

    final isSideBySide = json['layoutStyle'] == 'sideBySide';
    final layout = isSideBySide
        ? WasteAlertCardLayoutStyle.sideBySide
        : WasteAlertCardLayoutStyle.stacked;

    final hasDonation = (json['recommendedActionText'] ?? '')
        .toString()
        .toLowerCase()
        .contains('donation');

    return WasteAlert(
      id: json['id']?.toString() ?? '',
      itemName: json['itemName']?.toString() ?? '',
      salesText: json['salesText']?.toString() ?? '',
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      severityLabel: json['severityLabel']?.toString() ?? 'Low Pace',
      severityColor: parseColor(json['severityColor'], const Color(0xFFB91C1C)),
      recommendedActionText: json['recommendedActionText']?.toString() ?? 'Suggest 20% Discount',
      recommendedActionIcon: hasDonation
          ? Icons.volunteer_activism_outlined
          : Icons.local_offer_outlined,
      recommendedActionColor: parseColor(json['recommendedActionColor'], const Color(0xFF8B1E22)),
      recommendedDoneText: json['recommendedDoneText']?.toString() ?? 'Action Taken',
      isRecommendedActionDone: json['isRecommendedActionDone'] == true,
      primaryActionText: json['primaryActionText']?.toString() ?? 'Apply Discount',
      primaryDoneText: json['primaryDoneText']?.toString() ?? 'Action Done',
      isPrimaryActionDone: json['isPrimaryActionDone'] == true,
      isDismissed: json['isDismissed'] == true,
      layoutStyle: layout,
      foodType: json['foodType']?.toString() ?? 'croissant',
    );
  }
}

