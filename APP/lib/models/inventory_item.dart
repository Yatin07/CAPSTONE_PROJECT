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
  final int daysOfData;
  final String maturity;
  final String maturityLabel;
  final int? shelfLifeDays;
  final bool isReplayedDataset;
  final int? serverRestockQuantity;
  final bool hasActiveAlert;

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
    this.daysOfData = 0,
    this.maturity = 'Learning',
    this.maturityLabel = 'Learning (0/7 days)',
    this.shelfLifeDays,
    this.isReplayedDataset = false,
    this.serverRestockQuantity,
    this.hasActiveAlert = false,
  });

  int get restockQuantity {
    if (serverRestockQuantity != null) return serverRestockQuantity!;
    if (hasActiveAlert) return 0;
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
    int? daysOfData,
    String? maturity,
    String? maturityLabel,
    int? shelfLifeDays,
    bool? isReplayedDataset,
    int? serverRestockQuantity,
    bool? hasActiveAlert,
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
      daysOfData: daysOfData ?? this.daysOfData,
      maturity: maturity ?? this.maturity,
      maturityLabel: maturityLabel ?? this.maturityLabel,
      shelfLifeDays: shelfLifeDays ?? this.shelfLifeDays,
      isReplayedDataset: isReplayedDataset ?? this.isReplayedDataset,
      serverRestockQuantity: serverRestockQuantity ?? this.serverRestockQuantity,
      hasActiveAlert: hasActiveAlert ?? this.hasActiveAlert,
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

  factory InventoryItem.fromJson(Map<String, dynamic> json) {
    DateTime parsedDate;
    try {
      parsedDate = json['updatedAt'] != null && json['updatedAt'].toString().isNotEmpty
          ? DateTime.parse(json['updatedAt'].toString())
          : DateTime.now();
    } catch (_) {
      parsedDate = DateTime.now();
    }

    final dod = (json['daysOfData'] as num?)?.toInt() ?? 0;
    final mat = json['maturity']?.toString() ??
        (dod >= 28 ? 'Mature' : (dod >= 7 ? 'Improving' : 'Learning'));
    final matLbl = json['maturityLabel']?.toString() ??
        (dod >= 28 ? 'Mature ($dod days)' : (dod >= 7 ? 'Improving ($dod/28 days)' : 'Learning ($dod/7 days)'));

    final explicitRestock = (json['restockQuantity'] as num?)?.toInt();
    final hasAlert = json['hasWasteAlert'] == true ||
        (json['description'] != null && json['description'].toString().contains('Restock held to 0'));

    return InventoryItem(
      id: json['id']?.toString() ?? json['_id']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      category: json['category']?.toString() ?? 'Bakery',
      unit: json['unit']?.toString() ?? 'Units',
      currentStock: (json['currentStock'] as num?)?.toInt() ?? 0,
      isPerishable: json['isPerishable'] == true,
      price: (json['price'] as num?)?.toDouble(),
      predictedDemand: (json['predictedDemand'] as num?)?.toInt(),
      safetyStock: (json['safetyStock'] as num?)?.toInt(),
      updatedAt: parsedDate,
      description: json['description']?.toString(),
      riskLevel: json['riskLevel']?.toString() ?? 'normal',
      daysOfData: dod,
      maturity: mat,
      maturityLabel: matLbl,
      shelfLifeDays: (json['shelfLifeDays'] as num?)?.toInt(),
      isReplayedDataset: json['replayed_dataset'] == true || json['isReplayedDataset'] == true,
      serverRestockQuantity: explicitRestock,
      hasActiveAlert: hasAlert,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'category': category,
      'unit': unit,
      'currentStock': currentStock,
      'isPerishable': isPerishable,
      'price': price,
      'predictedDemand': predictedDemand,
      'safetyStock': safetyStock,
      'updatedAt': updatedAt.toIso8601String(),
      'description': description,
      'riskLevel': riskLevel,
      'daysOfData': daysOfData,
      'maturity': maturity,
      'maturityLabel': maturityLabel,
      'shelfLifeDays': shelfLifeDays,
      'replayed_dataset': isReplayedDataset,
      'restockQuantity': restockQuantity,
      'hasWasteAlert': hasActiveAlert,
    };
  }
}
