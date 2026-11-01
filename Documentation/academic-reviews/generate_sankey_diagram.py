import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import numpy as np

def draw_sankey():
    # 16:9 widescreen canvas (300 DPI)
    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Palette: Professional Academic Grayscale with Subtle Theme Accents
    c_white = "#FFFFFF"
    c_header_bg = "#B91C1C"    # Burgundy red matching college template
    c_header_text = "#FFFFFF"
    c_card_bg = "#F8FAFC"
    c_border = "#0F172A"
    c_text_main = "#0F172A"
    c_text_sub = "#334155"

    # Category Flow Colors (Subtle translucent tones)
    colors = {
        "ts": "#3B82F6",       # Blue (Time Series)
        "weather": "#F43F5E",  # Rose/Red (Weather)
        "sme": "#F59E0B",      # Amber (SME Sparsity)
        "waste": "#10B981",    # Emerald (Waste)
        "mobile": "#8B5CF6",   # Purple (Mobile TAM)
        "gap": "#64748B",      # Slate (Gaps)
        "sol": "#1E3A8A"       # Deep Navy (RestockIQ)
    }

    fig.patch.set_facecolor(c_white)

    # Helper: Draw smooth Bezier flow band between two vertical segments
    def draw_flow(x1, y1_bot, y1_top, x2, y2_bot, y2_top, color, alpha=0.35):
        # Cubic bezier connection
        mid_x = (x1 + x2) / 2
        verts = [
            (x1, y1_bot),
            (mid_x, y1_bot),
            (mid_x, y2_bot),
            (x2, y2_bot),
            (x2, y2_top),
            (mid_x, y2_top),
            (mid_x, y1_top),
            (x1, y1_top),
            (x1, y1_bot)
        ]
        codes = [
            Path.MOVETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.LINETO,
            Path.CURVE4,
            Path.CURVE4,
            Path.CURVE4,
            Path.CLOSEPOLY
        ]
        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor=color, edgecolor="none", alpha=alpha, zorder=2)
        ax.add_patch(patch)

    # Helper: Draw Node Rectangle
    def draw_node(x, y, w, h, title, subtitle="", bg="#FFFFFF", border="#000000", t_size=9.5, s_size=8.0):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0",
                                      fc=bg, ec=border, lw=1.2, zorder=3)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w / 2, y + h * 0.62, title, ha='center', va='center',
                    fontsize=t_size, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans', zorder=4)
            ax.text(x + w / 2, y + h * 0.28, subtitle, ha='center', va='center',
                    fontsize=s_size, color=c_text_sub, fontfamily='DejaVu Sans', zorder=4)
        else:
            ax.text(x + w / 2, y + h / 2, title, ha='center', va='center',
                    fontsize=t_size, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans', zorder=4)

    # =========================================================================
    # 0. HEADER BANNER
    # =========================================================================
    ax.text(50, 97.2, "RestockIQ: Literature Review Synthesis & Gap Flow (Sankey Taxonomy)",
            ha='center', va='center', fontsize=15, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans')
    ax.text(50, 94.6, "Mapping 25 Peer-Reviewed Studies (2024–2026) Across 5 Themes to Identified Gaps and RestockIQ Solutions",
            ha='center', va='center', fontsize=9.5, color=c_text_sub, fontfamily='DejaVu Sans')

    # Top Column Labels
    col_x = [4, 28, 54, 78]
    col_w = [18, 19, 19, 18]
    headers = [
        "1. LITERATURE THEMES\n(25 Papers: 2024–2026)",
        "2. SURVEYED PARADIGMS\n& METHODOLOGIES",
        "3. IDENTIFIED GAPS\n(Core Bottlenecks)",
        "4. RESTOCKIQ RESOLUTION\n(Proposed Engineering)"
    ]
    for idx, (cx, cw, hdr) in enumerate(zip(col_x, col_w, headers)):
        h_box = patches.FancyBboxPatch((cx, 87.0), cw, 5.8, boxstyle="square,pad=0",
                                       fc="#E2E8F0", ec="#0F172A", lw=1.2, zorder=3)
        ax.add_patch(h_box)
        ax.text(cx + cw / 2, 89.9, hdr, ha='center', va='center',
                fontsize=8.5, fontweight='bold', color=c_text_main, fontfamily='DejaVu Sans', zorder=4)

    # =========================================================================
    # COLUMN 1: 5 LITERATURE THEMES (X: 4 to 22)
    # =========================================================================
    t_boxes = [
        # y, h, title, sub, color_key
        (71.0, 14.0, "Time-Series & Forecasting", "9 Papers (Aqila, Kamboj, etc.)", "ts"),
        (55.0, 13.0, "External Regressors & Weather", "4 Papers (Guler, Lalitha, Jain)", "weather"),
        (40.0, 12.0, "SME Data Sparsity & Cold-Start", "3 Papers (Susanto, Rahmatillah)", "sme"),
        (25.0, 12.0, "Food Waste & Inventory Analytics", "3 Papers (Padmavathy, Avuduri)", "waste"),
        (8.0,  14.0, "Mobile Adoption & TAM Frameworks", "6 Papers (Janchidfah, Yuniarty)", "mobile")
    ]
    for y, h, t, s, ck in t_boxes:
        draw_node(4, y, 18, h, t, s, bg="#FFFFFF", border="#0F172A")

    # =========================================================================
    # COLUMN 2: METHODOLOGICAL PARADIGMS (X: 28 to 47)
    # =========================================================================
    m_boxes = [
        (72.0, 13.0, "Deep Neural Networks (LSTMs)", "Needs ~1,000 Days; High Overfitting"),
        (56.0, 13.0, "Enterprise GBDT & Prophet", "Heavy Compute; Complex Pipelines"),
        (42.0, 11.0, "Exogenous Weather Regressors", "Fails Placebos (p=0.3800, +0.32 pp)"),
        (26.0, 13.0, "Classical Moving Averages", "Static Heuristics; Zero Actionability"),
        (8.0,  15.0, "Manual Mobile Apps (TAM)", "High Usability; No Predictive Logic")
    ]
    for y, h, t, s in m_boxes:
        draw_node(28, y, 19, h, t, s, bg="#FFFFFF", border="#0F172A")

    # =========================================================================
    # COLUMN 3: THE 4 RESEARCH GAPS (X: 54 to 73)
    # =========================================================================
    g_boxes = [
        (66.0, 19.0, "Cold-Start & Sparsity Gap", "Deep models fail on shallow\nstore histories (<30 days)."),
        (46.0, 17.0, "Infrastructure Cost Gap", "Enterprise tools require heavy\ncloud GPUs & paid weather APIs."),
        (26.0, 17.0, "Forecast-to-Action Gap", "Studies stop at RMSE/MAPE without\ncalculating physical restock Q*."),
        (8.0,  15.0, "Micro-SME Accessibility Gap", "ERP systems assume data teams;\nsmall operators need mobile advice.")
    ]
    for y, h, t, s in g_boxes:
        draw_node(54, y, 19, h, t, s, bg="#FEF2F2", border="#DC2626")

    # =========================================================================
    # COLUMN 4: RESTOCKIQ RESOLUTION (X: 78 to 96)
    # =========================================================================
    s_boxes = [
        (66.0, 19.0, "Multi-Tier Tournament", "Category Priors (Days 1–6)\nEmpirical Shrinkage & 5-Model\nTournament with 5% Churn Guard"),
        (46.0, 17.0, "<1 ms Stdlib Microservice", "Pure Python standard library;\n$0 GPU cost, zero external API\npoints of failure (FastAPI/Render)"),
        (26.0, 17.0, "Stochastic Newsvendor (Q*)", "Asymmetric Critical Ratio (CR=0.60)\nCuts waste by 64.4% (-16,243 units)\nSurges profit by +16.3% (+€5,839)"),
        (8.0,  15.0, "Closed-Loop Flutter App", "Android Client (Riverpod State)\nDaily Closing Count (Zero-Waste Split)\nReal-Time Mid-Day Pace Alerts")
    ]
    for y, h, t, s in s_boxes:
        draw_node(78, y, 18, h, t, s, bg="#ECFDF5", border="#059669")

    # =========================================================================
    # SANKEY FLOW PATHS (Col 1 -> Col 2)
    # =========================================================================
    draw_flow(22, 73.0, 83.0, 28, 73.0, 83.0, colors["ts"])
    draw_flow(22, 71.0, 77.0, 28, 58.0, 67.0, colors["ts"])
    draw_flow(22, 56.0, 66.0, 28, 43.0, 51.0, colors["weather"])
    draw_flow(22, 42.0, 50.0, 28, 74.0, 82.0, colors["sme"])
    draw_flow(22, 40.0, 46.0, 28, 28.0, 37.0, colors["sme"])
    draw_flow(22, 26.0, 35.0, 28, 28.0, 37.0, colors["waste"])
    draw_flow(22, 10.0, 20.0, 28, 10.0, 21.0, colors["mobile"])

    # =========================================================================
    # SANKEY FLOW PATHS (Col 2 -> Col 3)
    # =========================================================================
    draw_flow(47, 74.0, 83.0, 54, 70.0, 83.0, colors["gap"])
    draw_flow(47, 58.0, 67.0, 54, 49.0, 61.0, colors["gap"])
    draw_flow(47, 43.0, 51.0, 54, 48.0, 58.0, colors["gap"])
    draw_flow(47, 28.0, 37.0, 54, 28.0, 41.0, colors["gap"])
    draw_flow(47, 10.0, 21.0, 54, 10.0, 21.0, colors["gap"])

    # =========================================================================
    # SANKEY FLOW PATHS (Col 3 -> Col 4: Each Gap Converges to RestockIQ Module)
    # =========================================================================
    draw_flow(73, 68.0, 83.0, 78, 68.0, 83.0, "#059669", alpha=0.4)
    draw_flow(73, 48.0, 61.0, 78, 48.0, 61.0, "#059669", alpha=0.4)
    draw_flow(73, 28.0, 41.0, 78, 28.0, 41.0, "#059669", alpha=0.4)
    draw_flow(73, 10.0, 21.0, 78, 10.0, 21.0, "#059669", alpha=0.4)

    out_png = r"E:\CAP\Documentation\academic-reviews\RestockIQ_Literature_Sankey.png"
    plt.savefig(out_png, dpi=300, bbox_inches='tight', facecolor=c_white, edgecolor='none')
    plt.close()
    print(f"Generated Literature Sankey Diagram: {out_png}")

if __name__ == "__main__":
    draw_sankey()

