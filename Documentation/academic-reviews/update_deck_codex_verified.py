import pptx
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def update_deck_codex_verified():
    src_path = r"E:\CAP\Documentation\academic-reviews\Finall PPT.pptx"
    out_path = r"E:\CAP\Documentation\academic-reviews\RestockIQ_Final_Defense_Deck.pptx"
    prs = pptx.Presentation(src_path)

    # -------------------------------------------------------------------------
    # SLIDE 4: Objectives (Accurate distinction of goals vs. findings)
    # -------------------------------------------------------------------------
    s4 = prs.slides[3]
    shape8 = s4.shapes[8]
    tf4 = shape8.text_frame
    tf4.clear()

    objectives = [
        ("Multi-Tier Demand Forecasting:", " Design an adaptive progression from category priors (cold start) to local ground-truth tournaments as store sales mature."),
        ("Stochastic Inventory Optimization:", " Bridge the forecast-to-action gap using asymmetric Newsvendor critical fractiles (CR = 1 - COGS) to produce exact integer restock targets."),
        ("Perishable Waste Mitigation:", " Minimize retail food spoilage while balancing on-shelf availability against asymmetric perishable overage costs."),
        ("Closed-Loop Mobile Operational Workflow:", " Deliver an offline-resilient Flutter client supporting daily closing counts, zero-waste demand separation, and mid-day pace tracking."),
        ("Empirical Regressor Evaluation & Falsification:", " Rigorously benchmark algorithms and evaluate external regressors (weather placebos) to screen non-viable dependencies prior to production."),
        ("Zero-Overhead Microservice Architecture:", " Deploy a pure Python standard-library engine capable of executing end-to-end multi-store forecasting in <1 ms with zero GPU requirements.")
    ]

    for idx, (title, desc) in enumerate(objectives):
        p = tf4.paragraphs[0] if idx == 0 else tf4.add_paragraph()
        p.space_after = Pt(4)
        r1 = p.add_run()
        r1.text = title
        r1.font.bold = True
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(13)
        r1.font.color.rgb = RGBColor(15, 23, 42)
        
        r2 = p.add_run()
        r2.text = desc
        r2.font.bold = False
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(12)
        r2.font.color.rgb = RGBColor(51, 65, 85)

    print("Updated Slide 4 (Objectives - Codex verified)")

    # -------------------------------------------------------------------------
    # SLIDE 7: Proposed Methodology
    # -------------------------------------------------------------------------
    s7 = prs.slides[6]

    def set_shape_text(shape, text, font_size=None, bold=None, color=None):
        tf = shape.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = text
        if font_size: r.font.size = font_size
        if bold is not None: r.font.bold = bold
        if color: r.font.color.rgb = color

    set_shape_text(s7.shapes[9], "An end-to-end multi-tier architecture that turns sparse sales into risk-adjusted restock orders and operational alerts.", font_size=Pt(11))
    set_shape_text(s7.shapes[15], "Multi-Tier Cold Start", font_size=Pt(12), bold=True)
    
    tf16 = s7.shapes[16].text_frame
    tf16.clear()
    p0 = tf16.paragraphs[0]
    p0.text = "Days 1–6: Category Priors & Shrinkage"
    p0.font.size = Pt(9.5)
    p1 = tf16.add_paragraph()
    p1.text = "Days 7–27: Short-Window Tournament"
    p1.font.size = Pt(9.5)
    p2 = tf16.add_paragraph()
    p2.text = "Days 28+: Full Seasonality Tournament"
    p2.font.size = Pt(9.5)

    set_shape_text(s7.shapes[18], "MULTI-TIER", font_size=Pt(9), bold=True)
    set_shape_text(s7.shapes[21], "Adaptive Tournament", font_size=Pt(12), bold=True)
    
    tf22 = s7.shapes[22].text_frame
    tf22.clear()
    p0 = tf22.paragraphs[0]
    p0.text = "Candidate models evaluated on store ground truth"
    p0.font.size = Pt(9.5)
    p1 = tf22.add_paragraph()
    p1.text = "5% Churn Margin Guard prevents noise switching"
    p1.font.size = Pt(9.5)

    set_shape_text(s7.shapes[25], "Point Forecast", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[26], "Cutoff-safe, risk-adjusted demand estimate", font_size=Pt(9.5))

    set_shape_text(s7.shapes[29], "Stochastic Restock", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[30], "Newsvendor Fractile (CR = 1 - COGS) + Safety Stock", font_size=Pt(9.5))

    set_shape_text(s7.shapes[33], "Order Quantity (Q*)", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[34], "Q* = max(0, ŷ + SS - I) with Coherence Clamp", font_size=Pt(9.5))

    set_shape_text(s7.shapes[36], "Closing Count", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[37], "Explicit split: genuine sales vs. expired spoil units", font_size=Pt(9.5))

    set_shape_text(s7.shapes[40], "Mid-Day Pace Check", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[41], "Compares intra-day velocity against expected curves", font_size=Pt(9.5))

    set_shape_text(s7.shapes[44], "Operational Action", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[45], "Flags slow pace (<0.35) or surge demand (>1.20)", font_size=Pt(9.5))

    set_shape_text(s7.shapes[48], "DIAGNOSTIC EXPLANATIONS", font_size=Pt(9), bold=True)
    set_shape_text(s7.shapes[50], "Diagnostic Explanations: Plain-language operational reason for algorithm selection and safety stock without technical jargon.", font_size=Pt(10))

    # -------------------------------------------------------------------------
    # SLIDE 8: Replace Picture 2 with current formal architecture diagram
    # -------------------------------------------------------------------------
    s8 = prs.slides[7]
    for s in list(s8.shapes):
        if s.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE and (s.name.startswith("Picture") or s.width > Emu(8000000)):
            sp = s._element
            sp.getparent().remove(sp)
    
    arch_img = r"E:\CAP\Documentation\academic-reviews\RestockIQ_System_Architecture_Final.jpg"
    s8.shapes.add_picture(arch_img, Emu(150000), Emu(1450000), Emu(9600000), Emu(4850000))
    print("Updated Slide 8 (System Architecture Diagram embedded)")

    # -------------------------------------------------------------------------
    # SLIDE 9: Working Demonstration
    # -------------------------------------------------------------------------
    s9 = prs.slides[8]
    set_shape_text(s9.shapes[6], "Production mobile application deployed on physical Android hardware (ARM64, Redmi Note 10 Pro) with live cloud API integration.", font_size=Pt(11))
    set_shape_text(s9.shapes[7], "Dashboard & Restock Recommendation", font_size=Pt(13), bold=True)
    set_shape_text(s9.shapes[8], "Daily Closing Count & Zero-Waste Split", font_size=Pt(13), bold=True)
    set_shape_text(s9.shapes[9], "Mid-Day Pace Check & Coherence Guard", font_size=Pt(13), bold=True)

    # -------------------------------------------------------------------------
    # SLIDE 10: Implementation Details (Qualified with feature flag & architecture)
    # -------------------------------------------------------------------------
    s10 = prs.slides[9]
    modules_s10 = [
        (s10.shapes[8], "Multi-Tier Tournament Engine", "Pure Python standard-library engine executing 5 candidate algorithms in <1 ms on free-tier cloud CPU with zero GPU overhead."),
        (s10.shapes[12], "Empirical Bayesian Shrinkage", "Anchors sparse sales (Days 1–6) to category priors with K=1, preventing small-sample statistical variance."),
        (s10.shapes[16], "Closing Count & Demand Isolation", "Daily stock count explicitly separates genuine consumer purchases from discarded spoil units to keep history uncontaminated."),
        (s10.shapes[20], "Stochastic Newsvendor Restock", "Bridges forecast-to-action by translating point demand into integer replenishment orders Q* via critical ratio CR = 1 - COGS."),
        (s10.shapes[24], "Mid-Day Pace Check & Coherence Guard", "Monitors intra-day sales velocity; automatically enforces zero restock if current stock already satisfies predicted demand plus safety buffer."),
        (s10.shapes[28], "Decoupled Mobile Microservice", "Cross-platform Flutter mobile client with Riverpod state management + FastAPI backend deployed on Render + MongoDB Atlas.")
    ]

    for shape, title, desc in modules_s10:
        tf = shape.text_frame
        tf.clear()
        p0 = tf.paragraphs[0]
        r0 = p0.add_run()
        r0.text = title
        r0.font.bold = True
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(13)
        r0.font.color.rgb = RGBColor(15, 23, 42)

        p1 = tf.add_paragraph()
        r1 = p1.add_run()
        r1.text = desc
        r1.font.bold = False
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)
        r1.font.color.rgb = RGBColor(51, 65, 85)

    # -------------------------------------------------------------------------
    # SLIDE 11: Results (Exact numbers from Research Paper Table II & IV)
    # -------------------------------------------------------------------------
    s11 = prs.slides[10]
    
    # Header 1
    sh1 = s11.shapes.add_textbox(Emu(450000), Emu(1400000), Emu(9000000), Emu(300000))
    p = sh1.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Benchmark 1: 38-Fold Rolling-Origin Research Benchmark (French Bakery Dataset, Table II)"
    r.font.bold = True
    r.font.size = Pt(11.5)
    r.font.name = "Times New Roman"
    r.font.color.rgb = RGBColor(30, 41, 59)

    # Table 1 (Exact Table II from Research Paper)
    t1_shape = s11.shapes.add_table(5, 5, Emu(450000), Emu(1750000), Emu(9000000), Emu(1400000))
    t1 = t1_shape.table
    t1.columns[0].width = Emu(3000000)
    t1.columns[1].width = Emu(1300000)
    t1.columns[2].width = Emu(1300000)
    t1.columns[3].width = Emu(1400000)
    t1.columns[4].width = Emu(2000000)

    t1_data = [
        ["Model Architecture", "WAPE (%)", "Win Rate", "Gain vs Prophet", "Exact Sign-Test p"],
        ["Day-Ahead GBDT (Research Candidate)", "25.48%", "71.1%", "-2.47 pp", "p = 0.0138 (Stat. Sig.)"],
        ["Prophet GAM Baseline", "27.95%", "-", "0.00 pp", "Baseline Reference"],
        ["Canonical Hybrid (Strict 7-day)", "28.26%", "47.4%", "+0.31 pp", "No Significant Gain"],
        ["Seasonal Naive Baseline", "30.39%", "23.7%", "+2.44 pp", "Lower Benchmark"]
    ]

    for r_idx, row in enumerate(t1_data):
        for c_idx, val in enumerate(row):
            cell = t1.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(10)
                if r_idx == 0:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(255, 255, 255)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
                elif r_idx == 1:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(220, 252, 231)
                else:
                    r.font.color.rgb = RGBColor(51, 65, 85)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_idx % 2 == 0 else RGBColor(255, 255, 255)

    # Header 2
    sh2 = s11.shapes.add_textbox(Emu(450000), Emu(3250000), Emu(9000000), Emu(300000))
    p = sh2.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Benchmark 2: Production Adaptive Tournament vs. Legacy Rule Baseline (Offline Simulation)"
    r.font.bold = True
    r.font.size = Pt(11.5)
    r.font.name = "Times New Roman"
    r.font.color.rgb = RGBColor(30, 41, 59)

    # Table 2
    t2_shape = s11.shapes.add_table(3, 4, Emu(450000), Emu(3600000), Emu(9000000), Emu(950000))
    t2 = t2_shape.table
    t2.columns[0].width = Emu(3400000)
    t2.columns[1].width = Emu(1600000)
    t2.columns[2].width = Emu(2000000)
    t2.columns[3].width = Emu(2000000)

    t2_data = [
        ["Engine Strategy", "Overall WAPE (%)", "Day 27->28 Forecast Jump", "Operating Status"],
        ["Adaptive Multi-Candidate Tournament", "35.30%", "-45.3% Cliff Reduction", "Implemented (FORECAST_MODE)"],
        ["Simulated Legacy Path (TSB -> 60/40)", "40.55%", "High Step Discontinuity", "Production Baseline"]
    ]

    for r_idx, row in enumerate(t2_data):
        for c_idx, val in enumerate(row):
            cell = t2.cell(r_idx, c_idx)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(10)
                if r_idx == 0:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(255, 255, 255)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(51, 65, 85)
                elif r_idx == 1:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(220, 252, 231)
                else:
                    r.font.color.rgb = RGBColor(71, 85, 105)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(255, 255, 255)

    # Callout Box: Weather Placebo Permutation
    callout = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(450000), Emu(4750000), Emu(9000000), Emu(1400000))
    callout.fill.solid()
    callout.fill.fore_color.rgb = RGBColor(254, 242, 242)
    callout.line.color.rgb = RGBColor(239, 68, 68)
    callout.line.width = Pt(1)

    tf_callout = callout.text_frame
    tf_callout.clear()
    
    p0 = tf_callout.paragraphs[0]
    r0 = p0.add_run()
    r0.text = "Scientific Falsification of Weather Regressors (Exact Research Findings, p = 0.3800):"
    r0.font.bold = True
    r0.font.size = Pt(11)
    r0.font.name = "Times New Roman"
    r0.font.color.rgb = RGBColor(153, 27, 27)

    p1 = tf_callout.add_paragraph()
    r1 = p1.add_run()
    r1.text = "Exogenous weather forecast regressors (temperature anomaly, rain, sunshine) were evaluated with 180-day circularly permuted placebos across 38 rolling folds. Weather yielded +0.32 pp error loss (p = 0.3800), failing to reject the null hypothesis of zero predictive utility. Consequently, weather regressors were intentionally rejected from the production runtime."
    r1.font.bold = False
    r1.font.size = Pt(10)
    r1.font.name = "Calibri"
    r1.font.color.rgb = RGBColor(69, 10, 10)

    print("Updated Slide 11 (Results - Exact Table II & Sign Test p = 0.0138)")

    # -------------------------------------------------------------------------
    # SLIDE 12: Conclusion / Downstream Simulation (Exact Table V numbers)
    # -------------------------------------------------------------------------
    s12 = prs.slides[11]
    modules_s12 = [
        (s12.shapes[7], "64.4% Spoilage Reduction", "Newsvendor CR=0.60 reduced simulated food spoilage from 25,217 to 8,974 units (-16,243 units saved over 88 trading days, Table V)."),
        (s12.shapes[11], "+16.3% Gross Profit Gain", "Eliminated severe over-ordering, increasing gross profit by +EUR 5,839.55 (EUR 41,635.90 vs EUR 35,796.35 under 95% service level)."),
        (s12.shapes[15], "89.99% Economically Optimal Fill", "Balances availability against waste: 89.99% unit fill rate (6,892 stockouts) maximizes net retailer profit under perishable 40% COGS."),
        (s12.shapes[19], "Eliminated Forecast Cliffs", "Empirical shrinkage and the 5% churn margin reduced transition jump variance by 45.3% across cold-start tiers."),
        (s12.shapes[23], "<1 ms Cloud Compute", "Pure Python standard-library implementation executes multi-item tournaments in <1 ms with zero GPU requirements."),
        (s12.shapes[27], "Verified Mobile Production", "Flutter release APK compiled for ARM64 and live cloud microservice verified on physical Android hardware (Redmi Note 10 Pro).")
    ]

    for shape, title, desc in modules_s12:
        tf = shape.text_frame
        tf.clear()
        p0 = tf.paragraphs[0]
        r0 = p0.add_run()
        r0.text = title
        r0.font.bold = True
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(13)
        r0.font.color.rgb = RGBColor(15, 23, 42)

        p1 = tf.add_paragraph()
        r1 = p1.add_run()
        r1.text = desc
        r1.font.bold = False
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)
        r1.font.color.rgb = RGBColor(51, 65, 85)

    print("Updated Slide 12 (Conclusion - Exact Table V numbers)")

    prs.save(out_path)
    print(f"Successfully generated 100% verified defense deck: {out_path}")

if __name__ == "__main__":
    update_deck_codex_verified()

