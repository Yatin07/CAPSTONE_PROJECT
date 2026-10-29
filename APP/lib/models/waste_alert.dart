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
  final Map<String, dynamic>? partnerItem;
  final double? bundleDiscountPct;
  final double? salesPaceRatio;

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
    this.partnerItem,
    this.bundleDiscountPct,
    this.salesPaceRatio,
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
    Map<String, dynamic>? partnerItem,
    double? bundleDiscountPct,
    double? salesPaceRatio,
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
      partnerItem: partnerItem ?? this.partnerItem,
      bundleDiscountPct: bundleDiscountPct ?? this.bundleDiscountPct,
      salesPaceRatio: salesPaceRatio ?? this.salesPaceRatio,
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

    final isBundle = (json['recommendedActionText'] ?? '')
        .toString()
        .toLowerCase()
        .contains('bundle');

    return WasteAlert(
      id: json['id']?.toString() ?? '',
      itemName: json['itemName']?.toString() ?? '',
      salesText: json['salesText']?.toString() ?? '',
      progress: (json['progress'] as num?)?.toDouble() ?? 0.0,
      severityLabel: json['severityLabel']?.toString() ?? 'Low Pace',
      severityColor: parseColor(json['severityColor'], const Color(0xFFB91C1C)),
      recommendedActionText: json['recommendedActionText']?.toString() ?? 'Suggest 10% Discount',
      recommendedActionIcon: isBundle
          ? Icons.layers_outlined
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
      partnerItem: json['partnerItem'] is Map<String, dynamic>
          ? json['partnerItem'] as Map<String, dynamic>
          : (json['partnerItem'] is Map ? Map<String, dynamic>.from(json['partnerItem'] as Map) : null),
      bundleDiscountPct: (json['bundleDiscountPct'] as num?)?.toDouble(),
      salesPaceRatio: (json['salesPaceRatio'] as num?)?.toDouble(),
    );
  }
}
