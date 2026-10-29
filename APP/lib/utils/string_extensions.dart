extension StringExtensions on String {
  /// Converts a string to Title Case for display purposes.
  /// E.g. "whole milk" -> "Whole Milk", "croissant" -> "Croissant"
  String toTitleCase() {
    if (isEmpty) return this;
    return split(' ')
        .map((word) => word.isEmpty
            ? word
            : word[0].toUpperCase() + word.substring(1).toLowerCase())
        .join(' ');
  }
}

