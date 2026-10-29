import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/dotted_background.dart';
import 'dashboard_screen.dart';
import 'item_setup_screen.dart';
import 'login_screen.dart';
import 'store_setup_screen.dart';
import 'tour_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Map<String, dynamic>? _userProfile;
  bool _isLoadingProfile = false;

  @override
  void initState() {
    super.initState();
    _fetchProfile();
  }

  Future<void> _fetchProfile() async {
    setState(() => _isLoadingProfile = true);
    final profile = await ApiService.instance.fetchUserProfile();
    if (mounted) {
      setState(() {
        _userProfile = profile;
        _isLoadingProfile = false;
      });
    }
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext dialogContext) {
        return AlertDialog(
          backgroundColor: AppColors.cardSurface,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          title: Text(
            'Log Out?',
            style: GoogleFonts.montserrat(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: AppColors.primaryDark,
            ),
          ),
          content: Text(
            'Are you sure you want to log out of RestockIQ?',
            style: GoogleFonts.inter(
              fontSize: 14,
              color: AppColors.onSurfaceVariant,
            ),
          ),
          actionsPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: Text(
                'Cancel',
                style: GoogleFonts.inter(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(dialogContext);
                ApiService.instance.logout();
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(
                    builder: (context) => const LoginScreen(),
                  ),
                  (route) => false,
                );
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: AppColors.onPrimary,
                elevation: 0,
                shape: const StadiumBorder(),
                padding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 10,
                ),
              ),
              child: Text(
                'Log Out',
                style: GoogleFonts.inter(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showCustomServerDialog(BuildContext context) {
    final customUrlController = TextEditingController(text: ApiService.instance.baseUrl);

    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Backend Server Target'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Select server target or enter custom API endpoint:',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            ListTile(
              dense: true,
              leading: const Icon(Icons.cloud_outlined, color: AppColors.primary),
              title: const Text('Render Cloud Live'),
              subtitle: const Text('https://restockiq-backend.onrender.com/api/v1', style: TextStyle(fontSize: 10)),
              onTap: () {
                setState(() {
                  ApiService.instance.baseUrl = 'https://restockiq-backend.onrender.com/api/v1';
                });
                Navigator.pop(dialogCtx);
              },
            ),
            ListTile(
              dense: true,
              leading: const Icon(Icons.flash_on_rounded, color: Colors.green),
              title: const Text('Local Emulator'),
              subtitle: const Text('http://10.0.2.2:8000/api/v1', style: TextStyle(fontSize: 10)),
              onTap: () {
                setState(() {
                  ApiService.instance.baseUrl = 'http://10.0.2.2:8000/api/v1';
                });
                Navigator.pop(dialogCtx);
              },
            ),
            ListTile(
              dense: true,
              leading: const Icon(Icons.laptop_chromebook_rounded, color: Colors.blue),
              title: const Text('Localhost (Web/Desktop)'),
              subtitle: const Text('http://127.0.0.1:8000/api/v1', style: TextStyle(fontSize: 10)),
              onTap: () {
                setState(() {
                  ApiService.instance.baseUrl = 'http://127.0.0.1:8000/api/v1';
                });
                Navigator.pop(dialogCtx);
              },
            ),
            const Divider(height: 20),
            TextField(
              controller: customUrlController,
              decoration: const InputDecoration(
                labelText: 'Custom API Base URL',
                hintText: 'https://...',
                contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() {
                ApiService.instance.baseUrl = ApiService.defaultBaseUrl;
              });
              Navigator.pop(dialogCtx);
            },
            child: const Text('Reset Default'),
          ),
          ElevatedButton(
            onPressed: () {
              final newUrl = customUrlController.text.trim();
              if (newUrl.isNotEmpty) {
                setState(() {
                  ApiService.instance.baseUrl = newUrl;
                });
              }
              Navigator.pop(dialogCtx);
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final storeName = _userProfile?['store_name']?.toString() ?? 'My Store';
    final userName = _userProfile?['name']?.toString() ?? ApiService.instance.userName ?? 'Store Owner';
    final userEmail = _userProfile?['email']?.toString() ?? '';
    final timezone = _userProfile?['timezone']?.toString() ?? 'Asia/Kolkata';
    final currency = _userProfile?['currency']?.toString() ?? '₹';
    final openH = (_userProfile?['opening_hour'] as num?)?.toDouble() ?? 8.0;
    final closeH = (_userProfile?['closing_hour'] as num?)?.toDouble() ?? 20.0;

    return Scaffold(
      bottomNavigationBar: const WarmTechBottomNavBar(selectedIndex: 3),
      body: DottedBackground(
        child: Column(
          children: [
            // Top Header Bar
            SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    IconButton(
                      icon: const Icon(
                        Icons.arrow_back_rounded,
                        color: AppColors.primaryDark,
                        size: 22,
                      ),
                      onPressed: () {
                        if (Navigator.canPop(context)) {
                          Navigator.pop(context);
                        } else {
                          Navigator.pushReplacement(
                            context,
                            MaterialPageRoute(
                              builder: (context) => const DashboardScreen(),
                            ),
                          );
                        }
                      },
                      tooltip: 'Back',
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Settings',
                      style: GoogleFonts.montserrat(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primaryDark,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // Main Content Area
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      children: [
                        // Profile Header Card
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            color: AppColors.cardSurface,
                            borderRadius: BorderRadius.circular(20),
                            boxShadow: const [
                              BoxShadow(
                                color: AppColors.ambientShadow,
                                blurRadius: 14,
                                offset: Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            children: [
                              if (_isLoadingProfile)
                                const LinearProgressIndicator(minHeight: 2),
                              Container(
                                width: 64,
                                height: 64,
                                decoration: BoxDecoration(
                                  color: AppColors.primary.withValues(alpha: 0.12),
                                  shape: BoxShape.circle,
                                ),
                                child: const Center(
                                  child: Icon(
                                    Icons.storefront_rounded,
                                    size: 32,
                                    color: AppColors.primaryDark,
                                  ),
                                ),
                              ),
                              const SizedBox(height: 12),
                              Text(
                                storeName,
                                style: GoogleFonts.montserrat(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.primaryDark,
                                ),
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '$userName • $userEmail',
                                style: AppTypography.bodyMd.copyWith(
                                  fontSize: 13,
                                  color: AppColors.onSurfaceVariant,
                                ),
                                textAlign: TextAlign.center,
                              ),
                              const SizedBox(height: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.inputFill,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  'Timezone: $timezone • Hours: ${openH.toInt()}:00 - ${closeH.toInt()}:00 ($currency)',
                                  style: GoogleFonts.inter(
                                    fontSize: 11,
                                    color: AppColors.onSurfaceVariant,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 20),

                        // Settings Option Cards
                        SettingsOptionCard(
                          icon: Icons.inventory_2_outlined,
                          title: 'Manage Inventory Items',
                          subtitle: 'View and add catalog items',
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const ItemSetupScreen(),
                              ),
                            );
                          },
                        ),

                        const SizedBox(height: 12),

                        SettingsOptionCard(
                          icon: Icons.storefront_outlined,
                          title: 'Store Configuration',
                          subtitle: 'Operating hours, timezone, and currency',
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const StoreSetupScreen(),
                              ),
                            ).then((_) => _fetchProfile());
                          },
                        ),

                        const SizedBox(height: 12),

                        SettingsOptionCard(
                          icon: Icons.tour_outlined,
                          title: 'Replay Tour',
                          subtitle: 'Explore sample data tour mode',
                          onTap: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => const TourScreen(isReplay: true),
                              ),
                            );
                          },
                        ),

                        if (kDebugMode) ...[
                          const SizedBox(height: 12),
                          SettingsOptionCard(
                            icon: Icons.developer_mode_rounded,
                            title: 'Backend Server Selector (Debug)',
                            subtitle: ApiService.instance.baseUrl,
                            onTap: () => _showCustomServerDialog(context),
                          ),
                        ],

                        const SizedBox(height: 28),

                        // Log Out Action
                        InkWell(
                          onTap: () => _showLogoutDialog(context),
                          borderRadius: BorderRadius.circular(8),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 10,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.logout_rounded, size: 18, color: AppColors.error),
                                const SizedBox(width: 8),
                                Text(
                                  'Log Out',
                                  style: GoogleFonts.inter(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.error,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),

                        const SizedBox(height: 24),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Reusable card component for Settings options.
class SettingsOptionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback? onTap;

  const SettingsOptionCard({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(
            color: AppColors.ambientShadow,
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(icon, color: AppColors.primary, size: 20),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: GoogleFonts.montserrat(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                          color: AppColors.primaryDark,
                        ),
                      ),
                      if (subtitle != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          subtitle!,
                          style: GoogleFonts.inter(
                            fontSize: 12,
                            color: AppColors.onSurfaceVariant,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ],
                  ),
                ),
                trailing ??
                    const Icon(
                      Icons.chevron_right_rounded,
                      color: AppColors.onSurfaceVariant,
                      size: 20,
                    ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
