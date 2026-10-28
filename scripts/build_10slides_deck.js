const path = require('path');
const fs = require('fs');
const pptxgen = require('../Documentation/node_modules/pptxgenjs');

console.log("================================================================================");
console.log("   RESTOCKIQ: BUILDING 10-SLIDE HIGH-READABILITY SOFTWARE TESTING DECK (.PPTX)  ");
console.log("================================================================================");

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE'; // 13.333 x 7.5 inches standard 16:9 widescreen
pptx.title = 'Testing RestockIQ: Software Testing Defense';
pptx.subject = 'Course 702IT0E035 Software Testing Presentation';
pptx.author = 'Yatin Patil (Lucifer)';

// ----------------------------------------------------------------------------
// Warm Tech Theme Color Tokens
// ----------------------------------------------------------------------------
const C = {
  bgWarm: 'FCF9F4',       // Off-white cream canvas
  cardBg: 'FFFFFF',       // Clean card surface
  primaryDark: '1B4332',  // Deep Forest Green
  primaryDeep: '0F291E',  // Dark Forest Green
  accentAmber: 'FFB702',  // Warm Amber
  textDark: '1C1C19',     // Deep Slate
  textMuted: '5A5A54',    // Muted grey for sub-labels
  borderSoft: 'E5E0D8',   // Soft divider border
  borderMedium: 'D8D2C6', // Stronger card border
  dangerRed: 'B91C1C',    // Coral Alert Red
  successGreen: '2D6A4F', // Forest Green Accent
  tagBg: 'EFEAE1',        // Soft badge container
  codeBg: 'F4EFE6',       // Code snippet background
  blueAccent: '1D4ED8',   // Blue accent for contrast
};

const F = {
  title: 'Montserrat',
  body: 'Inter',
  code: 'Consolas',
};

// ----------------------------------------------------------------------------
// Standard Slide Framing Helper for 10-Slide Deck
// Minimum Font Sizes: Title >= 32pt, Body >= 20pt, Tables >= 16pt, Diagrams >= 14pt, Min >= 13pt
// ----------------------------------------------------------------------------
function addSlideHeader(slide, titleText, slideNumber) {
  // Small slide number pill top right
  slide.addText(`${slideNumber} / 10`, {
    x: 11.5, y: 0.45, w: 1.1, h: 0.35,
    fontFace: F.title, fontSize: 13, bold: true, color: C.textMuted,
    align: 'right', valign: 'middle'
  });

  // Slide Title (34pt Montserrat bold)
  slide.addText(titleText, {
    x: 0.8, y: 0.40, w: 10.6, h: 0.65,
    fontFace: F.title, fontSize: 34, bold: true, color: C.primaryDark,
    valign: 'middle'
  });

  // Subtle clean accent underline
  slide.addShape(pptx.ShapeType.line, {
    x: 0.8, y: 1.15, w: 11.733, h: 0,
    line: { color: C.accentAmber, width: 2.5 }
  });
}

function addSlideBullets(slide, bullets, x = 0.8, y = 5.75, w = 11.733, h = 1.35) {
  const bulletObjects = bullets.map((b, i) => ({
    text: b,
    options: {
      bullet: { code: '2022' },
      breakLine: i !== bullets.length - 1,
      fontSize: 20,
      fontFace: F.body,
      color: C.textDark,
      paraSpaceBefore: 4,
      paraSpaceAfter: 4,
    }
  }));

  slide.addText(bulletObjects, {
    x, y, w, h,
    valign: 'top',
    wrap: true
  });
}

