import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle
import numpy as np

def draw_architecture_diagram():
    # High resolution 16:9 canvas (300 DPI)
    fig, ax = plt.subplots(figsize=(19.2, 10.8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette - Professional Academic / Enterprise
    c_bg = "#F8FAFC"          # Slate 50 background
    c_band_bg = "#FFFFFF"     # Clean white card
    c_border = "#CBD5E1"      # Slate 300
    c_navy = "#0F172A"        # Slate 900
    c_blue = "#1E3A8A"        # Blue 900
    c_teal = "#0D9488"        # Teal 600
    c_indigo = "#4338CA"      # Indigo 700
    c_amber = "#B45309"       # Amber 700
    c_emerald = "#047857"     # Emerald 700
    c_rose = "#BE123C"        # Rose 700
    c_text_dark = "#1E293B"   # Slate 800
    c_text_muted = "#475569"  # Slate 600
    c_arrow = "#334155"       # Slate 700

    fig.patch.set_facecolor(c_bg)

    def draw_box(x, y, w, h, title="", subtitle="", bg="#FFFFFF", border="#94A3B8", 
                 title_color="#0F172A", title_size=11, sub_size=9, radius=0.8, lw=1.2, align='center'):
        p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad={radius},rounding_size={radius}",
                           fc=bg, ec=border, lw=lw, zorder=2)
        ax.add_patch(p)
        if title:
            if subtitle:
                ty = y + h * 0.62
                sy = y + h * 0.28
                tx = x + w / 2 if align == 'center' else x + 1.2
                ax.text(tx, ty, title, ha=align, va='center', fontsize=title_size,
                        fontweight='bold', color=title_color, zorder=3, fontfamily='DejaVu Sans')
                ax.text(tx, sy, subtitle, ha=align, va='center', fontsize=sub_size,
                        fontweight='normal', color=c_text_muted, zorder=3, fontfamily='DejaVu Sans')
            else:
                ax.text(x + w / 2, y + h / 2, title, ha='center', va='center', fontsize=title_size,
                        fontweight='bold', color=title_color, zorder=3, fontfamily='DejaVu Sans')
        return p

    def draw_band(x, y, w, h, title, bg="#FFFFFF", border="#CBD5E1", title_bg="#1E293B", title_color="#FFFFFF"):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=0.5",
                           fc=bg, ec=border, lw=1.2, zorder=1)
        ax.add_patch(p)
        # Left or top badge
        bw, bh = 24, 3.2
        bx, by = x + 0.8, y + h - bh - 0.4
        b_patch = FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.3,rounding_size=0.3",
                                 fc=title_bg, ec="none", zorder=2)
        ax.add_patch(b_patch)
        ax.text(bx + bw / 2, by + bh / 2, title, ha='center', va='center', fontsize=9.5,
                fontweight='bold', color=title_color, zorder=3, fontfamily='DejaVu Sans')

    def draw_arrow(x1, y1, x2, y2, color=c_arrow, lw=1.5, ls='-', label="", label_pos=0.5, label_offset=(0, 1.2)):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=lw, ls=ls,
                                    shrinkA=2, shrinkB=2, mutation_scale=12),
                    zorder=4)
        if label:
            lx = x1 + (x2 - x1) * label_pos + label_offset[0]
            ly = y1 + (y2 - y1) * label_pos + label_offset[1]
            ax.text(lx, ly, label, ha='center', va='center', fontsize=8,
                    fontweight='bold', color=color, zorder=5, fontfamily='DejaVu Sans',
                    bbox=dict(boxstyle="round,pad=0.2", fc="#FFFFFF", ec="none", alpha=0.9))

    # =========================================================================
    # 0. MAIN TITLE & BANNER
    # =========================================================================
    ax.text(50, 97.5, "RestockIQ: Production System Architecture", ha='center', va='center',
            fontsize=17, fontweight='bold', color=c_navy, fontfamily='DejaVu Sans')
    ax.text(50, 95.2, "Decoupled Cloud-to-Mobile Microservice, Multi-Tier Tournament Engine & Stochastic Newsvendor Decision Support",
            ha='center', va='center', fontsize=10.5, color=c_text_muted, fontfamily='DejaVu Sans')

    # =========================================================================
    # 1. USER & MOBILE CLIENT LAYER (Y: 82 to 93)
    # =========================================================================
    draw_band(2, 82.5, 96, 11, "1. USER & MOBILE CLIENT LAYER", bg="#F8FAFC", border="#CBD5E1", title_bg="#0F172A")
    
    # User Box
    draw_box(4, 84, 15, 7.2, "Store Retailer", "Kirana / Bakery Manager",
             bg="#EFF6FF", border="#93C5FD", title_color="#1E3A8A", title_size=11, sub_size=8.5)
    
    # Flutter App Box
    draw_box(26, 83.5, 70, 8.2, "", "", bg="#FFFFFF", border="#3B82F6", lw=1.5)
    ax.text(28, 90, "Flutter Mobile Application (Android ARM64 Production Client)",
            ha='left', va='center', fontsize=10.5, fontweight='bold', color="#1D4ED8", fontfamily='DejaVu Sans', zorder=3)
    
    # Flutter sub-modules
    f_mods = [
        ("Riverpod State", "Deterministic State Flow"),
        ("Offline Cache", "Local Storage Fallback"),
        ("Closing Count UI", "Zero-Waste Separation"),
        ("Pace Monitor UI", "Mid-Day Velocity Alerts"),
        ("Restock Cards", "Actionable Q* Orders")
    ]
    for idx, (m_t, m_s) in enumerate(f_mods):
        draw_box(28 + idx * 13.5, 84.3, 12.5, 4.5, m_t, m_s,
                 bg="#F0FDF4", border="#86EFAC", title_color="#166534", title_size=9, sub_size=7.5)

    draw_arrow(19, 87.6, 26, 87.6, color="#2563EB", lw=2, label="Touch Inputs")

    # =========================================================================
    # 2. CLOUD MICROSERVICE & PERSISTENCE LAYER (Y: 65 to 80.5)
    # =========================================================================
    draw_band(2, 65.5, 96, 15, "2. CLOUD BACKEND & DATA PERSISTENCE LAYER", bg="#F8FAFC", border="#CBD5E1", title_bg="#1E3A8A")

    # FastAPI Cloud Service Box
    draw_box(4, 66.5, 62, 12.2, "", "", bg="#FFFFFF", border="#60A5FA", lw=1.5)
    ax.text(6, 77.2, "FastAPI Microservice (Deployed on Render Cloud, Python 3.10 ASGI)",
            ha='left', va='center', fontsize=10.5, fontweight='bold', color="#1E40AF", fontfamily='DejaVu Sans', zorder=3)
    
    api_mods = [
        ("Auth Router", "JWT Tokens / RBAC"),
        ("Catalog API", "Items & Category Priors"),
        ("Sales Ingestion", "Closing Count Endpoint"),
        ("Forecast Router", "Multi-Tier Tournament"),
        ("Newsvendor API", "Stochastic Restock Q*"),
        ("Pace Analytics", "Intra-Day Pace Check"),
        ("Batch Scheduler", "APScheduler @ Midnight"),
        ("Coherence Guard", "Sanity Stock Clamp")
    ]
    for idx, (a_t, a_s) in enumerate(api_mods):
        row = idx // 4
        col = idx % 4
        draw_box(6 + col * 14.6, 71.8 - row * 4.8, 13.8, 4.2, a_t, a_s,
                 bg="#F8FAFC", border="#94A3B8", title_color="#0F172A", title_size=8.5, sub_size=7.2)

    # MongoDB Atlas Box
    draw_box(70, 66.5, 26, 12.2, "", "", bg="#FFFFFF", border="#10B981", lw=1.5)
    ax.text(72, 77.2, "MongoDB Atlas (Cloud Database)",
            ha='left', va='center', fontsize=10.5, fontweight='bold', color="#047857", fontfamily='DejaVu Sans', zorder=3)
    
    db_colls = [
        ("users", "Store Profiles & Settings"),
        ("items", "Catalog, Category, Unit Price & COGS"),
        ("daily_sales", "Unique: (owner_id, item_id, date)"),
        ("forecasts", "Predictions, Winning Model & Restock Q*")
    ]
    for idx, (d_t, d_s) in enumerate(db_colls):
        draw_box(71.5, 73.8 - idx * 2.3, 23, 2.0, d_t + ": " + d_s, "",
                 bg="#ECFDF5", border="#6EE7B7", title_color="#065F46", title_size=8, sub_size=0, align='center')

    # Arrow between Mobile and FastAPI
    draw_arrow(60, 83.5, 60, 78.7, color="#2563EB", lw=1.8, label="HTTPS / JSON / JWT")
    # Arrow between FastAPI and MongoDB
    draw_arrow(66, 72.6, 70, 72.6, color="#059669", lw=1.8, label="PyMongo")

    # =========================================================================
    # 3. EMPIRICAL VALIDATION & REGRESSOR SCREENING (Y: 53.5 to 63.5)
    # =========================================================================
    draw_band(2, 53.5, 96, 10, "3. EMPIRICAL REGRESSOR SCREENING & FALSIFICATION GATE", bg="#FEF2F2", border="#FECACA", title_bg="#DC2626")

    # Placebo Reject Box
    draw_box(4, 54.5, 54, 7.5, "Exogenous Weather Regressors: EMPIRICALLY REJECTED",
             "180-Day Shifted & Permuted Placebos: p = 0.3800 (+0.32 pp WAPE Degradation). Excluded to avoid API rate limits & cost.",
             bg="#FFF1F2", border="#F43F5E", title_color="#9F1239", title_size=10.5, sub_size=8.5, lw=1.5)

    # Deterministic Calendar Box
    draw_box(62, 54.5, 34, 7.5, "Deterministic Calendar & Operating Context",
             "Local Day-of-Week Seasonality, Operating Store Hours & National Holidays via deterministic calendar masks.",
             bg="#EFF6FF", border="#60A5FA", title_color="#1E40AF", title_size=10.5, sub_size=8.5, lw=1.5)

    # Arrow from DB/API down to Screening
    draw_arrow(35, 66.5, 35, 62.0, color="#94A3B8", lw=1.2)

    # =========================================================================
    # 4. MULTI-TIER ADAPTIVE FORECASTING ENGINE (Y: 30 to 51.5)
    # =========================================================================
    draw_band(2, 30.5, 96, 21, "4. MULTI-TIER ADAPTIVE FORECASTING ENGINE (<1 ms Runtime, Pure Python Stdlib)",
              bg="#FEFCE8", border="#FEF08A", title_bg="#CA8A04")

    # Tier 1 Box
    draw_box(4, 34.5, 18, 14, "Tier 1: Cold Start", "n = 0 Days History\n\nCategory Bayesian Priors\n(\u03BC_cat from empirical base)\nRobust prior without store data",
             bg="#FFFFFF", border="#EAB308", title_color="#A16207", title_size=10.5, sub_size=8.5, lw=1.5)

    # Tier 2 Box
    draw_box(24, 34.5, 23, 14, "Tier 2: Early History", "1 \u2264 n < 5 Days History\n\nEmpirical Bayes Shrinkage:\n\u0177 = [n / (n + K)] \u00b7 \u0233 + [K / (n + K)] \u00b7 \u03BC_cat\n(K = 1, bounds variance)",
             bg="#FFFFFF", border="#EAB308", title_color="#A16207", title_size=10.5, sub_size=8.5, lw=1.5)

    # Tier 3 Box
    draw_box(49, 32.0, 31, 16.8, "Tier 3: Maturing Store History (n \u2265 5 Days)", "",
             bg="#FFFFFF", border="#EAB308", title_color="#A16207", title_size=10.5, sub_size=0, lw=1.5)
    ax.text(64.5, 46.2, "5-Candidate Ground-Truth Tournament:", ha='center', va='center',
            fontsize=9.5, fontweight='bold', color="#713F12", fontfamily='DejaVu Sans')

    cands = [
        "1. Naive Last-Observed (y_{t-1})",
        "2. EWMA (Exponential Smoothing, \u03b1 = 0.5)",
        "3. Moving Average (7-Day Rolling MA-7)",
        "4. Same-Weekday Moving Average (4-Week MA-4)",
        "5. Adaptive 60/40 Seasonal Hybrid (MA-4 + MA-7)"
    ]
    for c_idx, cand in enumerate(cands):
        ax.text(51, 43.8 - c_idx * 1.8, cand, ha='left', va='center', fontsize=8.2,
                color="#451A03", fontfamily='DejaVu Sans')

    # 5% Churn Margin Guard
    draw_box(50.5, 32.8, 28, 2.8, "5% Churn Margin Guard vs. MA-7 Baseline", "Prevents erratic model switching on statistical noise",
             bg="#FEF3C7", border="#D97706", title_color="#92400E", title_size=8.5, sub_size=7.2)

    # Winning Forecast Box
    draw_box(83, 34.5, 13, 14, "Winning Point\nForecast (\u0177)", "Cutoff-Safe Demand\n\nForecast Sigma:\n\u03c3 = max(1, RMSE)\n\nInference: <1 ms\nZero Heavy ML Libs",
             bg="#ECFDF5", border="#10B981", title_color="#065F46", title_size=10.5, sub_size=8.5, lw=1.5)

    # Arrows connecting tiers to winner
    draw_arrow(22, 41.5, 24, 41.5, color="#CA8A04", lw=1.5)
    draw_arrow(47, 41.5, 49, 41.5, color="#CA8A04", lw=1.5)
    draw_arrow(80, 41.5, 83, 41.5, color="#059669", lw=2, label="Winner")

    # =========================================================================
    # 5. STOCHASTIC INVENTORY DECISION LAYER (Y: 13.5 to 28.5)
    # =========================================================================
    draw_band(2, 13.5, 96, 15, "5. STOCHASTIC INVENTORY OPTIMIZATION LAYER (Newsvendor Model)",
              bg="#F0FDF4", border="#BBF7D0", title_bg="#15803D")

    # Cost Box
    draw_box(4, 15.0, 20, 11.5, "Asymmetric Cost Model", "Perishable Underage: Cu = p - c\nPerishable Overage: Co = c\n(100% loss of COGS on spoil)\n\nCritical Ratio:\nCR = Cu / (Cu + Co) = 1 - COGS",
             bg="#FFFFFF", border="#86EFAC", title_color="#14532D", title_size=10, sub_size=8.5, lw=1.3)

    # Safety Stock Box
    draw_box(26, 15.0, 21, 11.5, "Dynamic Safety Stock (SS)", "Target Normal Fractile:\nz* = \u03a6^-1(CR)  [\u2248 0.253 @ CR=0.60]\n\nSafety Stock Formulation:\nSS = max(1, min(3\u03c3, round(z* \u00b7 \u03c3)))",
             bg="#FFFFFF", border="#86EFAC", title_color="#14532D", title_size=10, sub_size=8.5, lw=1.3)

    # Order Target Box
    draw_box(49, 15.0, 23, 11.5, "Optimal Replenishment (Q*)", "Single-Period Integer Order:\nQ* = max(0, \u0177 + SS - I_current)\n\n-64.4% Spoilage Reduction\n+16.3% Gross Profit Surge",
             bg="#EFF6FF", border="#3B82F6", title_color="#1E40AF", title_size=10.5, sub_size=8.5, lw=1.5)

    # Coherence Guard Box
    draw_box(74, 15.0, 22, 11.5, "Hard Coherence Guard", "Sanity Stock Clamp:\nIf I_current \u2265 \u0177 + SS \u21d2 Q* \u2261 0\n\nPrevents over-ordering\nwhen surplus stock exists",
             bg="#FEF2F2", border="#EF4444", title_color="#991B1B", title_size=10, sub_size=8.5, lw=1.3)

    draw_arrow(89.5, 34.5, 89.5, 27.5, color="#15803D", lw=1.8, label="\u0177, \u03c3")
    draw_arrow(24, 20.7, 26, 20.7, color="#15803D", lw=1.5)
    draw_arrow(47, 20.7, 49, 20.7, color="#15803D", lw=1.5)
    draw_arrow(72, 20.7, 74, 20.7, color="#DC2626", lw=1.5)

    # =========================================================================
    # 6. CLOSED-LOOP OPERATIONAL FEEDBACK & EXPLANATION (Y: 1 to 12)
    # =========================================================================
    draw_band(2, 1.0, 96, 11, "6. CLOSED-LOOP OPERATIONAL FEEDBACK & GROUNDED DIAGNOSTICS",
              bg="#F8FAFC", border="#CBD5E1", title_bg="#334155")

    # Closing Count Split Box
    draw_box(4, 2.2, 28, 8.2, "Closing Count & Zero-Waste Split",
             "End-of-day stock count explicitly separates:\n\u2022 Actual Units Sold (Customer Demand)\n\u2022 Spoiled / Discarded Units (Waste Record)\nPrevents historical sales data contamination.",
             bg="#FFFFFF", border="#94A3B8", title_color="#0F172A", title_size=9.5, sub_size=8, lw=1.3)

    # Pace Check Box
    draw_box(34, 2.2, 30, 8.2, "Real-Time Mid-Day Pace Check",
             "Compares live sales velocity to expected curve:\n\u2022 Slow Pace Alert (< 0.35): Cut afternoon prep\n\u2022 Surge Alert (> 1.20): Stockout early-warning\nAverts waste before day's end.",
             bg="#FFFFFF", border="#94A3B8", title_color="#0F172A", title_size=9.5, sub_size=8, lw=1.3)

    # Diagnostic Explanation Box
    draw_box(66, 2.2, 30, 8.2, "Deterministic Diagnostic Explanations",
             "Grounded, plain-language manager advice:\n\u2022 'EWMA selected: 12% lower error than 7-day MA'\n\u2022 'Pace alert: sales at 28% of expected noon rate'\nZero ungrounded LLM hallucinations.",
             bg="#EFF6FF", border="#60A5FA", title_color="#1E40AF", title_size=9.5, sub_size=8, lw=1.3)

    # Closed-loop feedback arrows
    draw_arrow(18, 10.4, 18, 66.5, color="#475569", lw=1.5, ls='--', label="Uncontaminated Sales Ingestion", label_pos=0.6, label_offset=(-4, 0))
    draw_arrow(81, 10.4, 81, 83.5, color="#2563EB", lw=1.5, ls='--', label="Actionable Guidance & Pace Cards", label_pos=0.4, label_offset=(4, 0))

    out_png = r"E:\CAP\Documentation\academic-reviews\RestockIQ_System_Architecture_Current.png"
    out_svg = r"E:\CAP\Documentation\academic-reviews\RestockIQ_System_Architecture_Current.svg"
    
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.savefig(out_svg, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"Generated High-Res Architecture Diagram: {out_png} and {out_svg}")

if __name__ == "__main__":
    draw_architecture_diagram()

