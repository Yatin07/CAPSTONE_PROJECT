# RestockIQ: Physical Phone Screenshot Checklist for Black Book

This checklist provides the exact instructions for capturing, naming, and captioning physical mobile device screenshots from the live RestockIQ Flutter app (`RestockIQ-debug.apk` or Android device) for insertion into Chapter 4 / Chapter 5 of the Capstone Project Black Book.

---

| Item No. | Screen Name | Flutter Source File | State / View to Capture | Key Elements to Highlight in Screenshot | Black Book Caption |
|:---:|---|---|---|---|---|
| **SS-01** | **Authentication / Login** | `APP/lib/screens/login_screen.dart` | Clean login screen | RestockIQ branding, email field, password field, Remember Me toggle, and Material 3 primary action button. | *Figure 4.1: RestockIQ Mobile Authentication Screen with JWT Security & Session Persistence.* |
| **SS-02** | **Main Demand Dashboard** | `APP/lib/screens/dashboard_screen.dart` | Morning store opening view | Executive AI Briefing card, total tracked items (5), action required banner ("2 items require restocking"), SKU stock progress indicators, and Learning / Improving / Mature maturity chips. | *Figure 4.2: Main Operational Dashboard displaying Real-Time Point Estimates and Restocking Indicators.* |
| **SS-03** | **Item Detail & Forecast Series** | `APP/lib/screens/item_detail_forecast_screen.dart` | Detail view for Traditional Baguette | Predicted demand (39), safety stock (15), current stock (8), recommended reorder (46), 7-day historical bar chart, and 7-day forecast line. | *Figure 4.3: Item Detail Screen exhibiting 7-Day Historical POS Sales and 7-Day Forward Point Predictions.* |
| **SS-04** | **Real-Time Waste Alerts** | `APP/lib/screens/waste_alerts_screen.dart` | Active afternoon alert list | Low-velocity warning card for Traditional Baguette (40% pace ratio), sales progress ring, "Apply 20% Discount" button, and Dismiss option. | *Figure 4.4: Dynamic Waste Mitigation View displaying Afternoon Markdown Actions for Perishable SKUs.* |
| **SS-05** | **Grounded AI Assistant Modal** | `APP/lib/widgets/ai_briefing_card.dart` | Interactive manager Q&A | Manager query: *"What is the discount on baguette?"* followed by grounded contextual response referencing inventory count and pricing. | *Figure 4.5: Large Language Model Operational Assistant with Zero-Math Grounding and Offline Resilience.* |
| **SS-06** | **Inventory Check-In & Stepper** | `APP/lib/screens/inventory_checkin_screen.dart` | Shift stock verification view | SKU verification list, physical count steppers (+ / -), perishable daily lock indicators, and "Confirm Closing Stock" submission bar. | *Figure 4.6: End-of-Day Physical Inventory Check-In Screen with Non-Perishable Manual Override.* |
| **SS-07** | **Item Setup & Catalog CRUD** | `APP/lib/screens/item_setup_screen.dart` | Add / Edit SKU dialog | Form fields for Item Name, Category dropdown, Unit Price, Baseline Stock, Perishable toggle switch, and immediate Learning maturity status chip. | *Figure 4.7: Inventory Catalog Setup Dialog demonstrating Category Allocation and Perishable Classification.* |
| **SS-08** | **Application Settings** | `APP/lib/screens/settings_screen.dart` | System configuration view | Store operational hours (08:00–20:00), Cloud Gateway URL (`restockiq-backend.onrender.com`), Database sync status, and App Version (v1.0.0). | *Figure 4.8: Application Configuration View exhibiting Cloud Endpoint Settings and Cache Management.* |

---

## Technical Photography & Formatting Guidelines
1. **Resolution:** Capture at native phone resolution (minimum 1080x2400) or high-DPI emulator screenshot.
2. **Device Frames:** Crop cleanly to the phone display boundaries (no external phone bezel or desk background).
3. **Status Bar Cleanliness:** Ensure the Android status bar has full battery and clean Wi-Fi icon (or crop status bar to keep clean 9:16 aspect ratio).
4. **File Storage:** Save PNG files to `Documentation/black-book/assets/screenshots/` named `ss_01_login.png`, `ss_02_dashboard.png`, etc.
