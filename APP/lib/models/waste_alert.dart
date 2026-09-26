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
}