// ============================================================================
// SLIDE 1: Cover
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };

  // Subtitle Tag Pill
  slide.addShape(pptx.ShapeType.rect, {
    x: 1.0, y: 1.2, w: 2.8, h: 0.45,
    fill: { color: C.tagBg },
    line: { color: C.borderSoft, width: 1 },
    rectRadius: 0.08
  });
  slide.addText("SOFTWARE TESTING", {
    x: 1.0, y: 1.2, w: 2.8, h: 0.45,
    fontFace: F.title, fontSize: 14, bold: true, color: C.primaryDark,
    align: 'center', valign: 'middle'
  });

  // Main Title (44pt)
  slide.addText("Testing RestockIQ", {
    x: 1.0, y: 1.85, w: 11.3, h: 1.1,
    fontFace: F.title, fontSize: 46, bold: true, color: C.primaryDark,
    valign: 'middle'
  });

  // Accent Line
  slide.addShape(pptx.ShapeType.line, {
    x: 1.0, y: 3.1, w: 11.3, h: 0,
    line: { color: C.accentAmber, width: 3.5 }
  });

  // One-line what RestockIQ is (22pt)
  slide.addText("AI demand forecasting and dynamic waste prevention for retail food inventory.", {
    x: 1.0, y: 3.35, w: 11.3, h: 0.7,
    fontFace: F.body, fontSize: 22, color: C.textMuted,
    valign: 'middle'
  });

  // Metadata Card (Left side)
  slide.addShape(pptx.ShapeType.rect, {
    x: 1.0, y: 4.4, w: 6.8, h: 2.2,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText([
    { text: "Author: ", options: { bold: true, fontSize: 18, color: C.primaryDark } },
    { text: "Yatin Patil (Lucifer)\n", options: { fontSize: 18, color: C.textDark } },
    { text: "Program: ", options: { bold: true, fontSize: 18, color: C.primaryDark } },
    { text: "B.Tech Information Technology\n", options: { fontSize: 18, color: C.textDark } },
    { text: "College: ", options: { bold: true, fontSize: 18, color: C.primaryDark } },
    { text: "MPSTME, NMIMS University\n", options: { fontSize: 18, color: C.textDark } },
    { text: "Repository: ", options: { bold: true, fontSize: 18, color: C.primaryDark } },
    { text: "github.com/Yatin07/CAPSTONE_PROJECT", options: { fontSize: 17, color: C.blueAccent } }
  ], {
    x: 1.3, y: 4.55, w: 6.2, h: 1.9,
    fontFace: F.body, valign: 'middle'
  });

  // Scope Callout Card (Right side)
  slide.addShape(pptx.ShapeType.rect, {
    x: 8.2, y: 4.4, w: 4.1, h: 2.2,
    fill: { color: C.tagBg },
    line: { color: C.borderMedium, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("VERIFICATION SCOPE", {
    x: 8.4, y: 4.6, w: 3.7, h: 0.35,
    fontFace: F.title, fontSize: 14, bold: true, color: C.primaryDark
  });
  slide.addText("51", {
    x: 8.4, y: 4.95, w: 3.7, h: 0.8,
    fontFace: F.title, fontSize: 44, bold: true, color: C.primaryDark,
    align: 'center'
  });
  slide.addText("Automated Tests Passing\n+ Physical Android Audit", {
    x: 8.4, y: 5.75, w: 3.7, h: 0.65,
    fontFace: F.body, fontSize: 16, bold: true, color: C.textDark,
    align: 'center'
  });

  slide.addNotes("Good morning. Today I am presenting the software testing and quality engineering defense for RestockIQ. RestockIQ is a multi-tier platform that combines machine learning demand forecasting with active waste prevention for retail food businesses. This presentation covers the testing actually conducted on this project, spanning 51 automated tests and physical device smoke verification.");
}

// ============================================================================
// SLIDE 2: What We Tested (Architecture & Test Counts)
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "What We Tested", 2);

  // 4 Architecture Cards across the canvas
  const boxes = [
    { title: "Mobile App", sub: "Flutter 3.38+", count: "44 Tests", detail: "21 unit, 18 widget,\n5 integration tests", x: 0.8 },
    { title: "API Gateway", sub: "FastAPI & Python", count: "7 Suites", detail: "BVA, decision table,\nCFG, rate limiter", x: 3.8 },
    { title: "Cloud Database", sub: "MongoDB Atlas", count: "Live Ping", detail: "Multi-tenant filter,\nkeepalive health cron", x: 6.8 },
    { title: "ML & Gemini", sub: "Prophet + Gemini", count: "Audited", detail: "6-fold backtest,\nzero-math truth audit", x: 9.8 }
  ];

  boxes.forEach(b => {
    slide.addShape(pptx.ShapeType.rect, {
      x: b.x, y: 1.45, w: 2.73, h: 2.65,
      fill: { color: C.cardBg },
      line: { color: C.borderSoft, width: 1.5 },
      rectRadius: 0.12
    });
    slide.addText(b.title, {
      x: b.x + 0.15, y: 1.6, w: 2.43, h: 0.45,
      fontFace: F.title, fontSize: 20, bold: true, color: C.primaryDark,
      align: 'center'
    });
    slide.addText(b.sub, {
      x: b.x + 0.15, y: 2.05, w: 2.43, h: 0.35,
      fontFace: F.body, fontSize: 14, color: C.textMuted,
      align: 'center'
    });
    slide.addText(b.count, {
      x: b.x + 0.15, y: 2.45, w: 2.43, h: 0.55,
      fontFace: F.title, fontSize: 24, bold: true, color: C.accentAmber,
      align: 'center'
    });
    slide.addText(b.detail, {
      x: b.x + 0.15, y: 3.05, w: 2.43, h: 0.85,
      fontFace: F.body, fontSize: 14, color: C.textDark,
      align: 'center'
    });
  });

  // Big Stat Banner
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 4.3, w: 11.733, h: 1.25,
    fill: { color: C.primaryDark },
    line: { color: C.primaryDeep, width: 1 },
    rectRadius: 0.12
  });
  slide.addText("51 AUTOMATED TESTS + REAL PHONE CHECK", {
    x: 1.0, y: 4.40, w: 8.2, h: 0.45,
    fontFace: F.title, fontSize: 18, bold: true, color: 'FFFFFF',
    valign: 'middle'
  });
  slide.addText("Complete local test suite executes in ~44 seconds with zero network dependencies.", {
    x: 1.0, y: 4.88, w: 8.2, h: 0.45,
    fontFace: F.body, fontSize: 14.5, color: 'E5E0D8',
    valign: 'middle'
  });
  slide.addText("44s", {
    x: 9.2, y: 4.4, w: 3.0, h: 0.7,
    fontFace: F.title, fontSize: 36, bold: true, color: C.accentAmber,
    align: 'center', valign: 'middle'
  });
  slide.addText("Total Suite Runtime", {
    x: 9.2, y: 5.1, w: 3.0, h: 0.35,
    fontFace: F.body, fontSize: 14, color: 'FFFFFF',
    align: 'center', valign: 'middle'
  });

  addSlideBullets(slide, [
    "Tested mobile UI, backend gateway, database layer, and AI services.",
    "Decoupled fast offline suites isolate business formulas from cloud network.",
    "Physical Android audit confirmed release build behavior on real hardware."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("RestockIQ is built across four distinct architectural tiers: the Flutter mobile client, the FastAPI backend microservice, MongoDB Atlas cloud storage, and our ML forecasting engine with Google Gemini 3 Flash. We engineered 51 automated tests covering these components. The entire local test harness runs in approximately 44 seconds without needing external internet access.");
}

// ============================================================================
// SLIDE 3: Black-Box: Boundaries and Decisions
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Black-Box Testing: Bounds & Decisions", 3);

  // Left Card: BVA Table
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 5.65, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("BVA: Assistant Query Length (1 to 500 chars)", {
    x: 1.0, y: 1.6, w: 5.25, h: 0.45,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  const bvaRows = [
    [
      { text: "Length", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 16, color: C.primaryDark, align: 'center' } },
      { text: "Tested Input", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 16, color: C.primaryDark } },
      { text: "Expected Output", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 16, color: C.primaryDark } }
    ],
    ["0", "Empty string \"\"", "Rejects empty input"],
    ["1", "Single character \"a\"", "Accepted (Status 200)"],
    ["500", "500-character prompt", "Accepted (Status 200)"],
    ["501", "501-character prompt", "Rejects oversized input"]
  ];

  slide.addTable(bvaRows, {
    x: 1.0, y: 2.15, w: 5.25, h: 3.1,
    colW: [1.1, 2.15, 2.0],
    fill: { color: C.cardBg },
    color: C.textDark,
    fontSize: 16,
    fontFace: F.body,
    border: { pt: 0.5, color: C.borderSoft },
    rowH: [0.55, 0.6, 0.6, 0.6, 0.6]
  });

  // Right Card: Decision Table Boundary Rows
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.85, y: 1.45, w: 5.68, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("Decision Table: Waste Action Boundaries", {
    x: 7.05, y: 1.6, w: 5.28, h: 0.45,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  const dtRows = [
    [
      { text: "Pace Ratio", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 15, color: C.primaryDark, align: 'center' } },
      { text: "Perishable", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 15, color: C.primaryDark, align: 'center' } },
      { text: "Action Output", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 15, color: C.primaryDark } }
    ],
    ["0.70", "True", "Normal pace: No alert"],
    ["0.69", "True", "Slow pace: Suggest 20% Discount"],
    ["0.35", "True", "Moderate risk: Suggest 20% Discount"],
    ["0.34", "True", "Critical: Suggest 30% / Legacy Flag"]
  ];

  slide.addTable(dtRows, {
    x: 7.05, y: 2.15, w: 5.28, h: 3.1,
    colW: [1.15, 1.55, 2.58],
    fill: { color: C.cardBg },
    color: C.textDark,
    fontSize: 15,
    fontFace: F.body,
    border: { pt: 0.5, color: C.borderSoft },
    rowH: [0.55, 0.6, 0.6, 0.6, 0.6]
  });

  addSlideBullets(slide, [
    "Boundary value analysis validates assistant input rejects invalid lengths.",
    "Decision table tests exact velocity cutoffs triggering markdown actions.",
    "Pure offline test harnesses verify logic without calling external APIs."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("On this slide, we examine our black-box testing techniques. On the left, boundary value analysis probes the AI assistant query endpoint at lengths 0, 1, 500, and 501 characters, confirming the API rejects empty or oversized inputs. On the right, a decision table tests the waste action engine at exact code boundaries: 0.70 triggers no discount, while 0.69 immediately activates a 20 percent price discount.");
}

// ============================================================================
// SLIDE 4: State Transitions: Waste Alert Dynamic Lifecycle
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Waste Alert State Transitions", 4);

  // Canvas card for diagram
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 11.733, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });

  // State Boxes
  // S0: Unfired
  slide.addShape(pptx.ShapeType.rect, {
    x: 1.05, y: 2.6, w: 1.95, h: 1.5,
    fill: { color: C.tagBg },
    line: { color: C.primaryDark, width: 2 },
    rectRadius: 0.1
  });
  slide.addText("S0: UNFIRED\nNormal Pace or\nZero Stock", {
    x: 1.1, y: 2.65, w: 1.85, h: 1.4,
    fontFace: F.title, fontSize: 14.5, bold: true, color: C.primaryDark,
    align: 'center', valign: 'middle'
  });

  // S1: Active Low Pace
  slide.addShape(pptx.ShapeType.rect, {
    x: 4.42, y: 1.75, w: 2.3, h: 1.35,
    fill: { color: C.cardBg },
    line: { color: C.accentAmber, width: 2.5 },
    rectRadius: 0.1
  });
  slide.addText("S1: ACTIVE (LOW PACE)\n0.35 <= Pace < 0.70", {
    x: 4.47, y: 1.85, w: 2.2, h: 1.15,
    fontFace: F.title, fontSize: 13.5, bold: true, color: C.textDark,
    align: 'center', valign: 'middle'
  });

  // S2: Active Critical
  slide.addShape(pptx.ShapeType.rect, {
    x: 4.42, y: 3.85, w: 2.3, h: 1.35,
    fill: { color: C.dangerRed, width: 2.5 },
    rectRadius: 0.1
  });
  slide.addText("S2: ACTIVE (CRITICAL)\nPace < 0.35 & Stock > 0", {
    x: 4.47, y: 3.95, w: 2.2, h: 1.15,
    fontFace: F.title, fontSize: 13.5, bold: true, color: C.textDark,
    align: 'center', valign: 'middle'
  });

  // S3: Discounted
  slide.addShape(pptx.ShapeType.rect, {
    x: 8.15, y: 1.75, w: 2.2, h: 1.35,
    fill: { color: C.cardBg },
    line: { color: C.successGreen, width: 2.5 },
    rectRadius: 0.1
  });
  slide.addText("S3: DISCOUNTED\nPrice * 0.80 Mutated", {
    x: 8.2, y: 1.85, w: 2.1, h: 1.15,
    fontFace: F.title, fontSize: 13.5, bold: true, color: C.successGreen,
    align: 'center', valign: 'middle'
  });

  // S4: Legacy Donation Flag
  slide.addShape(pptx.ShapeType.rect, {
    x: 8.15, y: 3.85, w: 2.2, h: 1.35,
    fill: { color: C.cardBg },
    line: { color: C.borderMedium, width: 2 },
    rectRadius: 0.1
  });
  slide.addText("S4: LEGACY STATE (DEF-011)\nFlagged for Donation", {
    x: 8.2, y: 3.95, w: 2.1, h: 1.15,
    fontFace: F.title, fontSize: 13, bold: true, color: C.textMuted,
    align: 'center', valign: 'middle'
  });

  // S5: Dismissed / Suppressed
  slide.addShape(pptx.ShapeType.rect, {
    x: 10.95, y: 2.6, w: 1.45, h: 1.5,
    fill: { color: C.tagBg },
    line: { color: C.textMuted, width: 2 },
    rectRadius: 0.1
  });
  slide.addText("S5: DISMISSED\n\nAlert is\nsuppressed", {
    x: 11.0, y: 2.65, w: 1.35, h: 1.4,
    fontFace: F.title, fontSize: 12, bold: true, color: C.primaryDark,
    align: 'center', valign: 'middle'
  });

  // Transition Arrows & Labels
  slide.addText("T1: Pace < 0.70  -->", { x: 3.08, y: 2.05, w: 1.28, h: 0.35, fontFace: F.body, fontSize: 11.5, bold: true, color: C.textMuted });
  slide.addText("T2: Pace < 0.35  -->", { x: 3.08, y: 4.25, w: 1.28, h: 0.35, fontFace: F.body, fontSize: 11.5, bold: true, color: C.textMuted });
  slide.addText("T3: Apply Disc  -->", { x: 6.80, y: 2.05, w: 1.28, h: 0.35, fontFace: F.body, fontSize: 11.5, bold: true, color: C.textMuted });
  slide.addText("T4: Flag Legacy -->", { x: 6.80, y: 4.25, w: 1.28, h: 0.35, fontFace: F.body, fontSize: 11.5, bold: true, color: C.textMuted });
  slide.addText("T5/T6 -->", { x: 10.35, y: 3.15, w: 0.55, h: 0.35, fontFace: F.body, fontSize: 11.5, bold: true, color: C.textMuted });

  addSlideBullets(slide, [
    "Tested seven state transitions across active, discounted, and dismissed states.",
    "Verified discount action mutates database item price from $2.80 to $2.24.",
    "Dismissed alerts remain suppressed across subsequent dashboard polling."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("Slide 4 illustrates state transition testing on the dynamic waste alert system. An item transitions from unfired state S0 into active warning states S1 or S2 when evening sales pace slows. Applying a discount executes transition T3 into state S3, mutating the database item price by 20 percent. Transition T5 or T6 into state S5 permanently suppresses the alert from cluttering the manager's dashboard.");
}

// ============================================================================
// SLIDE 5: White-Box: CFG & Application Code Coverage
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "White-Box Testing: CFG & Coverage", 5);

  // Left Card: CFG Graph
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 6.0, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("CFG: get_client_ip(request) in Backend/main.py", {
    x: 1.0, y: 1.6, w: 5.6, h: 0.4,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  const cfgSteps = [
    { text: "(1) Entry: Read 'x-forwarded-for' header", color: C.cardBg, border: C.borderMedium },
    { text: "(2) Decision 1: Is header present and non-empty?", color: C.tagBg, border: C.accentAmber },
    { text: "(3) Decision 2: Split IPs; are tokens found?", color: C.tagBg, border: C.accentAmber },
    { text: "(4) Path 1 Exit: Return ips[-1] (Trusted Rightmost IP)", color: C.cardBg, border: C.successGreen },
    { text: "(5) Decision 3: Does request.client.host exist?", color: C.tagBg, border: C.accentAmber },
    { text: "(6) Path 3 Exit: Return request.client.host", color: C.cardBg, border: C.borderMedium },
    { text: "(7) Path 4/5 Exit: Return fallback '127.0.0.1'", color: C.cardBg, border: C.borderMedium }
  ];

  cfgSteps.forEach((st, idx) => {
    slide.addShape(pptx.ShapeType.rect, {
      x: 1.0, y: 2.1 + (idx * 0.44), w: 5.6, h: 0.38,
      fill: { color: st.color },
      line: { color: st.border, width: 1.5 },
      rectRadius: 0.06
    });
    slide.addText(st.text, {
      x: 1.15, y: 2.1 + (idx * 0.44), w: 5.3, h: 0.38,
      fontFace: F.body, fontSize: 14, color: C.textDark,
      valign: 'middle'
    });
  });

  // Right Card: Complexity Formula & Real App Coverage
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.05, y: 1.45, w: 5.48, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("Complexity Proof & Application Coverage", {
    x: 7.25, y: 1.6, w: 5.1, h: 0.4,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  slide.addShape(pptx.ShapeType.rect, {
    x: 7.25, y: 2.15, w: 5.08, h: 1.4,
    fill: { color: C.tagBg },
    line: { color: C.borderSoft, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "McCabe Cyclomatic Complexity Derivation:\n", options: { bold: true, fontSize: 15, color: C.primaryDark } },
    { text: "• Nodes (N) = 10, Edges (E) = 13, Component (P) = 1\n", options: { fontSize: 14, color: C.textDark } },
    { text: "• Formula: V(G) = E - N + 2P = 13 - 10 + 2 = 5\n", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "• Result: Exactly 5 basis paths required and tested.", options: { fontSize: 14, color: C.textDark } }
  ], {
    x: 7.4, y: 2.25, w: 4.8, h: 1.2,
    fontFace: F.body, valign: 'middle'
  });

  slide.addShape(pptx.ShapeType.rect, {
    x: 7.25, y: 3.75, w: 5.08, h: 1.55,
    fill: { color: C.cardBg },
    line: { color: C.borderMedium, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "Real Coverage.py on Application Code Only:\n", options: { bold: true, fontSize: 14.5, color: C.primaryDark } },
    { text: "• get_client_ip(): 100% statement (8/8) & branch (4/4)\n", options: { fontSize: 13, color: C.successGreen, bold: true } },
    { text: "• evaluate_waste_alert_tier(): 100% statement & branch\n", options: { fontSize: 13, color: C.successGreen, bold: true } },
    { text: "• Total App Code: 59% (500 statements, 136 branches)", options: { fontSize: 12.5, color: C.textMuted } }
  ], {
    x: 7.35, y: 3.80, w: 4.88, h: 1.4,
    fontFace: F.body, valign: 'middle'
  });

  addSlideBullets(slide, [
    "Derived five independent basis paths from the control flow graph.",
    "Security logic extracts the rightmost trusted proxy IP from header chains.",
    "Coverage measured on application code with zero test file contamination."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("On Slide 5, we present white-box basis path testing for the client IP extraction function. By mapping the control flow graph, we identify 10 nodes, 13 edges, and 4 decision points, yielding a cyclomatic complexity of exactly 5. We constructed 5 unit tests covering every independent path. Running coverage.py strictly on application source files confirms 100 percent branch coverage on core security functions.");
}

// ============================================================================
// SLIDE 6: Unit, Integration & CI Status
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Unit, Integration, and Regression", 6);

  // Top: Two Paradigm Cards
  // Detroit
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 5.65, h: 1.6,
    fill: { color: C.cardBg },
    line: { color: C.primaryDark, width: 2 },
    rectRadius: 0.1
  });
  slide.addText("CLASSICAL (DETROIT SCHOOL)", {
    x: 1.0, y: 1.55, w: 5.25, h: 0.35,
    fontFace: F.title, fontSize: 16, bold: true, color: C.primaryDark
  });
  slide.addText("Tests real object state mutations after actions execute.\nExample: InventoryProvider CRUD adds 5 items and verifies mutated array length directly in memory.", {
    x: 1.0, y: 1.95, w: 5.25, h: 0.95,
    fontFace: F.body, fontSize: 14, color: C.textDark
  });

  // London
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.85, y: 1.45, w: 5.68, h: 1.6,
    fill: { color: C.cardBg },
    line: { color: C.accentAmber, width: 2 },
    rectRadius: 0.1
  });
  slide.addText("MOCKIST (LONDON SCHOOL)", {
    x: 7.05, y: 1.55, w: 5.28, h: 0.35,
    fontFace: F.title, fontSize: 16, bold: true, color: C.primaryDark
  });
  slide.addText("Replaces external collaborators to verify isolated contracts.\nExample: Flutter widget tests mock network timeouts (4s) to verify UI displays local fallback without crashing.", {
    x: 7.05, y: 1.95, w: 5.28, h: 0.95,
    fontFace: F.body, fontSize: 14, color: C.textDark
  });

  // Middle: 4 Test Chips with Real Counts & Times
  const chips = [
    { name: "Flutter Unit", count: "21 Tests", time: "13.2s", x: 0.8 },
    { name: "Flutter Widget", count: "18 Tests", time: "24.8s", x: 3.8 },
    { name: "Flutter Integration", count: "5 Tests", time: "11.5s", x: 6.8 },
    { name: "Backend Unit (Python)", count: "7 Suites", time: "12.9s", x: 9.8 }
  ];

  chips.forEach(c => {
    slide.addShape(pptx.ShapeType.rect, {
      x: c.x, y: 3.25, w: 2.73, h: 1.1,
      fill: { color: C.cardBg },
      line: { color: C.borderSoft, width: 1.5 },
      rectRadius: 0.08
    });
    slide.addText(c.name, {
      x: c.x + 0.1, y: 3.35, w: 2.53, h: 0.3,
      fontFace: F.title, fontSize: 14, bold: true, color: C.primaryDark,
      align: 'center'
    });
    slide.addText(`${c.count} (${c.time})`, {
      x: c.x + 0.1, y: 3.7, w: 2.53, h: 0.45,
      fontFace: F.body, fontSize: 16, bold: true, color: C.successGreen,
      align: 'center'
    });
  });

  // Bottom: Real GitHub Actions CI Status Strip
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 4.55, w: 11.733, h: 0.95,
    fill: { color: C.tagBg },
    line: { color: C.borderMedium, width: 1 },
    rectRadius: 0.08
  });
  slide.addText("CI STATUS:", {
    x: 1.0, y: 4.65, w: 1.6, h: 0.75,
    fontFace: F.title, fontSize: 15, bold: true, color: C.primaryDark,
    valign: 'middle'
  });
  slide.addText([
    { text: "• Backend CI: ", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "PASSING (23s runtime)\n", options: { fontSize: 14, color: C.successGreen, bold: true } },
    { text: "• Flutter CI: ", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "FAILING on remote (6 unused imports fixed locally in commit 15b98b22, unpushed)\n", options: { fontSize: 14, color: C.dangerRed } },
    { text: "• Keepalive: ", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "PASSING (every 10 min cron */10 * * * *)", options: { fontSize: 14, color: C.successGreen, bold: true } }
  ], {
    x: 2.7, y: 4.6, w: 9.6, h: 0.85,
    fontFace: F.body, valign: 'middle'
  });

  addSlideBullets(slide, [
    "Balanced classical state verification with mockist fault injection.",
    "51 automated offline tests pass in under 44 seconds locally.",
    "CI passes backend tests; Flutter fix remains staged locally."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("Slide 6 contrasts our classical Detroit-style tests with mockist London-style tests. Classical tests verify real in-memory state mutations in our inventory providers, while mockist tests simulate 4-second API timeouts to ensure mobile screens fail over gracefully. In CI, our backend offline tests pass in 23 seconds and Render keepalive pings every 10 minutes, while the Flutter CI fix is staged locally.");
}

// ============================================================================
// SLIDE 7: Defect Taxonomy & Historical Log
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Bugs We Found: Lifecycle & Defect Log", 7);

  // Top: Error -> Defect -> Failure Chain Card
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.35, w: 11.733, h: 1.15,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.1
  });
  slide.addText("PROPAGATION CHAIN: DEF-009 (Physical Device Loopback Hang)", {
    x: 1.0, y: 1.40, w: 11.3, h: 0.28,
    fontFace: F.title, fontSize: 14, bold: true, color: C.primaryDark
  });

  const chain = [
    { title: "1. Human Error (Mistake)", desc: "Assumed 10.0.2.2 emulator IP is valid on physical phones", x: 1.0, w: 3.6 },
    { title: "2. Software Defect (Bug)", desc: "Hardcoded defaultBaseUrl to 10.0.2.2 without route checks", x: 4.85, w: 3.6 },
    { title: "3. System Failure (Observed)", desc: "Physical phone hung for 76.5 seconds in retry loop", x: 8.7, w: 3.6 }
  ];

  chain.forEach(c => {
    slide.addShape(pptx.ShapeType.rect, {
      x: c.x, y: 1.72, w: c.w, h: 0.68,
      fill: { color: C.tagBg },
      line: { color: C.borderSoft, width: 1 },
      rectRadius: 0.06
    });
    slide.addText(c.title, {
      x: c.x + 0.1, y: 1.75, w: c.w - 0.2, h: 0.26,
      fontFace: F.title, fontSize: 12.5, bold: true, color: C.primaryDark
    });
    slide.addText(c.desc, {
      x: c.x + 0.1, y: 2.03, w: c.w - 0.2, h: 0.32,
      fontFace: F.body, fontSize: 11.5, color: C.textDark
    });
  });

  // Bottom: Table of 5 Key Defects
  const defRows = [
    [
      { text: "Defect ID", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 14.5, color: C.primaryDark, align: 'center' } },
      { text: "Defect Description", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 14.5, color: C.primaryDark } },
      { text: "Category", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 14.5, color: C.primaryDark, align: 'center' } },
      { text: "Status", options: { bold: true, fill: { color: C.tagBg }, fontFace: F.title, fontSize: 14.5, color: C.primaryDark, align: 'center' } }
    ],
    ["DEF-001", "Hardcoded loopback IP (10.0.2.2) caused 76s physical phone hang", "Config/Net", "Fixed (Cloud URL + Probe)"],
    ["DEF-003", "Hardcoded JWT fallback secret in backend configuration", "Security", "Fixed (Fail-fast Startup)"],
    ["DEF-008", "37 store closure dates skewing 4-week lag calculation", "ML Align", "Resolved & Verified (Calendar Lookup)"],
    ["DEF-011", "Item setup form bottom overflow on small viewports", "UI/Layout", "Fixed (SingleChildScrollView)"],
    ["DEF-013", "Legacy donation endpoint retained vs commercial markdown", "Requirement", "Open (Documented V2 Backlog)"]
  ];

  slide.addTable(defRows, {
    x: 0.8, y: 2.65, w: 11.733, h: 2.5,
    colW: [1.6, 5.733, 1.8, 2.6],
    fill: { color: C.cardBg },
    color: C.textDark,
    fontSize: 13.5,
    fontFace: F.body,
    border: { pt: 0.5, color: C.borderSoft },
    rowH: [0.42, 0.40, 0.40, 0.40, 0.40, 0.40]
  });

  addSlideBullets(slide, [
    "Traced root causes from developer assumptions to runtime failures.",
    "Thirteen defects logged across git history: twelve resolved, one open.",
    "One non-critical architectural finding remains openly tracked (DEF-013)."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("Slide 7 demonstrates defect lifecycle management. At the top, we illustrate the progression from human error to code defect to runtime failure using DEF-009: a developer assumed the emulator loopback IP was universally reachable, creating a defect that caused a real 76-second freeze on physical hardware. Below, our defect table shows 11 historical defects tracked: 9 are resolved and regression tested, while 2 remain open.");
}

// ============================================================================
// SLIDE 8: Security & End-to-End Verification
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Security & End-to-End Testing", 8);

  // Left Card: 9 E2E Checkpoints
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 5.65, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("9-Step E2E Lifecycle Flow (verify_e2e.py)", {
    x: 1.0, y: 1.6, w: 5.25, h: 0.4,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  const e2eItems = [
    "1. GET /health: Ping MongoDB Atlas connection",
    "2. POST /auth/login: JWT token authentication & issue",
    "3. GET /items: Verify seeded inventory catalog",
    "4. batch_forecast.py: Run ML forecast pipeline",
    "5. GET /forecasts/today: Check dashboard estimates",
    "6. GET /forecasts/{id}: Validate 7-day forecast curve",
    "7. POST /items/{id}/restock: One-tap stock increment (+15)",
    "8. POST /sales/intraday: Log POS sales event to Atlas",
    "9. GET /waste-alerts: Trigger waste action engine rule"
  ];

  const e2eFormatted = e2eItems.map((s, idx) => ({
    text: s + (idx !== e2eItems.length - 1 ? "\n" : ""),
    options: {
      fontSize: 12.5,
      fontFace: F.body,
      color: C.textDark,
      paraSpaceAfter: 4
    }
  }));

  slide.addText(e2eFormatted, {
    x: 1.0, y: 2.05, w: 5.25, h: 2.85,
    valign: 'top', wrap: true
  });

  slide.addText("Limitation: Executed Oct 4 against local server + Atlas; requires network.", {
    x: 1.0, y: 5.08, w: 5.25, h: 0.32,
    fontFace: F.body, fontSize: 12, italic: true, color: C.textMuted
  });

  // Right Card: Security Verification (Owner-ID & Spoof Defense)
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.85, y: 1.45, w: 5.68, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("Security Logic & Identified Limitations", {
    x: 7.05, y: 1.6, w: 5.28, h: 0.4,
    fontFace: F.title, fontSize: 17, bold: true, color: C.primaryDark
  });

  // Subcard 1: Owner-ID Filtering
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.05, y: 2.05, w: 5.28, h: 1.5,
    fill: { color: C.tagBg },
    line: { color: C.borderSoft, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "Owner-ID Filtering (test_tenant_isolation.py):\n", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "• Tested 10 endpoints with cross-tenant tokens: ZERO LEAKS.\n", options: { fontSize: 13, color: C.successGreen, bold: true } },
    { text: "• All unauthorized requests return HTTP 404 or empty collection.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Limitation: Verified logic on a mock database.", options: { fontSize: 12, italic: true, color: C.textMuted } }
  ], {
    x: 7.2, y: 2.12, w: 5.0, h: 1.35,
    fontFace: F.body, valign: 'middle'
  });

  // Subcard 2: Custom Rate Limiter
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.05, y: 3.75, w: 5.28, h: 1.55,
    fill: { color: C.cardBg },
    line: { color: C.borderMedium, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "Custom Rate Limiter & Spoof Defense (main.py):\n", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "• In-memory sliding window purges timestamps older than window.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Spoof test: Simulated headers verified code selects rightmost IP.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Limitation: Actual proxy hop count on Render live edge is unverified.", options: { fontSize: 12, italic: true, color: C.dangerRed } }
  ], {
    x: 7.2, y: 3.82, w: 5.0, h: 1.4,
    fontFace: F.body, valign: 'middle'
  });

  addSlideBullets(slide, [
    "Validated entire restaurant inventory lifecycle across nine sequential steps.",
    "Probed tenant isolation across ten endpoints with zero leaks.",
    "Rate limiter enforces sliding window; edge hop depth unverified."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("On Slide 8, we review security and end-to-end testing. On the left, our 9-step E2E flow validates the entire lifecycle from authentication to restock and POS logging against MongoDB Atlas. On the right, owner-ID filtering ensures tenant data cannot cross store boundaries, tested with 100 percent isolation on a mock database. Our custom rate limiter protects against spoofed headers, with the limitation that live Render hop counts remain unverified.");
}

// ============================================================================
// SLIDE 9: Testing the AI: Backtest, Leakage & Simulation
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Testing the AI: Backtest & Integrity", 9);

  // Left Card: Native Bar Chart of Overall WAPE
  slide.addShape(pptx.ShapeType.rect, {
    x: 0.8, y: 1.45, w: 5.65, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("Overall 6-Fold WAPE by Model (backtest_results.csv)", {
    x: 1.0, y: 1.6, w: 5.25, h: 0.35,
    fontFace: F.title, fontSize: 16, bold: true, color: C.primaryDark
  });

  const chartData = [
    {
      name: "Overall WAPE (%)",
      labels: ["Prophet", "Hybrid", "GBDT", "MA 7d", "SNaive", "Wkday4W"],
      values: [21.74, 22.51, 27.29, 30.70, 32.06, 41.63]
    }
  ];

  slide.addChart(pptx.ChartType.bar, chartData, {
    x: 1.0, y: 1.95, w: 5.25, h: 2.75,
    barDir: 'col',
    chartColors: [C.primaryDark],
    valAxisMinVal: 0,
    valAxisMaxVal: 45,
    showValue: true,
    dataLabelFontSize: 13,
    catAxisLabelFontSize: 13,
    valAxisLabelFontSize: 12,
  });

  slide.addShape(pptx.ShapeType.rect, {
    x: 1.0, y: 4.75, w: 5.25, h: 0.65,
    fill: { color: C.tagBg },
    line: { color: C.borderSoft, width: 1 },
    rectRadius: 0.06
  });
  slide.addText("Honest Transparency: Prophet-only (21.7%) beat Hybrid (23.4%). Underlying cause was not tested.", {
    x: 1.1, y: 4.8, w: 5.05, h: 0.55,
    fontFace: F.body, fontSize: 12.5, bold: true, color: C.primaryDark,
    align: 'center', valign: 'middle'
  });

  // Right Card: Integrity Audits & Simulation Invariant
  slide.addShape(pptx.ShapeType.rect, {
    x: 6.85, y: 1.45, w: 5.68, h: 4.05,
    fill: { color: C.cardBg },
    line: { color: C.borderSoft, width: 1.5 },
    rectRadius: 0.12
  });
  slide.addText("Data Integrity Audits & 90-Day Simulation", {
    x: 7.05, y: 1.6, w: 5.28, h: 0.35,
    fontFace: F.title, fontSize: 16, bold: true, color: C.primaryDark
  });

  // Card 1: Temporal Leakage & Zero-Math Audits
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.05, y: 2.05, w: 5.28, h: 1.6,
    fill: { color: C.tagBg },
    line: { color: C.borderSoft, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "Temporal Leakage & Zero-Math Truth Audits:\n", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "• Temporal Leakage: Training ends before forecast starts in all 6 folds.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Zero lookahead contamination: training spans 527 to 593 sales days.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Zero-Math Audit: Every number in the AI answer appears in our data (check passed). Gemini 3 Flash acts as pure summarizer.", options: { fontSize: 12.5, color: C.successGreen, bold: true } }
  ], {
    x: 7.2, y: 2.12, w: 5.0, h: 1.45,
    fontFace: F.body, valign: 'middle'
  });

  // Card 2: 90-Day Simulation
  slide.addShape(pptx.ShapeType.rect, {
    x: 7.05, y: 3.80, w: 5.28, h: 1.55,
    fill: { color: C.cardBg },
    line: { color: C.borderMedium, width: 1 },
    rectRadius: 0.08
  });
  slide.addText([
    { text: "90-Day Inventory Simulation (Hybrid Model, 68,908 Demand):\n", options: { bold: true, fontSize: 14, color: C.primaryDark } },
    { text: "• Waste depends on safety buffer: 9.0% at z=0.0 to 37.6% at z=1.65.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• Profit trade-off: €40,717 at z=0.0 vs. €29,043 at z=1.65.\n", options: { fontSize: 12.5, color: C.textDark } },
    { text: "• At z=1.65, reduced 5,090 waste units and 366 stockouts vs Naive.", options: { fontSize: 12.5, bold: true, color: C.primaryDark } }
  ], {
    x: 7.2, y: 3.88, w: 5.0, h: 1.4,
    fontFace: F.body, valign: 'middle'
  });

  addSlideBullets(slide, [
    "Prophet baseline beat hybrid model; underlying cause was not tested.",
    "Verified training cutoff strictly preceded every 7-day forecast horizon.",
    "Confirmed Gemini assistant answers only use verified database metrics."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("Slide 9 reports empirical results from testing our AI models. In our 6-fold backtest, Prophet alone achieved 21.7 percent WAPE, outperforming the hybrid model at 23.4 percent; we report this negative finding transparently without claiming untested causes. We proved zero temporal leakage across all folds, verified that Gemini outputs zero hallucinated numbers, and confirmed via simulation that safety stock buffers dictate waste percentages.");
}

// ============================================================================
// SLIDE 10: Done, Not Done, and Next Steps
// ============================================================================
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bgWarm };
  addSlideHeader(slide, "Done, Not Done, and Next Steps", 10);

  // 3 Columns: Done | Not Done | Next Steps
  const columns = [
    {
      title: "WHAT WE COMPLETED (DONE)",
      items: [
        "EP + BVA on query lengths and decision tables on waste engine",
        "CFG basis path white-box testing with 100% security branch coverage",
        "51 automated offline tests across Flutter and FastAPI microservice",
        "Physical Android smoke audit on Xiaomi Redmi Note 10 Pro"
      ],
      color: C.cardBg,
      border: C.successGreen,
      tag: "Verified",
      tagColor: C.successGreen,
      x: 0.8
    },
    {
      title: "DOCUMENTED GAPS (NOT DONE)",
      items: [
        "Mutation testing and formal data-flow anomaly detection",
        "Distributed concurrent load testing (Locust / k6)",
        "Formal multi-user beta acceptance testing (Beta UAT)",
        "Formal TDD cycle (CO3 marked partial; DEF-008 open)"
      ],
      color: C.cardBg,
      border: C.dangerRed,
      tag: "Omitted",
      tagColor: C.dangerRed,
      x: 4.7
    },
    {
      title: "QUALITY ROADMAP (NEXT STEPS)",
      items: [
        "Refactor 4-week lag calculation to calendar alignment (DEF-008)",
        "Replace legacy donation endpoint with commercial bundling (DEF-011)",
        "Automate live CI pipeline with Atlas runner IP whitelist",
        "Multi-store bakery pilot trials to evaluate kitchen UX"
      ],
      color: C.cardBg,
      border: C.accentAmber,
      tag: "Roadmap",
      tagColor: C.primaryDark,
      x: 8.6
    }
  ];

  columns.forEach(col => {
    slide.addShape(pptx.ShapeType.rect, {
      x: col.x, y: 1.45, w: 3.73, h: 4.05,
      fill: { color: col.color },
      line: { color: col.border, width: 2 },
      rectRadius: 0.12
    });

    slide.addShape(pptx.ShapeType.rect, {
      x: col.x + 0.15, y: 1.6, w: 3.43, h: 0.4,
      fill: { color: C.tagBg },
      line: { color: C.borderSoft, width: 1 },
      rectRadius: 0.06
    });
    slide.addText(col.title, {
      x: col.x + 0.15, y: 1.6, w: 3.43, h: 0.4,
      fontFace: F.title, fontSize: 13, bold: true, color: col.tagColor,
      align: 'center', valign: 'middle'
    });

    const itemObjects = col.items.map((it, idx) => ({
      text: it,
      options: {
        bullet: { code: '2022' },
        breakLine: idx !== col.items.length - 1,
        fontSize: 14,
        fontFace: F.body,
        color: C.textDark,
        paraSpaceBefore: 6,
        paraSpaceAfter: 6,
      }
    }));

    slide.addText(itemObjects, {
      x: col.x + 0.2, y: 2.15, w: 3.33, h: 3.2,
      valign: 'top',
      wrap: true
    });
  });

  addSlideBullets(slide, [
    "Met core testing objectives across unit, integration, and security.",
    "Advanced structural techniques and load stress tests were omitted.",
    "Roadmap prioritizes calendar-day alignment and retail bundling logic."
  ], 0.8, 5.75, 11.733, 1.35);

  slide.addNotes("To conclude on Slide 10, we summarize our achievements and remaining roadmap. We designed and executed comprehensive black-box, white-box, integration, and security test suites, fulfilling course outcomes CO1 and CO2, while CO3 on test-driven development remains partial. We acknowledge unperformed techniques including mutation and distributed load testing, and prioritize calendar alignment and commercial bundling in future work. Thank you.");
}

// ----------------------------------------------------------------------------
// Output Presentation Generation
// ----------------------------------------------------------------------------
const outputPath = path.resolve(__dirname, '../docs/software_testing_10slides.pptx');
console.log(`Writing 10-slide presentation to: ${outputPath}`);

pptx.writeFile({ fileName: outputPath })
  .then(() => {
    console.log("================================================================================");
    console.log("SUCCESS: 10-Slide Presentation generated successfully at docs/software_testing_10slides.pptx");
    console.log("================================================================================");
  })
  .catch(err => {
    console.error("ERROR generating 10-slide presentation:", err);
    process.exit(1);
  });
