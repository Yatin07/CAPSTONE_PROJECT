import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def generate_formal_architecture():
    # 16:9 canvas at 300 DPI for presentation
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette: Formal Academic Black & White / Grayscale
    c_white = "#FFFFFF"
    c_gray_light = "#F8F9FA"
    c_gray_box = "#F1F3F5"
    c_gray_border = "#CED4DA"
    c_border_dark = "#212529"
    c_text_main = "#000000"
    c_text_sub = "#212529"
    c_arrow = "#000000"

    fig.patch.set_facecolor(c_white)

    def draw_band(x, y, w, h, title):
        # Outer enclosing band
        band = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                              fc=c_white, ec=c_border_dark, lw=1.5, zorder=1)
        ax.add_patch(band)
        # Header banner on left/top
        hh = 3.8
        banner = FancyBboxPatch((x, y + h - hh), w, hh, boxstyle="square,pad=0",
                                fc=c_gray_box, ec=c_border_dark, lw=1.2, zorder=2)
        ax.add_patch(banner)
        ax.text(x + 1.5, y + h - hh / 2, title, ha='left', va='center',
                fontsize=11.5, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans', zorder=3)

    def draw_card(x, y, w, h, title="", lines=[], bg=c_white, ec=c_border_dark, lw=1.2):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=0.4",
                              fc=bg, ec=ec, lw=lw, zorder=3)
        ax.add_patch(card)
        if title:
            ax.text(x + w / 2, y + h - 1.6, title, ha='center', va='top',
                    fontsize=10.5, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans', zorder=4)
            # Divider line below title
            ax.plot([x + 0.8, x + w - 0.8], [y + h - 3.2, y + h - 3.2], color=c_gray_border, lw=0.8, zorder=4)
        
        if lines:
            line_y = y + h - 4.4
            spacing = (h - 5.0) / max(len(lines), 1)
            for idx, line in enumerate(lines):
                ax.text(x + w / 2, line_y - idx * spacing, line, ha='center', va='center',
                        fontsize=9.0, color=c_text_sub, fontfamily='DejaVu Sans', zorder=4)

    def draw_arrow(x1, y1, x2, y2, label="", label_pos=0.5, label_offset=(0, 1.2), lw=1.4):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=c_arrow, lw=lw,
                                    shrinkA=2, shrinkB=2, mutation_scale=14),
                    zorder=5)
        if label:
            lx = x1 + (x2 - x1) * label_pos + label_offset[0]
            ly = y1 + (y2 - y1) * label_pos + label_offset[1]
            ax.text(lx, ly, label, ha='center', va='center', fontsize=8.5,
                    fontweight='bold', color=c_text_main, zorder=6, fontfamily='DejaVu Sans',
                    bbox=dict(boxstyle="square,pad=0.2", fc=c_white, ec=c_gray_border, lw=0.8))

    # =========================================================================
    # 0. MAIN TITLE
    # =========================================================================
    ax.text(50, 97.5, "RestockIQ: Production System Architecture", ha='center', va='center',
            fontsize=15, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans')
    ax.text(50, 95.3, "Decoupled Cloud-to-Mobile Microservice, Multi-Tier Adaptive Forecasting & Stochastic Newsvendor Decision Support",
            ha='center', va='center', fontsize=9.5, color=c_text_sub, fontfamily='DejaVu Sans')

    # =========================================================================
    # LAYER 1: CLIENT & CLOUD INFRASTRUCTURE (Y: 73 to 93)
    # =========================================================================
    draw_band(2, 73, 96, 20.5, "1. USER INTERFACE, CLOUD MICROSERVICE & PERSISTENCE LAYER")

    # User
    draw_card(3.5, 74.2, 12, 15, "User Layer",
              ["Store Retailer /", "Artisan Bakery /", "Kirana Manager", "", "(Mobile Operator)"])

    # Mobile App
    draw_card(18.5, 74.2, 23, 15, "Mobile Application Layer",
              ["Flutter Client (Android ARM64)", "• Riverpod State Management", "• Offline Local Cache", "• Daily Closing Count Input", "• Real-Time Restock Dashboard", "• Mid-Day Pace Alerts"])

    # REST API
    draw_card(44.5, 74.2, 27, 15, "FastAPI Cloud Microservice",
              ["Render Cloud Backend (Python 3.10)", "• Authentication Router (JWT / RBAC)", "• Catalog & Items API (COGS & Margins)", "• Sales Ingestion Router (Closing Count)", "• Adaptive Forecast & Newsvendor API", "• Pace Analytics & Midnight Scheduler"])

    # Database
    draw_card(74.5, 74.2, 22, 15, "Database Persistence Layer",
              ["MongoDB Atlas Cloud DB", "• users (Store Profiles)", "• items (Catalog & Priors)", "• daily_sales (Composite Index)", "• forecasts (Winners & Q*)", "(Enforces Idempotency)"])

    # Arrows in Layer 1
    draw_arrow(15.5, 81.7, 18.5, 81.7, label="")
    draw_arrow(41.5, 81.7, 44.5, 81.7, label="HTTPS / JWT", label_pos=0.5, label_offset=(0, 1.2))
    draw_arrow(71.5, 81.7, 74.5, 81.7, label="PyMongo", label_pos=0.5, label_offset=(0, 1.2))

    # =========================================================================
    # LAYER 2: MULTI-TIER ADAPTIVE FORECASTING ENGINE (Y: 47 to 70.5)
    # =========================================================================
    draw_band(2, 47, 96, 23.5, "2. MULTI-TIER ADAPTIVE FORECASTING ENGINE (<1 ms Runtime, Pure Python Stdlib)")

    # Data Input
    draw_card(3.5, 48.2, 15, 18.8, "Sales History",
              ["Store Ground Truth", "Historical Daily Demand", "(Filtered for Outliers", "and Stockouts)", "", "Sample Depth: n days"])

    # Tier 1 & 2 Box
    draw_card(21.5, 48.2, 22, 18.8, "Cold Start & Early History",
              ["Tier 1: Cold Start (n = 0)", "Category Bayesian Priors (μ_cat)", "Empirical Cross-Store Baseline", "", "Tier 2: Early History (1 ≤ n < 5)", "Empirical Bayes Shrinkage:", "ŷ = [n/(n+K)]·ȳ + [K/(n+K)]·μ_cat", "(K = 1, bounds variance)"])

    # Tier 3 Box
    draw_card(46.5, 48.2, 28, 18.8, "Tier 3: Maturing History (n ≥ 5)",
              ["5-Candidate Tournament:", "1. Naive Baseline (y_t-1)", "2. EWMA Smoothing (α = 0.5)", "3. 7-Day Moving Average (MA-7)", "4. Same-Weekday Moving Avg (MA-4)", "5. Adaptive 60/40 Hybrid Blend", "", "5% Churn Margin Guard:", "RMSE_challenger ≤ 0.95 · RMSE_MA7"])

    # Winning Forecast
    draw_card(77.5, 48.2, 19, 18.8, "Optimal Point Forecast",
              ["Winning Point Forecast (ŷ)", "", "Forecast Uncertainty:", "σ = max(1, RMSE)", "", "Properties:", "• Runtime: <1 ms / item", "• Zero Heavy ML Dependencies", "• Smooth Tier Transitions"])

    # Arrows in Layer 2
    draw_arrow(58, 74.2, 11, 67.0, label="Historical Sales", label_pos=0.4, label_offset=(0, 1.2))
    draw_arrow(18.5, 57.6, 21.5, 57.6)
    draw_arrow(43.5, 57.6, 46.5, 57.6)
    draw_arrow(74.5, 57.6, 77.5, 57.6, label="Winner")

    # =========================================================================
    # LAYER 3: STOCHASTIC INVENTORY DECISION LAYER (Y: 23 to 44.5)
    # =========================================================================
    draw_band(2, 23, 96, 21.5, "3. STOCHASTIC INVENTORY OPTIMIZATION LAYER (Newsvendor Model)")

    # Cost Box
    draw_card(3.5, 24.2, 21, 16.8, "Asymmetric Cost Formulation",
              ["Perishable Overage / Underage", "• Underage Cost: Cu = p - c", "• Overage Cost: Co = c (100% loss)", "", "Critical Fractile Ratio:", "CR = Cu / (Cu + Co) = 1 - COGS", "(e.g., CR = 0.60 for COGS = 40%)"])

    # Dynamic Safety Stock
    draw_card(27.5, 24.2, 21, 16.8, "Dynamic Safety Stock (SS)",
              ["Target Normal Fractile:", "z* = Φ^-1(CR)  [≈ 0.253 @ CR=0.60]", "", "Safety Stock Calculation:", "SS = max(1, min(round(3σ),", "round(z* · σ)))", "", "Scaled by Forecast Error σ"])

    # Replenishment Order
    draw_card(51.5, 24.2, 22, 16.8, "Restock Order Target (Q*)",
              ["Single-Period Restock Target:", "Q* = max(0, ŷ + SS - I_current)", "", "Performance Impact:", "• -64.4% Food Waste Cut", "• +16.3% Net Profit Surge", "• 100% Fulfillment Preserved"])

    # Coherence Guard
    draw_card(76.5, 24.2, 20, 16.8, "Hard Coherence Guard",
              ["Sanity Stock Clamp:", "", "If  I_current ≥ ŷ + SS", "⟹  Q* ≡ 0", "", "Prevents over-ordering when", "current inventory already", "satisfies predicted demand"])

    # Arrows in Layer 3
    draw_arrow(87, 48.2, 87, 41.0, label="ŷ, σ")
    draw_arrow(24.5, 32.6, 27.5, 32.6)
    draw_arrow(48.5, 32.6, 51.5, 32.6)
    draw_arrow(73.5, 32.6, 76.5, 32.6)

    # =========================================================================
    # LAYER 4: OPERATIONAL FEEDBACK & EXPLANATIONS (Y: 2.5 to 20.5)
    # =========================================================================
    draw_band(2, 2.5, 96, 18.0, "4. CLOSED-LOOP OPERATIONAL FEEDBACK & GROUNDED DIAGNOSTICS")

    # Closing Count
    draw_card(3.5, 3.7, 30, 13.5, "Daily Closing Count & Zero-Waste Split",
              ["Shift-End Physical Inventory Split:", "• Actual Units Sold (Pure Consumer Demand)", "• Spoiled / Expired Units (Waste Record)", "Eliminates historical sales data contamination,", "ensuring unbiased time-series records."])

    # Pace Check
    draw_card(36.5, 3.7, 30, 13.5, "Real-Time Mid-Day Pace Check",
              ["Intra-Day Sales Velocity Monitoring:", "• Slow Pace Alert (< 0.35): Halts afternoon baking", "• Surge Alert (> 1.20): Early stockout warning", "Enables proactive intra-day waste mitigation", "before day close."])

    # Explanations
    draw_card(69.5, 3.7, 27, 13.5, "Grounded Diagnostic Explanations",
              ["Deterministic Plain-Language Rationales:", "• 'EWMA selected: 12% lower error than 7-day MA'", "• 'Pace alert: sales at 28% of expected noon rate'", "Transparent operational guidance without", "ungrounded LLM hallucinations."])

    # Feedback Arrows
    draw_arrow(18.5, 17.2, 18.5, 74.2, label="Uncontaminated Sales History", label_pos=0.5, label_offset=(-8, 0))
    draw_arrow(83.0, 17.2, 41.5, 74.2, label="Actionable Guidance & Pace Cards", label_pos=0.6, label_offset=(8, 0))

    out_png = r"E:\CAP\Documentation\academic-reviews\RestockIQ_System_Architecture_Current.png"
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor=c_white, edgecolor='none')
    plt.close()
    print(f"Generated clean formal architecture diagram: {out_png}")

if __name__ == "__main__":
    generate_formal_architecture()

