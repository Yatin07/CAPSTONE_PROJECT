import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/custom_dropdown.dart';
import '../widgets/custom_input.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import 'item_setup_screen.dart';

class StoreSetupScreen extends StatefulWidget {
  const StoreSetupScreen({super.key});

  @override
  State<StoreSetupScreen> createState() => _StoreSetupScreenState();
}

class _StoreSetupScreenState extends State<StoreSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _storeNameController = TextEditingController(text: 'My Bakery');

  String _selectedTimezone = 'Asia/Kolkata';
  double _openingHour = 8.0;
  double _closingHour = 20.0;
  String _selectedCurrency = '₹';
  bool _isLoading = false;
  String? _errorMessage;

  final List<String> _timezones = [
    'Asia/Kolkata',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Dubai',
    'Asia/Singapore',
    'Asia/Tokyo',
    'Australia/Sydney',
    'UTC',
  ];

  final List<String> _currencies = ['₹', '\$', '€', '£'];

  @override
  void dispose() {
    _storeNameController.dispose();
    super.dispose();
  }

  Future<void> _handleSaveStore() async {
    setState(() => _errorMessage = null);

    if (!_formKey.currentState!.validate()) return;

    if (_closingHour <= _openingHour) {
      setState(() {
        _errorMessage = 'Closing hour must be strictly after opening hour.';
      });
      return;
    }

    setState(() => _isLoading = true);

    final success = await ApiService.instance.updateUserProfile(
      storeName: _storeNameController.text.trim(),
      timezone: _selectedTimezone,
      openingHour: _openingHour,
      closingHour: _closingHour,
      currency: _selectedCurrency,
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Store settings configured! Now add your first menu item.'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const ItemSetupScreen(),
        ),
      );
    } else {
      setState(() {
        _errorMessage = 'Failed to save store profile. Please check your internet connection.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DottedBackground(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 440),
              child: Container(
                padding: const EdgeInsets.all(28),
                decoration: BoxDecoration(
                  color: AppColors.cardSurface,
                  borderRadius: BorderRadius.circular(20),
                  boxShadow: const [
                    BoxShadow(
                      color: AppColors.ambientShadow,
                      blurRadius: 20,
                      offset: Offset(0, 4),
                    ),
                  ],
                ),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Center(
                        child: Container(
                          width: 64,
                          height: 64,
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.1),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.storefront_rounded,
                            size: 32,
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),

                      Center(
                        child: Text(
                          'Store Configuration',
                          style: AppTypography.headlineLg,
                        ),
                      ),
                      const SizedBox(height: 6),

                      Center(
                        child: Text(
                          'Set your timezone and operating hours for precise alert pacing.',
                          style: AppTypography.bodyMd.copyWith(color: AppColors.onSurfaceVariant),
                          textAlign: TextAlign.center,
                        ),
                      ),
                      const SizedBox(height: 24),

                      if (_errorMessage != null) ...[
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.error.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.error.withValues(alpha: 0.4)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline_rounded, color: AppColors.error, size: 18),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: AppTypography.captionBold.copyWith(color: AppColors.error),
                                ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Store Name
                      CustomInput(
                        label: 'Store / Bakery Name',
                        hintText: 'e.g. Corner Crumb Bakery',
                        controller: _storeNameController,
                        validator: (val) {
                          if (val == null || val.trim().isEmpty) {
                            return 'Please enter store name';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Timezone Dropdown
                      CustomDropdown<String>(
                        label: 'Store Timezone (IANA)',
                        hintText: 'Select Timezone',
                        value: _selectedTimezone,
                        items: _timezones,
                        itemLabelBuilder: (tz) => tz,
                        onChanged: (val) {
                          if (val != null) setState(() => _selectedTimezone = val);
                        },
                      ),
                      const SizedBox(height: 16),

                      // Hours & Currency Row
                      Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Opening', style: AppTypography.labelBold),
                                const SizedBox(height: 6),
                                DropdownButtonFormField<double>(
                                  initialValue: _openingHour,
                                  decoration: InputDecoration(
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                                  ),
                                  items: List.generate(24, (i) => i.toDouble()).map((h) {
                                    final label = '${h.toInt().toString().padLeft(2, '0')}:00';
                                    return DropdownMenuItem(value: h, child: Text(label, style: const TextStyle(fontSize: 13)));
                                  }).toList(),
                                  onChanged: (val) {
                                    if (val != null) setState(() => _openingHour = val);
                                  },
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Closing', style: AppTypography.labelBold),
                                const SizedBox(height: 6),
                                DropdownButtonFormField<double>(
                                  initialValue: _closingHour,
                                  decoration: InputDecoration(
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                                  ),
                                  items: List.generate(24, (i) => i.toDouble()).map((h) {
                                    final label = '${h.toInt().toString().padLeft(2, '0')}:00';
                                    return DropdownMenuItem(value: h, child: Text(label, style: const TextStyle(fontSize: 13)));
                                  }).toList(),
                                  onChanged: (val) {
                                    if (val != null) setState(() => _closingHour = val);
                                  },
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Currency', style: AppTypography.labelBold),
                                const SizedBox(height: 6),
                                DropdownButtonFormField<String>(
                                  initialValue: _selectedCurrency,
                                  decoration: InputDecoration(
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                                  ),
                                  items: _currencies.map((c) {
                                    return DropdownMenuItem(value: c, child: Text(c, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)));
                                  }).toList(),
                                  onChanged: (val) {
                                    if (val != null) setState(() => _selectedCurrency = val);
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Continue Button
                      PrimaryButton(
                        label: 'Save & Add Catalog Items',
                        icon: Icons.arrow_forward_rounded,
                        isLoading: _isLoading,
                        onPressed: _handleSaveStore,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
