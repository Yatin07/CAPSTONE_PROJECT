import 'package:flutter/material.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../screens/dashboard_screen.dart';
import '../screens/inventory_checkin_screen.dart';
import '../screens/waste_alerts_screen.dart';
import '../screens/settings_screen.dart';

class WarmTechBottomNavBar extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int>? onItemTapped;

  const WarmTechBottomNavBar({
    super.key,
    this.selectedIndex = 0,
    this.onItemTapped,
  });

  void _handleTap(BuildContext context, int index) {
    if (onItemTapped != null) {
      onItemTapped!(index);
      return;
    }

    if (index == selectedIndex) return;

    Widget targetScreen;
    switch (index) {
      case 0:
        targetScreen = const DashboardScreen();
        break;
      case 1:
        targetScreen = const InventoryCheckInScreen();
        break;
      case 2:
        targetScreen = const WasteAlertsScreen();
        break;
      case 3:
        targetScreen = const SettingsScreen();
        break;
      default:
        targetScreen = const DashboardScreen();
    }

    Navigator.pushReplacement(
      context,
      PageRouteBuilder(
        pageBuilder: (context, animation1, animation2) => targetScreen,
        transitionDuration: Duration.zero,
        reverseTransitionDuration: Duration.zero,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFF3EFEA),
        border: Border(
          top: BorderSide(
            color: AppColors.outlineVariant.withValues(alpha: 0.25),
          ),
        ),
      ),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildNavItem(
                context,
                index: 0,
                icon: Icons.grid_view_rounded,
                label: 'Dashboard',
              ),
              _buildNavItem(
                context,
                index: 1,
                icon: Icons.assignment_outlined,
                label: 'Check-In',
              ),
              _buildNavItem(
                context,
                index: 2,
                icon: Icons.notifications_none_rounded,
                label: 'Alerts',
                hasBadge: true,
              ),
              _buildNavItem(
                context,
                index: 3,
                icon: Icons.settings_outlined,
                label: 'Settings',
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildNavItem(
    BuildContext context, {
    required int index,
    required IconData icon,
    required String label,
    bool hasBadge = false,
  }) {
    final isSelected = index == selectedIndex;

    if (isSelected) {
      return Container(
        width: 100,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: AppColors.primary,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: AppColors.onPrimary,
              size: 22,
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: AppTypography.bodyMd.copyWith(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.onPrimary,
              ),
            ),
          ],
        ),
      );
    }

    return InkWell(
      onTap: () => _handleTap(context, index),
      borderRadius: BorderRadius.circular(16),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Icon(
                  icon,
                  color: AppColors.onSurface,
                  size: 22,
                ),
                if (hasBadge)
                  Positioned(
                    top: -1,
                    right: -2,
                    child: Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: AppColors.tertiaryCoral,
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: AppTypography.bodyMd.copyWith(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: AppColors.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
