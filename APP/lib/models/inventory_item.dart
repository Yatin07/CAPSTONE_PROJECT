import 'dart:math';

class InventoryItem {
  final String id;
  final String name;
  final String category;
  final String unit;
  final int currentStock;
  final bool isPerishable;
  final double? price;
  final int? predictedDemand;
  final int? safetyStock;
  final DateTime updatedAt;
  final String? description;
  final String? riskLevel;

  const InventoryItem({
    required this.id,
    required this.name,
    required this.category,
    required this.unit,
    required this.currentStock,
    required this.isPerishable,
    this.price,
    this.predictedDemand,
    this.safetyStock,
    required this.updatedAt,
    this.description,
    this.riskLevel,
  });

  int get restockQuantity {
    final demand = predictedDemand ?? 0;
    final safety = safetyStock ?? 0;
    return max(0, demand + safety - currentStock);
  }

  double get stockProgress {
    final forecastNeed = (predictedDemand ?? 0) + (safetyStock ?? 0);
    if (forecastNeed <= 0) return 1.0;
    return (currentStock / forecastNeed).clamp(0.0, 1.0);
  }

  InventoryItem copyWith({
    String? id,
    String? name,
    String? category,
    String? unit,
    int? currentStock,
    bool? isPerishable,
    double? price,
    int? predictedDemand,
    int? safetyStock,
    DateTime? updatedAt,
    String? description,
    String? riskLevel,
  }) {
    return InventoryItem(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      unit: unit ?? this.unit,
      currentStock: currentStock ?? this.currentStock,
      isPerishable: isPerishable ?? this.isPerishable,
      price: price ?? this.price,
      predictedDemand: predictedDemand ?? this.predictedDemand,
      safetyStock: safetyStock ?? this.safetyStock,
      updatedAt: updatedAt ?? this.updatedAt,
      description: description ?? this.description,
      riskLevel: riskLevel ?? this.riskLevel,
    );
  }

  String get formattedUpdatedTime {
    final diff = DateTime.now().difference(updatedAt);
    if (diff.inMinutes < 60) {
      final mins = diff.inMinutes <= 0 ? 1 : diff.inMinutes;
      return 'Updated ${mins}m ago';
    } else if (diff.inHours < 24) {
      return 'Updated ${diff.inHours}h ago';
    } else {
      return 'Updated ${diff.inDays}d ago';
    }
  }
}

