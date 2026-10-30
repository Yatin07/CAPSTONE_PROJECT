import 'dart:math';
import 'package:flutter/material.dart';
import '../models/inventory_item.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';

class SalesForecastChart extends StatelessWidget {
  final InventoryItem? item;
  final List<double?>? actualSales;
  final List<double>? predictedSales;
  final List<String> days;

  const SalesForecastChart({
    super.key,
    this.item,
    this.actualSales,
    this.predictedSales,
    this.days = const ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  });

  /// 0-indexed day of the week (0 = Mon, 1 = Tue, ..., 4 = Fri, ..., 6 = Sun)
  int get todayIndex {
    final weekday = DateTime.now().weekday; // 1 = Mon, ..., 7 = Sun
    return (weekday - 1).clamp(0, 6);
  }

  String get todayName {
    const names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    return names[todayIndex];
  }

  List<double> get computedPredicted {
    if (predictedSales != null) return predictedSales!;
    if (item != null) {
      final base = (item!.predictedDemand ?? 35).toDouble();
      // Weekday multiplier profile: Mon=0.90, Tue=0.88, Wed=0.92, Thu=0.98, Fri=1.15, Sat=1.25, Sun=1.10
      final multipliers = [0.90, 0.88, 0.92, 0.98, 1.15, 1.25, 1.10];
      return multipliers.map((m) => (base * m).roundToDouble()).toList();
    }
    return const [34, 38, 35, 41, 46, 55, 60];
  }

  List<double?> get computedActual {
    if (actualSales != null) {
      if (actualSales!.length == 7) return actualSales!;
      final result = List<double?>.filled(7, null);
      for (int i = 0; i < min(actualSales!.length, 7); i++) {
        result[i] = actualSales![i];
      }
      return result;
    }

    final result = List<double?>.filled(7, null);

    if (item != null) {
      // Cold-start items with 0 days of completed data have no historical sales points yet
      if (item!.daysOfData <= 0) {
        return result;
      }

      final base = (item!.predictedDemand ?? 35).toDouble();
      final recordedDays = min(item!.daysOfData, todayIndex + 1);
      final multipliers = [0.88, 0.94, 0.90, 0.96, 1.05, 1.15, 1.10];

      // Calendar alignment: actual sales can only exist up to Today (e.g. Saturday)
      // Future days (Sunday) have not occurred yet.
      final endDay = todayIndex;
      final startDay = max(0, endDay - recordedDays + 1);

      for (int day = startDay; day <= endDay; day++) {
        result[day] = (base * multipliers[day % multipliers.length]).roundToDouble();
      }
      return result;
    }

    // Default mock preview: Mon up to Today
    final defaultBase = 35.0;
    final defaultMultipliers = [0.88, 0.94, 0.90, 0.96, 1.05, 1.15, 1.10];
    for (int day = 0; day <= todayIndex; day++) {
      result[day] = (defaultBase * defaultMultipliers[day % defaultMultipliers.length]).roundToDouble();
    }
    return result;
  }

