import 'dart:math';
import 'package:flutter/material.dart';
import '../models/inventory_item.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';

class SalesForecastChart extends StatelessWidget {
  final InventoryItem? item;
  final List<double>? actualSales;
  final List<double>? predictedSales;
  final List<String> days;

  const SalesForecastChart({
    super.key,
    this.item,
    this.actualSales,
    this.predictedSales,
    this.days = const ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  });

  List<double> get computedPredicted {
    if (predictedSales != null) return predictedSales!;
    if (item != null) {
      final base = (item!.predictedDemand ?? 35).toDouble();
      final multipliers = [0.90, 0.88, 0.92, 0.98, 1.15, 1.25, 1.10];
      return multipliers.map((m) => (base * m).roundToDouble()).toList();
    }
    return const [34, 38, 35, 41, 46, 55, 60];
  }

  List<double> get computedActual {
    if (actualSales != null) return actualSales!;
    if (item != null) {
      if (item!.daysOfData == 0) {
        return [];
      }
      final base = (item!.predictedDemand ?? 35).toDouble();
      final recordedDays = min(item!.daysOfData, 5);
      final multipliers = [0.88, 0.94, 0.90, 1.02, 1.12];
      return List.generate(
        recordedDays,
        (i) => (base * multipliers[i % multipliers.length]).roundToDouble(),
      );
    }
    return const [35, 40, 32, 42, 48];
  }

  @override
  Widget build(BuildContext context) {
    final actual = computedActual;
    final predicted = computedPredicted;

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
          // Section Title & Legend
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
                  if (item != null && item!.daysOfData == 0)
                    Text(
                      'Initial Category Prior Baseline (Learning)',
                      style: TextStyle(fontSize: 11, color: AppColors.secondaryAmber, fontWeight: FontWeight.w600),
                    ),
                ],
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (actual.isNotEmpty) ...[
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
  final List<double> actualSales;
  final List<double> predictedSales;
  final List<String> days;

  _SalesChartPainter({
    required this.actualSales,
    required this.predictedSales,
    required this.days,
  });

  @override
  void paint(Canvas canvas, Size size) {
    const double bottomPadding = 24.0;
    const double topPadding = 12.0;
    const double leftPadding = 10.0;
    const double rightPadding = 10.0;

    final double chartWidth = size.width - leftPadding - rightPadding;
    final double chartHeight = size.height - topPadding - bottomPadding;

    final allVals = [...actualSales, ...predictedSales];
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

    // Draw Day Labels at Bottom
    final textStyle = TextStyle(
      fontSize: 11,
      fontFamily: 'Inter',
      fontWeight: FontWeight.w500,
      color: AppColors.onSurfaceVariant,
    );

    for (int i = 0; i < days.length; i++) {
      final x = leftPadding + i * xStep;
      final textPainter = TextPainter(
        text: TextSpan(text: days[i], style: textStyle),
        textDirection: TextDirection.ltr,
      )..layout();

      textPainter.paint(
        canvas,
        Offset(x - textPainter.width / 2, size.height - bottomPadding + 6),
      );
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

    // Draw Actual Sales Line (Forest Green)
    if (actualSales.isNotEmpty) {
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

      for (int i = 0; i < actualSales.length; i++) {
        final x = leftPadding + i * xStep;
        final y = getYOffset(actualSales[i]);
        if (i == 0) {
          actualPath.moveTo(x, y);
        } else {
          actualPath.lineTo(x, y);
        }
      }
      canvas.drawPath(actualPath, actualPaint);

      for (int i = 0; i < actualSales.length; i++) {
        final x = leftPadding + i * xStep;
        final y = getYOffset(actualSales[i]);
        canvas.drawCircle(Offset(x, y), 4.5, dotPaint);
        canvas.drawCircle(Offset(x, y), 4.5, dotBorderPaint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant _SalesChartPainter oldDelegate) {
    return oldDelegate.actualSales != actualSales ||
        oldDelegate.predictedSales != predictedSales ||
        oldDelegate.days != days;
  }
}
