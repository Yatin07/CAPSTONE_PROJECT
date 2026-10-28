import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/custom_input.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import 'item_setup_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  String _selectedRole = 'owner';
  bool _isPasswordVisible = false;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    setState(() {
      _errorMessage = null;
    });

    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    final name = _nameController.text.trim();
    final email = _emailController.text.trim().toLowerCase();
    final password = _passwordController.text;

    final success = await ApiService.instance.register(
      name,
      email,
      password,
      role: _selectedRole,
    );

    if (!mounted) return;

    if (success) {
      // Sync fresh blank tenant state into providers
      try {
        if (!mounted) return;
        await Provider.of<InventoryProvider>(context, listen: false).fetchDashboardItems();
        if (!mounted) return;
        await Provider.of<WasteAlertsProvider>(context, listen: false).fetchCloudWasteAlerts();
      } catch (_) {}

      if (!mounted) return;
      setState(() {
        _isLoading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Account created! Welcome, $name.'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );

      // Onboarding step: Guide first-time user directly to catalog item setup
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const ItemSetupScreen(),
        ),
      );
    } else {
      setState(() {
        _isLoading = false;
        _errorMessage = 'Registration failed. Email may already be registered.';
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Registration failed. Please check your details or try logging in.'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
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
              constraints: const BoxConstraints(maxWidth: 420),
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
                    children: [
                      // Header Section
                      Text(
                        'Create Account',
                        style: AppTypography.headlineLg,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),

                      // Store Icon Badge
                      Container(
                        width: 68,
                        height: 68,
                        decoration: BoxDecoration(
                          color: AppColors.primary.withValues(alpha: 0.1),
                          shape: BoxShape.circle,
                        ),
                        child: const Center(
                          child: Icon(
                            Icons.storefront_rounded,
                            size: 34,
                            color: AppColors.primary,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),

                      Text(
                        'Join RestockIQ to automate store forecasts & eliminate waste.',
                        style: AppTypography.bodyMd.copyWith(
                          color: AppColors.onSurfaceVariant,
                          height: 1.4,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 20),

                      if (_errorMessage != null) ...[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
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

                      // Full Name / Store Name Input
                      CustomInput(
                        label: 'Full Name / Business Name',
                        hintText: 'e.g. Marie Dubois or Artisanal Bakery',
                        controller: _nameController,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter your name or business name';
                          }
                          if (value.trim().length < 2) {
                            return 'Name must be at least 2 characters';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Email Input
                      CustomInput(
                        label: 'Email Address',
                        hintText: 'manager@store.com',
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return 'Please enter an email';
                          }
                          final emailRegex = RegExp(r'^[\w\.-]+@[\w-]+\.\w{2,}$');
                          if (!emailRegex.hasMatch(value.trim())) {
                            return 'Please enter a valid email address';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Password Input
                      CustomInput(
                        label: 'Password',
                        hintText: '••••••••',
                        controller: _passwordController,
                        isPassword: true,
                        isPasswordVisible: _isPasswordVisible,
                        onTogglePasswordVisibility: () {
                          setState(() {
                            _isPasswordVisible = !_isPasswordVisible;
                          });
                        },
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter a password';
                          }
                          if (value.length < 6) {
                            return 'Password must be at least 6 characters';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),

                      // Role Selection Segment
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Operational Role', style: AppTypography.labelBold),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Expanded(
                                child: ChoiceChip(
                                  label: const Center(child: Text('Store Owner')),
                                  selected: _selectedRole == 'owner',
                                  selectedColor: AppColors.primary.withValues(alpha: 0.12),
                                  labelStyle: TextStyle(
                                    color: _selectedRole == 'owner' ? AppColors.primary : AppColors.onSurface,
                                    fontWeight: FontWeight.w600,
                                  ),
                                  onSelected: (selected) {
                                    if (selected) setState(() => _selectedRole = 'owner');
                                  },
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: ChoiceChip(
                                  label: const Center(child: Text('Manager')),
                                  selected: _selectedRole == 'manager',
                                  selectedColor: AppColors.primary.withValues(alpha: 0.12),
                                  labelStyle: TextStyle(
                                    color: _selectedRole == 'manager' ? AppColors.primary : AppColors.onSurface,
                                    fontWeight: FontWeight.w600,
                                  ),
                                  onSelected: (selected) {
                                    if (selected) setState(() => _selectedRole = 'manager');
                                  },
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Submit Button
                      PrimaryButton(
                        label: 'Create Account',
                        icon: Icons.person_add_rounded,
                        isLoading: _isLoading,
                        onPressed: _handleRegister,
                      ),

                      // Server wake indicator
                      ValueListenableBuilder<bool>(
                        valueListenable: ApiService.isWakingUpServer,
                        builder: (context, isWaking, _) {
                          if (!isWaking) return const SizedBox.shrink();
                          return Container(
                            margin: const EdgeInsets.only(top: 14),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFFF8E7),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: const Color(0xFFFFD580)),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF8A5A00)),
                                  ),
                                ),
                                const SizedBox(width: 10),
                                ValueListenableBuilder<String?>(
                                  valueListenable: ApiService.serverStatusMessage,
                                  builder: (context, msg, _) {
                                    return Text(
                                      msg ?? 'Waking up server...',
                                      style: AppTypography.captionBold.copyWith(
                                        color: const Color(0xFF8A5A00),
                                      ),
                                    );
                                  },
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                      const SizedBox(height: 20),

                      // Return to Login Link
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            'Already have an account? ',
                            style: AppTypography.bodyMd.copyWith(color: AppColors.onSurfaceVariant),
                          ),
                          GestureDetector(
                            onTap: () {
                              Navigator.pop(context);
                            },
                            child: Text(
                              'Login',
                              style: AppTypography.bodyMd.copyWith(
                                color: AppColors.primary,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
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
