import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

/// Renders atmospheric glows and a subtle dot grid pattern in the background.
class DottedBackground extends StatelessWidget {
  final Widget child;

  const DottedBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Solid Cream base background
        Positioned.fill(
          child: Container(color: AppColors.background),
        ),
        // Soft Top-Right Green Glow
        Positioned(
          top: -100,
          right: -100,
          child: Container(
            width: 350,
            height: 350,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFFC1ECD4).withValues(alpha: 0.35),
            ),
          ),
        ),
        // Soft Bottom-Left Amber Glow
        Positioned(
          bottom: -100,
          left: -100,
          child: Container(
            width: 300,
            height: 300,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: const Color(0xFFFFDEA9).withValues(alpha: 0.35),
            ),
          ),
        ),
        // Subtle Dotted Pattern Custom Painter
        Positioned.fill(
          child: CustomPaint(
            painter: _DotGridPainter(),
          ),
        ),
        // Main Foreground Content
        SafeArea(child: child),
      ],
    );
  }
}

class _DotGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF717973).withValues(alpha: 0.12)
      ..strokeWidth = 1.2
      ..strokeCap = StrokeCap.round;

    const spacing = 24.0;
    for (double x = spacing / 2; x < size.width; x += spacing) {
      for (double y = spacing / 2; y < size.height; y += spacing) {
        canvas.drawCircle(Offset(x, y), 1.0, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
