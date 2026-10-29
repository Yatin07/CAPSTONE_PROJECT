class StockCheckEntry {
  final String id;
  final String name;
  final String? category;
  final int suggestedQuantity;
  int actualQuantity;
  bool isAutoCalculated;
  bool isManualOverride;
  final bool isPerishable;
  final int openingStock;
  final int producedOrRestocked;
  final int? closingUnitsLeft;
  final int? soldUnits;
  final int? wasteUnits;
  final String? validationError;

  StockCheckEntry({
    required this.id,
    required this.name,
    this.category,
    required this.suggestedQuantity,
    required this.actualQuantity,
    required this.isAutoCalculated,
    required this.isManualOverride,
    required this.isPerishable,
    this.openingStock = 0,
    this.producedOrRestocked = 0,
    this.closingUnitsLeft,
    this.soldUnits,
    this.wasteUnits,
    this.validationError,
  });

  int get availableStock => openingStock + producedOrRestocked;

  StockCheckEntry copyWith({
    String? id,
    String? name,
    String? category,
    int? suggestedQuantity,
    int? actualQuantity,
    bool? isAutoCalculated,
    bool? isManualOverride,
    bool? isPerishable,
    int? openingStock,
    int? producedOrRestocked,
    int? closingUnitsLeft,
    int? soldUnits,
    int? wasteUnits,
    String? validationError,
  }) {
    return StockCheckEntry(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      suggestedQuantity: suggestedQuantity ?? this.suggestedQuantity,
      actualQuantity: actualQuantity ?? this.actualQuantity,
      isAutoCalculated: isAutoCalculated ?? this.isAutoCalculated,
      isManualOverride: isManualOverride ?? this.isManualOverride,
      isPerishable: isPerishable ?? this.isPerishable,
      openingStock: openingStock ?? this.openingStock,
      producedOrRestocked: producedOrRestocked ?? this.producedOrRestocked,
      closingUnitsLeft: closingUnitsLeft ?? this.closingUnitsLeft,
      soldUnits: soldUnits ?? this.soldUnits,
      wasteUnits: wasteUnits ?? this.wasteUnits,
      validationError: validationError ?? this.validationError,
    );
  }
}
