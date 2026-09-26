import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/inventory_item.dart';
import '../providers/inventory_provider.dart';
import '../theme/app_colors.dart';
import '../theme/app_typography.dart';
import '../widgets/custom_dropdown.dart';
import '../widgets/custom_input.dart';
import '../widgets/dotted_background.dart';
import '../widgets/inventory_item_card.dart';
import '../widgets/primary_button.dart';
import 'dashboard_screen.dart';
import 'item_detail_forecast_screen.dart';

class ItemSetupScreen extends StatefulWidget {
  const ItemSetupScreen({super.key});

  @override
  State<ItemSetupScreen> createState() => _ItemSetupScreenState();
}

class _ItemSetupScreenState extends State<ItemSetupScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _stockController = TextEditingController(text: '0');

  String? _selectedCategory;
  String _selectedUnit = 'Units';
  bool _isPerishable = false;

  final List<String> _categories = [
    'Bakery',
    'Beverage',
    'Food',
    'Dessert',
    'Snack',
    'Other',
  ];

  final List<String> _units = [
    'Units',
    'KG',
    'Liters',
    'Grams',
    'Packs',
  ];

  @override
  void dispose() {
    _nameController.dispose();
    _stockController.dispose();
    super.dispose();
  }

  void _populateForm(InventoryItem item) {
    _nameController.text = item.name;
    _selectedCategory = item.category;
    _selectedUnit = _units.contains(item.unit) ? item.unit : 'Units';
    _stockController.text = item.currentStock.toString();
    _isPerishable = item.isPerishable;
  }

  void _resetForm() {
    _nameController.clear();
    _stockController.text = '0';
    _selectedCategory = null;
    _selectedUnit = 'Units';
    _isPerishable = false;
  }

  void _handleSubmitItem(InventoryProvider provider) {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_selectedCategory == null || _selectedCategory!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a category.'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final name = _nameController.text.trim();
    final stock = int.tryParse(_stockController.text.trim()) ?? 0;

    if (provider.isEditing && provider.editingItem != null) {
      final editingId = provider.editingItem!.id;
      provider.updateItem(
        id: editingId,
        name: name,
        category: _selectedCategory!,
        unit: _selectedUnit,
        currentStock: stock,
        isPerishable: _isPerishable,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Updated "$name" in inventory.'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } else {
      provider.addItem(
        name: name,
        category: _selectedCategory!,
        unit: _selectedUnit,
        currentStock: stock,
        isPerishable: _isPerishable,
      );
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Added "$name" to inventory.'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }

    _resetForm();
    provider.clearEditing();
  }

  void _handleSaveAndContinue(InventoryProvider provider) {
    if (provider.items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please add at least one menu item before continuing.'),
          backgroundColor: AppColors.error,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const DashboardScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final inventoryProvider = Provider.of<InventoryProvider>(context);

    return Scaffold(
      body: DottedBackground(
        child: Column(
          children: [
            // Top Header Bar
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(
                      Icons.arrow_back_ios_new_rounded,
                      color: AppColors.primaryDark,
                      size: 20,
                    ),
                    onPressed: () {
                      if (Navigator.canPop(context)) {
                        Navigator.pop(context);
                      }
                    },
                    tooltip: 'Back',
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'RestockIQ',
                    style: AppTypography.headlineMd.copyWith(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primaryDark,
                    ),
                  ),
                ],
              ),
            ),

            // Scrollable Content
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Main Title
                        Text(
                          'Your Menu Items',
                          style: AppTypography.headlineLg.copyWith(
                            fontSize: 26,
                            color: AppColors.primaryDark,
                          ),
                        ),
                        const SizedBox(height: 6),
                        // Description
                        Text(
                          'Set your initial inventory to start generating\nAI forecasts.',
                          style: AppTypography.bodyMd.copyWith(
                            color: AppColors.onSurfaceVariant,
                            height: 1.4,
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Form Card (Add New Item / Edit Item)
                        Container(
                          padding: const EdgeInsets.all(20),
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
                            border: Border.all(
                              color: AppColors.outlineVariant.withValues(alpha: 0.3),
                            ),
                          ),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Section Header
                                Row(
                                  children: [
                                    Icon(
                                      inventoryProvider.isEditing
                                          ? Icons.edit_rounded
                                          : Icons.add_circle_outline_rounded,
                                      color: AppColors.primary,
                                      size: 22,
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      inventoryProvider.isEditing
                                          ? 'Edit Item'
                                          : 'Add New Item',
                                      style: AppTypography.labelBold.copyWith(
                                        fontSize: 18,
                                        color: AppColors.primary,
                                      ),
                                    ),
                                    if (inventoryProvider.isEditing) ...[
                                      const Spacer(),
                                      GestureDetector(
                                        onTap: () {
                                          _resetForm();
                                          inventoryProvider.clearEditing();
                                        },
                                        child: Text(
                                          'Cancel Edit',
                                          style: AppTypography.linkBold.copyWith(
                                            fontSize: 13,
                                            color: AppColors.error,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                                const SizedBox(height: 18),

                                // Item Name Field
                                CustomInput(
                                  label: 'Item Name',
                                  hintText: 'e.g. Sourdough Loaf',
                                  controller: _nameController,
                                  validator: (value) {
                                    if (value == null || value.trim().isEmpty) {
                                      return 'Please enter an item name.';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 16),

                                // Category Dropdown
                                CustomDropdown<String>(
                                  label: 'Category',
                                  hintText: 'Select Category',
                                  value: _selectedCategory,
                                  items: _categories,
                                  itemLabelBuilder: (c) => c,
                                  onChanged: (value) {
                                    setState(() {
                                      _selectedCategory = value;
                                    });
                                  },
                                  validator: (value) {
                                    if (value == null || value.isEmpty) {
                                      return 'Please select a category.';
                                    }
                                    return null;
                                  },
                                ),
                                const SizedBox(height: 16),

                                // Unit & Starting Stock Row
                                Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    // Unit Dropdown
                                    Expanded(
                                      child: CustomDropdown<String>(
                                        label: 'Unit',
                                        hintText: 'Units',
                                        value: _selectedUnit,
                                        items: _units,
                                        itemLabelBuilder: (u) => u,
                                        onChanged: (value) {
                                          if (value != null) {
                                            setState(() {
                                              _selectedUnit = value;
                                            });
                                          }
                                        },
                                      ),
                                    ),
                                    const SizedBox(width: 14),

                                    // Starting Stock Field
                                    Expanded(
                                      child: CustomInput(
                                        label: 'Starting Stock ($_selectedUnit)',
                                        hintText: '0',
                                        controller: _stockController,
                                        keyboardType: TextInputType.number,
                                        validator: (value) {
                                          if (value == null || value.trim().isEmpty) {
                                            return 'Enter stock';
                                          }
                                          final parsed = int.tryParse(value.trim());
                                          if (parsed == null || parsed < 0) {
                                            return 'Invalid stock';
                                          }
                                          return null;
                                        },
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 16),

                                // Highly Perishable Toggle
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 14,
                                    vertical: 8,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppColors.inputFill,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Row(
                                    mainAxisAlignment:
                                        MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              'Highly Perishable?',
                                              style: AppTypography.labelBold
                                                  .copyWith(fontSize: 14),
                                            ),
                                            const SizedBox(height: 2),
                                            Text(
                                              'Item expires quickly if left unsold',
                                              style: AppTypography.bodyMd.copyWith(
                                                fontSize: 11,
                                                color: AppColors.onSurfaceVariant,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                      Switch(
                                        value: _isPerishable,
                                        onChanged: (val) {
                                          setState(() {
                                            _isPerishable = val;
                                          });
                                        },
                                        activeThumbColor: AppColors.primary,
                                        activeTrackColor: AppColors.primary
                                            .withValues(alpha: 0.25),
                                        inactiveThumbColor: AppColors.outlineVariant,
                                        inactiveTrackColor: AppColors.cardSurface,
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 20),

                                // Add to List / Update Item Button
                                Align(
                                  alignment: Alignment.centerRight,
                                  child: SizedBox(
                                    width: 160,
                                    height: 44,
                                    child: ElevatedButton.icon(
                                      onPressed: () =>
                                          _handleSubmitItem(inventoryProvider),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: AppColors.primary,
                                        foregroundColor: AppColors.onPrimary,
                                        shape: const StadiumBorder(),
                                        elevation: 0,
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 16,
                                        ),
                                      ),
                                      icon: Icon(
                                        inventoryProvider.isEditing
                                            ? Icons.check_rounded
                                            : Icons.add_rounded,
                                        size: 18,
                                      ),
                                      label: Text(
                                        inventoryProvider.isEditing
                                            ? 'Update Item'
                                            : 'Add to List',
                                        style: AppTypography.buttonLabel.copyWith(
                                          fontSize: 14,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 28),

                        // Current Inventory Section Title
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Current Inventory',
                              style: AppTypography.headlineMd.copyWith(
                                fontSize: 20,
                                color: AppColors.primaryDark,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 12,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: AppColors.primary.withValues(alpha: 0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '${inventoryProvider.itemCount} Items',
                                style: AppTypography.labelBold.copyWith(
                                  fontSize: 13,
                                  color: AppColors.primary,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 14),

                        // Inventory Items List
                        if (inventoryProvider.items.isEmpty)
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(24),
                            decoration: BoxDecoration(
                              color: AppColors.cardSurface,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Column(
                              children: [
                                const Icon(
                                  Icons.inventory_2_outlined,
                                  size: 40,
                                  color: AppColors.outlineVariant,
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'No inventory items added yet.',
                                  style: AppTypography.bodyMd,
                                ),
                              ],
                            ),
                          )
                        else
                          ...inventoryProvider.items.map((item) {
                            return InventoryItemCard(
                              item: item,
                              onEdit: () {
                                inventoryProvider.startEditing(item);
                                _populateForm(item);
                              },
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (context) =>
                                        ItemDetailForecastScreen(item: item),
                                  ),
                                );
                              },
                            );
                          }),

                        const SizedBox(height: 24),

                        // Save & Continue Button
                        PrimaryButton(
                          label: 'Save & Continue →',
                          onPressed: () =>
                              _handleSaveAndContinue(inventoryProvider),
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
