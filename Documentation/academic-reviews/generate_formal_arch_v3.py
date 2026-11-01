import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def create_formal_architecture_v3():
    # 16:9 widescreen canvas at 300 DPI (ideal for slide decks)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette: Clean Formal Academic Black & White / Grayscale
    c_white = "#FFFFFF"
    c_header_bg = "#E5E7EB"    # Slate 200 for layer headers
    c_sub_bg = "#F3F4F6"       # Slate 100 for component title banners
    c_border = "#000000"       # Pure black borders
    c_text_bold = "#000000"    # Pure black text
    c_text_reg = "#1F2937"     # Dark charcoal text

    fig.patch.set_facecolor(c_white)

    # Helper: Draw Layer Enclosure with Header Banner
    def draw_layer_band(x, y, w, h, layer_title):
        # Outer border
        outer = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                               fc=c_white, ec=c_border, lw=1.6, zorder=1)
        ax.add_patch(outer)
        # Header banner
        header_h = 3.6
        header = FancyBboxPatch((x, y + h - header_h), w, header_h, boxstyle="square,pad=0",
                                fc=c_header_bg, ec=c_border, lw=1.2, zorder=2)
        ax.add_patch(header)
        ax.text(x + 1.8, y + h - header_h / 2, layer_title, ha='left', va='center',
                fontsize=11.5, fontweight='bold', color=c_text_bold, fontfamily='DejaVu Sans', zorder=3)

    # Helper: Draw Component Box with Header and Clean Spaced Body
    def draw_component(x, y, w, h, title="", lines=[], title_size=10.0, body_size=8.5, lw=1.2):
        box = FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                             fc=c_white, ec=c_border, lw=lw, zorder=3)
        ax.add_patch(box)
        
        cur_y = y + h
        if title:
            th = 3.2
            t_box = FancyBboxPatch((x, y + h - th), w, th, boxstyle="square,pad=0",
                                   fc=c_sub_bg, ec=c_border, lw=1.0, zorder=4)
            ax.add_patch(t_box)
            ax.text(x + w / 2, y + h - th / 2, title, ha='center', va='center',
                    fontsize=title_size, fontweight='bold', color=c_text_bold,
                    fontfamily='DejaVu Sans', zorder=5)
            cur_y = y + h - th

        if lines:
            available_h = cur_y - y
            n = len(lines)
            # Give comfortable line spacing
            step = available_h / (n + 1)
            for i, line in enumerate(lines):
                ly = cur_y - (i + 1) * step
                is_bold = (line.startswith("•") or line.startswith("CR =") or 
                           line.startswith("Q* =") or line.startswith("SS =") or 
                           line.startswith("Tier ") or line.startswith("5% Churn") or
                           line.startswith("Challenger") or line.startswith("1.") or
                           line.startswith("2.") or line.startswith("3.") or 
                           line.startswith("4.") or line.startswith("5.") or
                           line.startswith("Optimal") or line.startswith("If "))
                weight = 'bold' if is_bold else 'normal'
                size = body_size if not is_bold else body_size + 0.3
                color = c_text_bold if is_bold else c_text_reg
                ax.text(x + w / 2, ly, line, ha='center', va='center',
                        fontsize=size, fontweight=weight, color=color,
                        fontfamily='DejaVu Sans', zorder=5)

    # Helper: Clean Straight Orthogonal Arrows
    def draw_arrow(x1, y1, x2, y2, label="", label_pos=0.5, label_offset=(0, 0), lw=1.4):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=c_border, lw=lw,
                                    shrinkA=1, shrinkB=1, mutation_scale=13),
                    zorder=6)
        if label:
            lx = x1 + (x2 - x1) * label_pos + label_offset[0]
            ly = y1 + (y2 - y1) * label_pos + label_offset[1]
            ax.text(lx, ly, label, ha='center', va='center', fontsize=8.5,
                    fontweight='bold', color=c_text_bold, zorder=7, fontfamily='DejaVu Sans',
                    bbox=dict(boxstyle="square,pad=0.25", fc=c_white, ec=c_border, lw=0.8))

    # =========================================================================
    # 0. MAIN PRESENTATION HEADER
    # =========================================================================
    ax.text(50, 97.6, "RestockIQ: Production System Architecture", ha='center', va='center',
            fontsize=15.5, fontweight='bold', color=c_text_bold, fontfamily='DejaVu Sans')
    ax.text(50, 95.3, "Decoupled Cloud-to-Mobile Microservice, Multi-Tier Adaptive Forecasting & Stochastic Newsvendor Decision Support",
            ha='center', va='center', fontsize=9.5, color=c_text_reg, fontfamily='DejaVu Sans')

    # =========================================================================
    # LAYER 1: CLIENT & CLOUD INFRASTRUCTURE (Y: 74.0 to 93.5)
    # =========================================================================
    draw_layer_band(2, 74.0, 96, 19.5, "1. USER INTERFACE, CLOUD MICROSERVICE & PERSISTENCE LAYER")

    # 1.1 User Layer
    draw_component(3.5, 75.0, 11.5, 14.8, "User Layer",
                   ["Store Retailer /", "Artisan Bakery /", "Kirana Operator", "", "(Mobile User)"],
                   title_size=10, body_size=9)

    # 1.2 Mobile Application (Client)
    draw_component(17.5, 75.0, 22.0, 14.8, "Mobile Application (Client)",
                   ["Flutter App (Android ARM64)", "• Riverpod Reactive State", "• Offline-Tolerant Cache", "• Daily Closing Count UI", "• Real-Time Restock Cards", "• Mid-Day Pace Monitoring"],
                   title_size=10, body_size=8.5)

    # 1.3 Cloud Backend (FastAPI on Render)
    draw_component(42.5, 75.0, 28.0, 14.8, "REST API Backend (FastAPI)",
                   ["Render Cloud Microservice (Python 3.10)", "• Auth & User Management API (JWT)", "• Item Catalog & COGS Configuration API", "• Sales Ingestion Router (Closing Count)", "• Multi-Tier Adaptive Forecast API", "• Stochastic Restock & Pace Analytics API", "• Midnight Batch Forecast Scheduler"],
                   title_size=10, body_size=8.2)

    # 1.4 Database Layer (MongoDB Atlas)
    draw_component(73.5, 75.0, 23.0, 14.8, "Database Layer (MongoDB)",
                   ["MongoDB Atlas Cloud Database", "• users: Store Profiles & Roles", "• items: Catalog, Priors & Unit COGS", "• daily_sales: Composite Unique Index", "  (owner_id, item_id, date)", "• forecasts: Winning Model & Q*"],
                   title_size=10, body_size=8.2)

    # Layer 1 Horizontal Connections
    draw_arrow(15.0, 82.4, 17.5, 82.4)
    draw_arrow(39.5, 82.4, 42.5, 82.4, label="HTTPS / JWT", label_pos=0.5, label_offset=(0, 1.4))
    draw_arrow(70.5, 82.4, 73.5, 82.4, label="PyMongo", label_pos=0.5, label_offset=(0, 1.4))

    # =========================================================================
    # LAYER 2: MULTI-TIER ADAPTIVE FORECASTING ENGINE (Y: 48.5 to 71.5)
    # =========================================================================
    draw_layer_band(2, 48.5, 96, 23.0, "2. MULTI-TIER ADAPTIVE FORECASTING ENGINE (<1 ms Runtime, Pure Python Stdlib)")

    # 2.1 Sales Ingestion
    draw_component(3.5, 49.5, 14.0, 18.2, "Sales Ingestion",
                   ["Historical Daily Sales", "Cleaned Store Ground Truth", "(Filtered for stockouts)", "", "Sample Depth: n days", "Deterministically Masked", "for Store Operating Days"],
                   title_size=10, body_size=8.5)

    # 2.2 Cold Start & Early History (Tier 1 & Tier 2)
    draw_component(20.0, 49.5, 22.0, 18.2, "Cold Start & Early History",
                   ["Tier 1: Cold Start (n = 0 days)", "Category Bayesian Priors (μ_cat)", "Cross-Store Empirical Distribution", "", "Tier 2: Early History (1 ≤ n < 5)", "Empirical Bayesian Shrinkage:", "ŷ = [n/(n+K)]·ȳ + [K/(n+K)]·μ_cat", "Shrinkage Constant: K = 1", "(Dampens Small-Sample Variance)"],
                   title_size=10, body_size=8.2)

    # 2.3 Maturing History Tournament (Tier 3)
    draw_component(44.5, 49.5, 29.5, 18.2, "Tier 3: Maturing History (n ≥ 5)",
                   ["5-Candidate Model Tournament:", "1. Naive Baseline (y_t-1)", "2. EWMA Smoothing (α = 0.5)", "3. 7-Day Moving Average (MA-7)", "4. Same-Weekday Moving Avg (MA-4)", "5. Adaptive 60/40 Hybrid Blend", "", "5% Churn Margin Guard Rule:", "Challenger must beat MA-7 by ≥ 5%", "Eliminates Erratic Model Flipping"],
                   title_size=10, body_size=8.2)

    # 2.4 Optimal Forecast Output
    draw_component(76.5, 49.5, 20.0, 18.2, "Forecasting Output",
                   ["Optimal Point Forecast (ŷ)", "", "Forecast Uncertainty:", "σ = max(1, RMSE_winner)", "", "Engine Performance:", "• Latency: < 1 ms per item", "• Pure Python Standard Library", "• Zero Heavy ML Dependencies"],
                   title_size=10, body_size=8.5)

    # Layer 1 to Layer 2 Vertical Trigger
    draw_arrow(56.5, 75.0, 56.5, 71.5, label="Trigger Forecast", label_pos=0.5, label_offset=(4.2, 0))

    # Layer 2 Internal Horizontal Flow
    draw_arrow(17.5, 58.6, 20.0, 58.6)
    draw_arrow(42.0, 58.6, 44.5, 58.6)
    draw_arrow(74.0, 58.6, 76.5, 58.6, label="Winner", label_pos=0.5, label_offset=(0, 1.4))

    # =========================================================================
    # LAYER 3: STOCHASTIC INVENTORY DECISION LAYER (Y: 25.0 to 46.0)
    # =========================================================================
    draw_layer_band(2, 25.0, 96, 21.0, "3. STOCHASTIC INVENTORY OPTIMIZATION LAYER (Newsvendor Model)")

    # 3.1 Asymmetric Cost Formulation
    draw_component(3.5, 26.0, 21.0, 16.2, "Asymmetric Cost Model",
                   ["Perishable Cost Trade-off", "• Underage Cost: Cu = p - c", "• Overage Cost: Co = c (100% loss)", "", "Critical Fractile Ratio:", "CR = Cu / (Cu + Co) = 1 - COGS", "(e.g., CR = 0.60 for COGS = 40%)"],
                   title_size=10, body_size=8.5)

    # 3.2 Dynamic Safety Stock Calculation
    draw_component(27.0, 26.0, 21.5, 16.2, "Dynamic Safety Stock",
                   ["Target Normal Fractile:", "z* = Φ^-1(CR)  [≈ 0.253 @ CR=0.60]", "", "Safety Stock Formulation:", "SS = max(1, min(round(3σ),", "round(z* · σ)))", "", "Scaled by Forecast Uncertainty σ"],
                   title_size=10, body_size=8.5)

    # 3.3 Replenishment Order Target (Q*)
    draw_component(51.0, 26.0, 22.5, 16.2, "Restock Target (Q*)",
                   ["Single-Period Optimization:", "Q* = max(0, ŷ + SS - I_current)", "", "Empirical Downstream Impact:", "• -64.4% Perishable Waste Cut", "• +16.3% Net Profit Surge", "• 100% Demand Fulfillment"],
                   title_size=10, body_size=8.5)

    # 3.4 Hard Coherence Guard
    draw_component(76.0, 26.0, 20.5, 16.2, "Hard Coherence Guard",
                   ["Sanity Inventory Clamp:", "", "If  I_current ≥ ŷ + SS", "⟹  Q* ≡ 0", "", "Prevents excess ordering when", "existing on-hand stock already", "covers predicted demand"],
                   title_size=10, body_size=8.5)

    # Layer 2 to Layer 3 Vertical Flow
    draw_arrow(86.5, 49.5, 86.5, 46.0, label="ŷ, σ", label_pos=0.5, label_offset=(2.0, 0))

    # Layer 3 Internal Horizontal Flow
    draw_arrow(24.5, 34.1, 27.0, 34.1)
    draw_arrow(48.5, 34.1, 51.0, 34.1)
    draw_arrow(73.5, 34.1, 76.0, 34.1)

    # =========================================================================
    # LAYER 4: CLOSED-LOOP OPERATIONAL FEEDBACK & EXPLANATION (Y: 2.5 to 22.5)
    # =========================================================================
    draw_layer_band(2, 2.5, 96, 20.0, "4. CLOSED-LOOP OPERATIONAL FEEDBACK & GROUNDED DIAGNOSTICS")

    # 4.1 Daily Closing Count & Zero-Waste Split
    draw_component(3.5, 3.5, 29.5, 15.2, "Daily Closing Count & Zero-Waste Split",
                   ["Shift-End Physical Inventory Count:", "• Actual Units Sold (Genuine Customer Demand)", "• Spoiled / Expired Stock (Recorded as Waste)", "", "Eliminates historical data contamination,", "ensuring unbiased time-series records.", "Feeds directly into daily_sales collection."],
                   title_size=10, body_size=8.5)

    # 4.2 Real-Time Mid-Day Pace Check
    draw_component(35.5, 3.5, 30.5, 15.2, "Real-Time Mid-Day Pace Check",
                   ["Intra-Day Sales Velocity Monitoring:", "• Slow Pace Alert (< 0.35): Halts afternoon prep", "• Surge Alert (> 1.20): Stockout early warning", "", "Enables proactive intra-day waste mitigation", "before shift close.", "Visible on Flutter manager dashboard."],
                   title_size=10, body_size=8.5)

    # 4.3 Grounded Diagnostic Explanations
    draw_component(68.5, 3.5, 28.0, 15.2, "Deterministic Diagnostic Engine",
                   ["Transparent Plain-Language Rationales:", "• 'EWMA selected: 12% lower error than 7-day MA'", "• 'Pace alert: sales at 28% of expected noon rate'", "", "Grounded in engine metrics without", "ungrounded LLM hallucinations.", "Delivers actionable advice to mobile cards."],
                   title_size=10, body_size=8.5)

    # Layer 3 to Layer 4 Vertical Flow
    draw_arrow(62.2, 26.0, 62.2, 22.5, label="Q* & Decision Metrics", label_pos=0.5, label_offset=(5.5, 0))

    out_png = r"E:\CAP\Documentation\academic-reviews\RestockIQ_System_Architecture_Current.png"
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor=c_white, edgecolor='none')
    plt.close()
    print(f"Generated clean formal architecture diagram v3: {out_png}")

if __name__ == "__main__":
    create_formal_architecture_v3()

