import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../repositories/app_repository.dart';
import '../theme/app_colors.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import 'store_setup_screen.dart';

class TourScreen extends StatefulWidget {
  final bool isReplay;

  const TourScreen({super.key, this.isReplay = false});

  @override
  State<TourScreen> createState() => _TourScreenState();
}

class _TourScreenState extends State<TourScreen> {
  int _currentStep = 0;
  final PageController _pageController = PageController();

  final List<Map<String, dynamic>> _steps = [
    {
      'title': 'Intelligent Daily Forecasts',
      'icon': Icons.trending_up_rounded,
      'badge': 'PREDICTIVE REPLENISHMENT',
      'description':
          'RestockIQ uses machine learning to compute optimal restock quantities:\n\nRestock = max(0, Demand + Safety Stock - On Hand)\n\nZero guesswork at opening.',
      'card': {
        'name': 'Croissants',
        'stock': '30 units on hand',
        'forecast': 'Predicted Demand: 80',
        'safety': 'Safety Stock: 40',
        'action': 'Restock +90 at open',
        'maturity': 'Mature (45 days)',
      },
    },
    {
      'title': 'Proactive Waste Mitigation',
      'icon': Icons.warning_amber_rounded,
      'badge': 'SMART BUNDLE ACTIONS',
      'description':
          'When mid-day sales pace lags, RestockIQ triggers timely commercial actions:\n\n• Low Pace: 10% promotional markdown\n• Critical Expiry: 20% combo bundle pairing with a top-selling complementary partner item.',
      'card': {
        'name': 'Whole Milk',
        'stock': '4 GAL remaining (pace: 0.25)',
        'forecast': 'Risk: High Spoilage',
        'safety': 'Combo Partner: Croissants',
        'action': 'Apply 20% Bundle (₹6.40 combo)',
        'maturity': 'Improving (18/28 days)',
      },
    },
    {
      'title': 'Closing Count & Learning Loop',
      'icon': Icons.checklist_rounded,
      'badge': 'DAILY CLOSING ROUTINE',
      'description':
          'At the end of every store day, record leftover units.\n\n• Sold = Opening + Restocked - Leftover\n• Perishable leftovers become waste (next opening = 0)\n• Non-perishable items carry over\n\nFeeds yesterday review and ML training.',
      'card': {
        'name': 'Yesterday Review',
        'stock': 'Croissants: 92% Sell-Through (High)',
        'forecast': 'Baguettes: 78% Sell-Through (Normal)',
        'safety': 'Milk: 35% Sell-Through (Critical)',
        'action': 'Idempotent daily capture',
        'maturity': 'Auto-updating maturity tiers',
      },
    },
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      // Set to sample repository for tour experience
      Provider.of<InventoryProvider>(context, listen: false)
          .setRepository(SampleRepository());
      Provider.of<WasteAlertsProvider>(context, listen: false)
          .setRepository(SampleRepository());
    });
  }

  void _finishTour() {
    // ALWAYS switch to LiveRepository when exiting tour, so real user data is used
    Provider.of<InventoryProvider>(context, listen: false)
        .setRepository(LiveRepository());
    Provider.of<WasteAlertsProvider>(context, listen: false)
        .setRepository(LiveRepository());

    if (widget.isReplay) {
      Navigator.pop(context);
    } else {
      // First-time onboarding: proceed to store setup
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => const StoreSetupScreen(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: DottedBackground(
        child: SafeArea(
          child: Column(
            children: [
              // Header with DEMO TOUR badge
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        if (widget.isReplay)
                          IconButton(
                            icon: const Icon(Icons.arrow_back_rounded, color: AppColors.primaryDark),
                            onPressed: _finishTour,
                          ),
                        Text(
                          'Interactive Tour',
                          style: GoogleFonts.montserrat(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                            color: AppColors.primaryDark,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.amber.shade100,
                        border: Border.all(color: Colors.amber.shade700, width: 1.2),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.science_outlined, size: 14, color: Colors.amber.shade900),
                          const SizedBox(width: 4),
                          Text(
                            'DEMO TOUR',
                            style: GoogleFonts.inter(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: Colors.amber.shade900,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // Tour step banner
              Container(
                width: double.infinity,
                margin: const EdgeInsets.symmetric(horizontal: 20),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.primary.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(
                  'Sample data demonstration. Zero network requests — nothing is saved.',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: AppColors.primary,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),

              // Page View
              Expanded(
                child: PageView.builder(
                  controller: _pageController,
                  itemCount: _steps.length,
                  onPageChanged: (idx) {
                    setState(() => _currentStep = idx);
                  },
                  itemBuilder: (context, idx) {
                    final step = _steps[idx];
                    final card = step['card'] as Map<String, dynamic>;

                    return SingleChildScrollView(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Center(
                            child: Container(
                              width: 64,
                              height: 64,
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.12),
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                step['icon'] as IconData,
                                size: 32,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                          const SizedBox(height: 16),

                          Center(
                            child: Text(
                              step['badge'] as String,
                              style: GoogleFonts.inter(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.1,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),

                          Center(
                            child: Text(
                              step['title'] as String,
                              style: GoogleFonts.montserrat(
                                fontSize: 22,
                                fontWeight: FontWeight.w700,
                                color: AppColors.primaryDark,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          const SizedBox(height: 12),

                          Text(
                            step['description'] as String,
                            style: GoogleFonts.inter(
                              fontSize: 14,
                              height: 1.5,
                              color: AppColors.onSurfaceVariant,
                            ),
                          ),
                          const SizedBox(height: 20),

                          // Sample Preview Card
                          Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: AppColors.cardSurface,
                              borderRadius: BorderRadius.circular(16),
                              boxShadow: const [
                                BoxShadow(
                                  color: AppColors.ambientShadow,
                                  blurRadius: 14,
                                  offset: Offset(0, 4),
                                ),
                              ],
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      card['name'] as String,
                                      style: GoogleFonts.montserrat(
                                        fontSize: 16,
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.primaryDark,
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: AppColors.primary.withValues(alpha: 0.1),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        card['maturity'] as String,
                                        style: GoogleFonts.inter(
                                          fontSize: 10,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.primary,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  card['stock'] as String,
                                  style: GoogleFonts.inter(fontSize: 13, color: AppColors.onSurfaceVariant),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  card['forecast'] as String,
                                  style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w500),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  card['safety'] as String,
                                  style: GoogleFonts.inter(fontSize: 13, color: AppColors.onSurfaceVariant),
                                ),
                                const Divider(height: 20),
                                Row(
                                  children: [
                                    const Icon(Icons.bolt_rounded, size: 16, color: Colors.green),
                                    const SizedBox(width: 6),
                                    Expanded(
                                      child: Text(
                                        card['action'] as String,
                                        style: GoogleFonts.inter(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: Colors.green.shade800,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),

              // Indicators & Navigation Buttons
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                child: Column(
                  children: [
                    // Dot indicators
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: List.generate(
                        _steps.length,
                        (i) => Container(
                          margin: const EdgeInsets.symmetric(horizontal: 4),
                          width: _currentStep == i ? 24 : 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: _currentStep == i ? AppColors.primary : AppColors.outlineVariant,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    Row(
                      children: [
                        if (_currentStep > 0)
                          Expanded(
                            child: OutlinedButton(
                              onPressed: () {
                                _pageController.previousPage(
                                  duration: const Duration(milliseconds: 250),
                                  curve: Curves.easeInOut,
                                );
                              },
                              style: OutlinedButton.styleFrom(
                                minimumSize: const Size(0, 48),
                                shape: const StadiumBorder(),
                              ),
                              child: const Text('Previous'),
                            ),
                          ),
                        if (_currentStep > 0) const SizedBox(width: 12),
                        Expanded(
                          flex: 2,
                          child: PrimaryButton(
                            label: _currentStep < _steps.length - 1
                                ? 'Next'
                                : (widget.isReplay ? 'Exit Tour' : 'Set Up My Store'),
                            icon: _currentStep < _steps.length - 1
                                ? Icons.arrow_forward_rounded
                                : Icons.store_rounded,
                            onPressed: () {
                              if (_currentStep < _steps.length - 1) {
                                _pageController.nextPage(
                                  duration: const Duration(milliseconds: 250),
                                  curve: Curves.easeInOut,
                                );
                              } else {
                                _finishTour();
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
