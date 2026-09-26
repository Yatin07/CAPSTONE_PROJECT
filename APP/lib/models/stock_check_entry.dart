class StockCheckEntry {
  final String id;
  final String name;
  final String? category;
  final int suggestedQuantity;
  int actualQuantity;
  bool isAutoCalculated;
  bool isManualOverride;
  final bool isPerishable;

  StockCheckEntry({
    required this.id,
    required this.name,
    this.category,
    required this.suggestedQuantity,
    required this.actualQuantity,
    required this.isAutoCalculated,
    required this.isManualOverride,
    required this.isPerishable,
  });

  StockCheckEntry copyWith({
    String? id,
    String? name,
    String? category,
    int? suggestedQuantity,
    int? actualQuantity,
    bool? isAutoCalculated,
    bool? isManualOverride,
    bool? isPerishable,
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
    );
  }
}
