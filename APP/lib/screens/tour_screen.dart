import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../providers/inventory_provider.dart';
import '../providers/stock_check_provider.dart';
import '../providers/waste_alerts_provider.dart';
import '../repositories/app_repository.dart';
import '../services/api_service.dart';
import '../theme/app_colors.dart';
import '../widgets/dotted_background.dart';
import '../widgets/primary_button.dart';
import 'dashboard_screen.dart';
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
  String? _seedingError;

  final List<Map<String, dynamic>> _steps = [
    // Step 1: Dashboard & Maturity Chips
    {
      'title': 'Intelligent Daily Forecasts',
      'icon': Icons.trending_up_rounded,
      'badge': 'PREDICTIVE REPLENISHMENT',
      'description':
          'RestockIQ uses machine learning to compute optimal restock quantities:\n\nRestock = max(0, Demand + Safety Stock - On Hand)\n\nZero guesswork at opening. Items evolve from Cold-Start (0d) to Improving (18d) to Mature (45+ days).',
      'card': {
        'name': 'Croissants',
        'stock': '30 units on hand',
        'forecast': 'Predicted Demand: 80',
        'safety': 'Safety Stock: 40',
        'action': 'Restock +90 at open',
        'maturity': 'Mature (45 days)',
      },
    },
    // Step 2: Waste Mitigation
    {
      'title': 'Proactive Waste Mitigation',
      'icon': Icons.warning_amber_rounded,
      'badge': 'SMART BUNDLE ACTIONS',
      'description':
          'When mid-day sales pace lags, RestockIQ triggers timely commercial actions:\n\n• Low Pace: 10% promotional markdown\n• Critical Expiry: 20% combo bundle pairing with a top-selling partner item.',
      'card': {
        'name': 'Whole Milk',
        'stock': '4 GAL remaining (pace: 0.25)',
        'forecast': 'Risk: High Spoilage',
        'safety': 'Combo Partner: Croissants',
        'action': 'Apply 20% Bundle (₹6.40 combo)',
        'maturity': 'Improving (18/28 days)',
      },
    },
    // Step 3: Item Detail & Restock Formula
    {
      'title': 'Item Detail & Restock Formula',
      'icon': Icons.inventory_2_rounded,
      'badge': 'SCIENTIFIC REPLENISHMENT',
      'description':
          'Review each item\'s historical sales curve, day-of-week seasonality, and replenish directly from item detail with one tap.\n\nRestock adds units cleanly to daily stock.',
      'card': {
        'name': 'Traditional Baguette',
        'stock': '8 loaf on hand',
        'forecast': 'Predicted Demand: 39',
        'safety': 'Safety Stock: 15',
        'action': 'Restock +46 with 1 tap',
        'maturity': 'Mature (45 days)',
      },
    },
    // Step 4: Mid-Day Count & Clock Simulation
    {
      'title': 'Mid-Day Check & Simulated Clock',
      'icon': Icons.access_time_rounded,
      'badge': 'PROACTIVE INTRADAY TRACKING',
      'description':
          'Capture mid-day shelf counts to compute real-time sales pace.\n\nTap "Simulate 14:30 Clock" below to test how RestockIQ detects lagging pace in the afternoon.',
      'card': {
        'name': 'Simulate Store Clock',
        'stock': 'Current local time: 14:30',
        'forecast': 'Pace Threshold: 0.50 (50% expected sold)',
        'safety': 'Shadow Tenant Clock Control',
        'action': 'Tap below to set 14:30',
        'maturity': 'Interactive Control',
      },
      'hasClockAction': true,
    },
    // Step 5: Closing Routine & Learning Loop
    {
      'title': 'Closing Count & Learning Loop',
      'icon': Icons.checklist_rounded,
      'badge': 'DAILY CLOSING ROUTINE',
      'description':
          'At the end of every store day, record leftover units.\n\n• Sold = Opening + Restocked - Leftover\n• Perishable leftovers become waste (next opening = 0)\n• Feeds yesterday review and self-supervised ML.',
      'card': {
        'name': 'Yesterday Review',
        'stock': 'Croissants: 92% Sell-Through (High)',
        'forecast': 'Baguettes: 78% Sell-Through (Normal)',
        'safety': 'Milk: 35% Sell-Through (Critical)',
        'action': 'Idempotent daily capture',
        'maturity': 'Auto-updating maturity tiers',
      },
    },
    // Step 6: Executive AI Briefing & Chat
    {
      'title': 'Executive AI Briefing & Chat',
      'icon': Icons.psychology_rounded,
      'badge': 'EXECUTIVE INTELLIGENCE',
      'description':
          'Morning briefing provides concise, zero-hallucination operational summaries.\n\nManager assistant answers operational queries with audit-backed calculations (15 queries/day).',
      'card': {
        'name': 'Operational Assistant',
        'stock': 'Daily Query Quota: 15 / day',
        'forecast': 'Model: Gemini 3.5 Flash (with local fallback)',
        'safety': 'Suggested Chips:',
        'action': '"Why is Baguette critical today?"',
        'maturity': 'Cached per date',
      },
    },
    // Step 7: Clean Slate & Production Store
    {
      'title': 'Start My Real Store',
      'icon': Icons.storefront_rounded,
      'badge': 'CLEAN SLATE PRODUCTION',
      'description':
          'The demo sandbox was a throwaway environment using sample bakery data.\n\nStarting your store deletes all demo data permanently. Your live store starts 100% fresh and empty.',
      'card': {
        'name': 'Clean Slate Isolation',
        'stock': 'Live store items: 0',
        'forecast': 'Demo data: Deleted upon exit',
        'safety': 'Cryptographic Tenant Isolation',
        'action': 'Start fresh store setup',
        'maturity': 'Zero Residual Data',
      },
    },
  ];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _initTour());
  }

  Future<void> _initTour() async {
    try {
      if (ApiService.instance.isAuthenticated) {
        await ApiService.instance.startDemo();
        if (mounted) {
          Provider.of<InventoryProvider>(context, listen: false).setRepository(LiveRepository());
          Provider.of<WasteAlertsProvider>(context, listen: false).setRepository(LiveRepository());
          Provider.of<StockCheckProvider>(context, listen: false).setRepository(LiveRepository());
        }
      } else {
        _useSampleFallback();
      }
    } catch (e) {
      _seedingError = e.toString();
      _useSampleFallback();
    }
  }

  void _useSampleFallback() {
    if (!mounted) return;
    Provider.of<InventoryProvider>(context, listen: false).setRepository(SampleRepository());
    Provider.of<WasteAlertsProvider>(context, listen: false).setRepository(SampleRepository());
    Provider.of<StockCheckProvider>(context, listen: false).setRepository(SampleRepository());
  }

  Future<void> _handleClockSimulation() async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      if (ApiService.instance.isDemoWorkspace) {
        await ApiService.instance.setDemoClock(14.5);
        messenger.showSnackBar(
          const SnackBar(
            content: Text('Simulated store clock set to 14:30 (Asia/Kolkata). Intraday pace triggers active.'),
            backgroundColor: Color(0xFF2E7D32),
            duration: Duration(seconds: 2),
          ),
        );
      } else {
        messenger.showSnackBar(
          const SnackBar(
            content: Text('Simulated time 14:30 active in offline demo.'),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('Clock simulation error: $e'), backgroundColor: Colors.red),
      );
    }
  }

  Future<void> _finishTour() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: Text(
          'Start My Store',
          style: GoogleFonts.montserrat(fontWeight: FontWeight.w700),
        ),
        content: const Text(
          'Starting your store will delete all sample bakery data. Your live store will start fresh and empty.\n\nReady to proceed?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFD97706),
              foregroundColor: Colors.white,
            ),
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Start My Store'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      if (ApiService.instance.isDemoWorkspace) {
        await ApiService.instance.exitDemo();
      }
    } catch (_) {
      ApiService.instance.setWorkspace(null);
    }

    if (!mounted) return;

    // Reset providers to LiveRepository, live store empty
    Provider.of<InventoryProvider>(context, listen: false).setRepository(LiveRepository());
    Provider.of<WasteAlertsProvider>(context, listen: false).setRepository(LiveRepository());
    Provider.of<StockCheckProvider>(context, listen: false).setRepository(LiveRepository());

    if (widget.isReplay) {
      Navigator.pop(context);
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const StoreSetupScreen()),
      );
    }
  }

  void _openSandboxBakery() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const DashboardScreen()),
    );
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
                  _seedingError != null
                      ? 'Offline sample demonstration. Zero network requests — nothing is saved.'
                      : 'Sample data demonstration. Zero network requests — nothing is saved.',
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
                    final hasClock = step['hasClockAction'] == true;

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

                          if (hasClock) ...[
                            const SizedBox(height: 16),
                            Center(
                              child: ElevatedButton.icon(
                                icon: const Icon(Icons.alarm_on_rounded, size: 18),
                                label: const Text('Simulate 14:30 Clock'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFFD97706),
                                  foregroundColor: Colors.white,
                                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                                ),
                                onPressed: _handleClockSimulation,
                              ),
                            ),
                          ],

                          const SizedBox(height: 16),
                          Center(
                            child: TextButton.icon(
                              icon: const Icon(Icons.open_in_new_rounded, size: 16),
                              label: const Text('Explore Sandbox Bakery (Real Screens)'),
                              onPressed: _openSandboxBakery,
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
                                : (widget.isReplay ? 'Exit Tour' : 'Start My Store'),
                            icon: _currentStep < _steps.length - 1
                                ? Icons.arrow_forward_rounded
                                : Icons.storefront_rounded,
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
