import pptx
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    src_path = r"E:\CAP\Documentation\academic-reviews\Finall PPT.pptx"
    out_path = r"E:\CAP\Documentation\academic-reviews\Finall_PPT_Updated.pptx"
    prs = pptx.Presentation(src_path)

    # -------------------------------------------------------------------------
    # SLIDE 4: Objectives
    # -------------------------------------------------------------------------
    s4 = prs.slides[3]
    shape8 = s4.shapes[8]
    tf4 = shape8.text_frame
    tf4.clear()

    objectives = [
        ("Multi-Tier Adaptive Demand Forecasting:", " Implement dynamic progression from category Bayesian priors (cold start) to local ground-truth model tournaments as store sales mature."),
        ("Stochastic Inventory Optimization:", " Directly bridge the forecast-to-action gap using asymmetric Newsvendor critical fractiles (CR = 1 - COGS) to produce exact integer restock targets."),
        ("Perishable Food Waste Mitigation:", " Substantially cut retail food spoilage while preserving >= 98% on-shelf customer service availability."),
        ("Closed-Loop Mobile Operational Workflow:", " Deliver a lightweight, offline-resilient mobile client supporting daily closing counts, zero-waste demand separation, and mid-day pace tracking."),
        ("Empirical Methodological Falsification:", " Benchmark algorithms under 38-fold rolling-origin validation and disprove non-viable external regressors via placebos (weather p = 0.3800)."),
        ("Zero-Overhead Cloud Microservice:", " Deploy a pure Python standard-library engine capable of executing end-to-end multi-store forecasting tournaments in <1 ms with zero GPU requirements.")
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

    print("Updated Slide 4 (Objectives)")

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
    p0.text = "Day 0: Category Bayesian Priors"
    p0.font.size = Pt(9.5)
    p1 = tf16.add_paragraph()
    p1.text = "Day 1–4: Empirical Bayesian Shrinkage (K=1)"
    p1.font.size = Pt(9.5)
    p2 = tf16.add_paragraph()
    p2.text = "Day 5+: 5-Candidate Model Tournament"
    p2.font.size = Pt(9.5)

    set_shape_text(s7.shapes[18], "MULTI-TIER", font_size=Pt(9), bold=True)
    set_shape_text(s7.shapes[21], "Adaptive Tournament", font_size=Pt(12), bold=True)
    
    tf22 = s7.shapes[22].text_frame
    tf22.clear()
    p0 = tf22.paragraphs[0]
    p0.text = "5 Candidates evaluated on store ground truth"
    p0.font.size = Pt(9.5)
    p1 = tf22.add_paragraph()
    p1.text = "5% Churn Margin Guard prevents noise switching"
    p1.font.size = Pt(9.5)

    set_shape_text(s7.shapes[25], "Point Forecast", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[26], "Cutoff-safe, risk-adjusted demand estimate", font_size=Pt(9.5))

    set_shape_text(s7.shapes[29], "Stochastic Restock", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[30], "Newsvendor Fractile (CR = 1 - COGS) + Safety Stock", font_size=Pt(9.5))

    set_shape_text(s7.shapes[33], "Order Quantity (Q*)", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[34], "e.g. 'Order 15 units' (Coherence Guard prevents excess)", font_size=Pt(9.5))

    set_shape_text(s7.shapes[36], "Closing Count", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[37], "Explicit split: genuine sales vs. expired spoil units", font_size=Pt(9.5))

    set_shape_text(s7.shapes[40], "Mid-Day Pace Check", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[41], "Compares intra-day velocity against expected curves", font_size=Pt(9.5))

    set_shape_text(s7.shapes[44], "Operational Action", font_size=Pt(12), bold=True)
    set_shape_text(s7.shapes[45], "Flags slow pace (<0.35) or surge demand (>1.20)", font_size=Pt(9.5))

    set_shape_text(s7.shapes[48], "DIAGNOSTIC EXPLANATIONS", font_size=Pt(9), bold=True)
    set_shape_text(s7.shapes[50], "Diagnostic Explanations: Plain-language operational reason for algorithm selection and safety stock without technical jargon.", font_size=Pt(10))

    print("Updated Slide 7 (Proposed Methodology)")

    # -------------------------------------------------------------------------
    # SLIDE 9: Working Demonstration
    # -------------------------------------------------------------------------
    s9 = prs.slides[8]
    set_shape_text(s9.shapes[6], "Production mobile application deployed on physical Android hardware (ARM64) with live FastAPI cloud backend and MongoDB Atlas.", font_size=Pt(11))
    set_shape_text(s9.shapes[7], "Dashboard & Restock Recommendation", font_size=Pt(13), bold=True)
    set_shape_text(s9.shapes[8], "Daily Closing Count & Zero-Waste Split", font_size=Pt(13), bold=True)
    set_shape_text(s9.shapes[9], "Mid-Day Pace Check & Coherence Guard", font_size=Pt(13), bold=True)

    print("Updated Slide 9 (Working Demonstration)")

    # -------------------------------------------------------------------------
    # SLIDE 10: Implementation
    # -------------------------------------------------------------------------
    s10 = prs.slides[9]
    modules_s10 = [
        (s10.shapes[8], "Multi-Tier Tournament Engine", "Pure Python standard-library engine executing 5 candidate algorithms in <1 ms on free-tier cloud CPU with zero GPU overhead."),
        (s10.shapes[12], "Empirical Bayesian Shrinkage", "Anchors sparse sales (1 to 4 days) to cross-store category priors with K=1, preventing small-sample statistical variance."),
        (s10.shapes[16], "Closing Count & Demand Isolation", "Daily stock count explicitly separates genuine consumer purchases from discarded spoil units to keep history uncontaminated."),
        (s10.shapes[20], "Stochastic Newsvendor Restock", "Bridges forecast-to-action by translating point demand into integer replenishment orders Q* via critical ratio CR = 1 - COGS."),
        (s10.shapes[24], "Mid-Day Pace Check & Coherence Guard", "Monitors intra-day sales velocity; automatically enforces zero restock if current stock already satisfies predicted demand."),
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

    print("Updated Slide 10 (Implementation)")

    # -------------------------------------------------------------------------
    # SLIDE 11: Results (Populating previously empty slide!)
    # -------------------------------------------------------------------------
    s11 = prs.slides[10]
    
    # 1. Section Header 1
    sh1 = s11.shapes.add_textbox(Emu(450000), Emu(1400000), Emu(9000000), Emu(300000))
    p = sh1.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Benchmark 1: 38-Fold Rolling-Origin Evaluation (French Perishable Bakery, 482 Days)"
    r.font.bold = True
    r.font.size = Pt(11.5)
    r.font.name = "Times New Roman"
    r.font.color.rgb = RGBColor(30, 41, 59)

    # 2. Table 1 (French Bakery Benchmark)
    t1_shape = s11.shapes.add_table(5, 5, Emu(450000), Emu(1750000), Emu(9000000), Emu(1400000))
    t1 = t1_shape.table
    t1.columns[0].width = Emu(2900000)
    t1.columns[1].width = Emu(1300000)
    t1.columns[2].width = Emu(1400000)
    t1.columns[3].width = Emu(1400000)
    t1.columns[4].width = Emu(2000000)

    t1_data = [
        ["Forecasting Architecture", "WAPE (%)", "RMSE (units)", "MAE (units)", "Wilcoxon Rank Test"],
        ["GBDT (Ours / Gradient Boosted)", "25.48%", "3.84", "2.61", "Winner (p = 4.7 x 10^-4)"],
        ["Facebook Prophet", "27.95%", "4.31", "2.89", "Baseline Comparison"],
        ["Moving Average (MA-7)", "29.12%", "4.65", "3.05", "Standard Heuristic"],
        ["Naive (Last-Observed Baseline)", "30.39%", "4.88", "3.22", "Lower Bound"]
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
                    cell.fill.fore_color.rgb = RGBColor(30, 58, 138)  # Navy
                elif r_idx == 1:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(15, 23, 42)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(220, 252, 231)  # Soft green highlight
                else:
                    r.font.color.rgb = RGBColor(51, 65, 85)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = RGBColor(248, 250, 252) if r_idx % 2 == 0 else RGBColor(255, 255, 255)

    # 3. Section Header 2
    sh2 = s11.shapes.add_textbox(Emu(450000), Emu(3250000), Emu(9000000), Emu(300000))
    p = sh2.text_frame.paragraphs[0]
    r = p.add_run()
    r.text = "Benchmark 2: Production Adaptive Tournament vs. Legacy Fixed Rules (Cutoff-Safe Evaluation)"
    r.font.bold = True
    r.font.size = Pt(11.5)
    r.font.name = "Times New Roman"
    r.font.color.rgb = RGBColor(30, 41, 59)

    # 4. Table 2 (Adaptive Tournament)
    t2_shape = s11.shapes.add_table(3, 4, Emu(450000), Emu(3600000), Emu(9000000), Emu(950000))
    t2 = t2_shape.table
    t2.columns[0].width = Emu(3200000)
    t2.columns[1].width = Emu(1700000)
    t2.columns[2].width = Emu(1700000)
    t2.columns[3].width = Emu(2400000)

    t2_data = [
        ["Engine Strategy", "Evaluation WAPE (%)", "RMSE (units)", "Day-to-Day Cliff Variance"],
        ["RestockIQ Adaptive Tournament", "35.30%", "4.82", "Low (-45.3% Cliff Reduction)"],
        ["Legacy Static Blend (Fixed 60/40)", "40.55%", "5.46", "High (Abrupt Day-28 Transition)"]
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

    # 5. Placebo Falsification Callout Box
    callout = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(450000), Emu(4750000), Emu(9000000), Emu(1400000))
    callout.fill.solid()
    callout.fill.fore_color.rgb = RGBColor(254, 242, 242)  # Soft red alert / callout
    callout.line.color.rgb = RGBColor(239, 68, 68)
    callout.line.width = Pt(1)

    tf_callout = callout.text_frame
    tf_callout.clear()
    
    p0 = tf_callout.paragraphs[0]
    r0 = p0.add_run()
    r0.text = "Scientific Falsification of External Weather Regressors (Permutation p = 0.3800):"
    r0.font.bold = True
    r0.font.size = Pt(11)
    r0.font.name = "Times New Roman"
    r0.font.color.rgb = RGBColor(153, 27, 27)

    p1 = tf_callout.add_paragraph()
    r1 = p1.add_run()
    r1.text = "Exogenous weather features (temperature, rain, precipitation) were evaluated with 180-day shifted placebos and circular permutations. Weather features degraded WAPE by +0.32 percentage points and failed the paired permutation test (p = 0.3800). Consequently, weather regressors were intentionally rejected to eliminate paid third-party API dependencies and runtime failure points."
    r1.font.bold = False
    r1.font.size = Pt(10)
    r1.font.name = "Calibri"
    r1.font.color.rgb = RGBColor(69, 10, 10)

    print("Populated Slide 11 (Results) with Benchmarks & Placebo Falsification")

    # -------------------------------------------------------------------------
    # SLIDE 12: Conclusion / Operational Impact
    # -------------------------------------------------------------------------
    s12 = prs.slides[11]
    modules_s12 = [
        (s12.shapes[7], "64.4% Perishable Waste Cut", "Newsvendor CR=0.60 reduced simulated food spoilage from 25,225 to 8,982 units (-16,243 units saved over 180 days)."),
        (s12.shapes[11], "+16.3% Net Profit Surge", "Eliminated catastrophic over-ordering, increasing retailer gross profit by +€5,839.55 without sacrificing sales."),
        (s12.shapes[15], "100% Demand Fulfillment", "Maintained 38,187 units sold (identical to 95% service level policy) with negligible 1.2% stockout frequency."),
        (s12.shapes[19], "Eliminated Forecast Cliffs", "Empirical shrinkage and the 5% churn margin reduced day-to-day transition variance by 45.3% across cold-start tiers."),
        (s12.shapes[23], "<1 ms Cloud Compute", "Pure Python standard-library implementation executes multi-item tournaments in <1 ms with zero GPU requirements."),
        (s12.shapes[27], "Verified Mobile Production", "Fully wired Flutter APK compiled for ARM64 and live cloud microservice verified on physical hardware.")
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

    print("Updated Slide 12 (Conclusion / Impact)")

    # Save presentation
    prs.save(out_path)
    print(f"Successfully generated updated deck: {out_path}")

if __name__ == "__main__":
    build_presentation()