  @override
  Widget build(BuildContext context) {
    final actual = computedActual;
    final predicted = computedPredicted;
    final hasActualData = actual.any((v) => v != null);
    final isColdStart = item != null && item!.daysOfData <= 0;

    return Container(
      padding: const EdgeInsets.all(16),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Section Title, Subtitle & Legend
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            runSpacing: 8,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Sales vs Prediction',
                    style: AppTypography.labelBold.copyWith(
                      fontSize: 16,
                      color: AppColors.primaryDark,
                    ),
                  ),
                  const SizedBox(height: 2),
                  if (isColdStart)
                    Text(
                      'Cold-Start Prior Baseline (Learning)',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppColors.secondaryAmber,
                        fontWeight: FontWeight.w600,
                      ),
                    )
                  else
                    Text(
                      'Sales up to today ($todayName)',
                      style: TextStyle(
                        fontSize: 11,
                        color: AppColors.onSurfaceVariant,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                ],
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (hasActualData) ...[
                    _buildLegendItem('Actual Sales', AppColors.primary),
                    const SizedBox(width: 12),
                  ],
                  _buildLegendItem('Predicted', AppColors.secondaryAmber),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Custom Painted Line Chart
          SizedBox(
            height: 160,
            width: double.infinity,
            child: CustomPaint(
              painter: _SalesChartPainter(
                actualSales: actual,
                predictedSales: predicted,
                days: days,
                todayIndex: todayIndex,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: AppTypography.bodyMd.copyWith(
            fontSize: 11,
            fontWeight: FontWeight.w500,
            color: AppColors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}

class _SalesChartPainter extends CustomPainter {
  final List<double?> actualSales;
  final List<double> predictedSales;
  final List<String> days;
  final int todayIndex;

  _SalesChartPainter({
    required this.actualSales,
    required this.predictedSales,
    required this.days,
    required this.todayIndex,
  });

  @override
  void paint(Canvas canvas, Size size) {
    const double bottomPadding = 26.0;
    const double topPadding = 12.0;
    const double leftPadding = 12.0;
    const double rightPadding = 12.0;

    final double chartWidth = size.width - leftPadding - rightPadding;
    final double chartHeight = size.height - topPadding - bottomPadding;

    final actualNonNull = actualSales.whereType<double>().toList();
    final allVals = [...actualNonNull, ...predictedSales];
    final double maxVal = allVals.isEmpty ? 50.0 : allVals.reduce(max);
    final double maxY = max(10.0, (maxVal * 1.25).ceilToDouble());
    const double minY = 0.0;

    // Draw horizontal grid lines
    final gridPaint = Paint()
      ..color = AppColors.outlineVariant.withValues(alpha: 0.25)
      ..strokeWidth = 1.0;

    const int gridCount = 4;
    for (int i = 0; i <= gridCount; i++) {
      final y = topPadding + (chartHeight / gridCount) * i;
      canvas.drawLine(
        Offset(leftPadding, y),
        Offset(size.width - rightPadding, y),
        gridPaint,
      );
    }

    final double xStep = chartWidth / (days.length - 1);

    // Subtle vertical indicator line at Today
    if (todayIndex >= 0 && todayIndex < days.length) {
      final todayX = leftPadding + todayIndex * xStep;
      final todayLinePaint = Paint()
        ..color = AppColors.primary.withValues(alpha: 0.15)
        ..strokeWidth = 1.5
        ..style = PaintingStyle.stroke;
      canvas.drawLine(
        Offset(todayX, topPadding),
        Offset(todayX, topPadding + chartHeight),
        todayLinePaint,
      );
    }

    // Draw Day Labels at Bottom with Today highlighted
    final defaultTextStyle = TextStyle(
      fontSize: 11,
      fontFamily: 'Inter',
      fontWeight: FontWeight.w500,
      color: AppColors.onSurfaceVariant,
    );

    final todayTextStyle = TextStyle(
      fontSize: 11,
      fontFamily: 'Inter',
      fontWeight: FontWeight.w700,
      color: AppColors.primary,
    );

    for (int i = 0; i < days.length; i++) {
      final x = leftPadding + i * xStep;
      final isToday = i == todayIndex;
      final textPainter = TextPainter(
        text: TextSpan(
          text: days[i],
          style: isToday ? todayTextStyle : defaultTextStyle,
        ),
        textDirection: TextDirection.ltr,
      )..layout();

      textPainter.paint(
        canvas,
        Offset(x - textPainter.width / 2, size.height - bottomPadding + 6),
      );

      // Draw a small dot under Today
      if (isToday) {
        final dotPaint = Paint()
          ..color = AppColors.primary
          ..style = PaintingStyle.fill;
        canvas.drawCircle(
          Offset(x, size.height - bottomPadding + 22),
          2.0,
          dotPaint,
        );
      }
    }

    // Helper to calculate Y offset
    double getYOffset(double val) {
      final normalized = (val - minY) / (maxY - minY);
      return topPadding + chartHeight * (1.0 - normalized);
    }

    // Draw Predicted Sales Line (Soft Amber)
    if (predictedSales.isNotEmpty) {
      final predictedPath = Path();
      final predictedPaint = Paint()
        ..color = AppColors.secondaryAmber
        ..strokeWidth = 2.5
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      final dotPaint = Paint()
        ..color = AppColors.secondaryAmber
        ..style = PaintingStyle.fill;

      for (int i = 0; i < predictedSales.length; i++) {
        final x = leftPadding + i * xStep;
        final y = getYOffset(predictedSales[i]);
        if (i == 0) {
          predictedPath.moveTo(x, y);
        } else {
          predictedPath.lineTo(x, y);
        }
      }
      canvas.drawPath(predictedPath, predictedPaint);

      for (int i = 0; i < predictedSales.length; i++) {
        final x = leftPadding + i * xStep;
        final y = getYOffset(predictedSales[i]);
        canvas.drawCircle(Offset(x, y), 3.5, dotPaint);
      }
    }

    // Draw Actual Sales (Forest Green) aligned to days
    if (actualNonNull.isNotEmpty) {
      final actualPath = Path();
      final actualPaint = Paint()
        ..color = AppColors.primary
        ..strokeWidth = 3.0
        ..style = PaintingStyle.stroke
        ..strokeCap = StrokeCap.round;

      final dotPaint = Paint()
        ..color = AppColors.primary
        ..style = PaintingStyle.fill;

      final dotBorderPaint = Paint()
        ..color = AppColors.cardSurface
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5;

      int? lastValidIndex;
      for (int i = 0; i < actualSales.length; i++) {
        final val = actualSales[i];
        if (val == null) {
          lastValidIndex = null;
          continue;
        }
        final x = leftPadding + i * xStep;
        final y = getYOffset(val);

        if (lastValidIndex != null && lastValidIndex == i - 1) {
          actualPath.lineTo(x, y);
        } else {
          actualPath.moveTo(x, y);
        }
        lastValidIndex = i;
      }
      canvas.drawPath(actualPath, actualPaint);

      for (int i = 0; i < actualSales.length; i++) {
        final val = actualSales[i];
        if (val == null) continue;
        final x = leftPadding + i * xStep;
        final y = getYOffset(val);
        canvas.drawCircle(Offset(x, y), 5.0, dotPaint);
        canvas.drawCircle(Offset(x, y), 5.0, dotBorderPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SalesChartPainter oldDelegate) {
    return oldDelegate.actualSales != actualSales ||
        oldDelegate.predictedSales != predictedSales ||
        oldDelegate.days != days ||
        oldDelegate.todayIndex != todayIndex;
  }
}
