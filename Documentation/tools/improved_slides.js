const pptxgen = require("pptxgenjs");

const RED_BAR   = "C62829";
const RED_BOX   = "BB302C";
const NAVY      = "2E3B7D";
const GRAY_BG   = "F7F5F4";
const GRAY_LN   = "D9D9D9";
const TEXT_DARK = "3A3A3A";

let pres = new pptxgen();
pres.defineLayout({ name: "NMIMS", width: 10.8333, height: 7.5 });
pres.layout = "NMIMS";

function addHeader(slide, pageNum) {
  slide.background = { color: "FFFFFF" };
  
  // Top Red Bar
  slide.addShape("rect", { x: 0, y: 0, w: 10.8333, h: 0.72, fill: { color: RED_BAR }, line: { type: "none" } });
  
  // White Box for Logo (Assuming logo is left aligned)
  slide.addShape("rect", { x: 0, y: 0, w: 2.55, h: 0.92, fill: { color: "FFFFFF" }, line: { type: "none" } });
  
  // We'll leave the image out if it doesn't exist, but we can add a placeholder text for NMIMS Logo
  slide.addText("NMIMS LOGO", {
    x: 0.1, y: 0.2, w: 2.06, h: 0.5,
    fontFace: "Arial", fontSize: 14, bold: true, color: RED_BAR, align: "center", valign: "middle"
  });

  // Header Title
  slide.addText("MUKESH PATEL SCHOOL OF TECHNOLOGY MANAGEMENT & ENGINEERING, SHIRPUR", {
    x: 2.65, y: 0, w: 8.05, h: 0.72, isTextBox: true, margin: 0,
    fontFace: "Georgia", fontSize: 11, bold: true, color: "FFFFFF",
    align: "left", valign: "middle"
  });

  // Bottom Red Bar
  slide.addShape("rect", { x: 0, y: 7.42, w: 10.8333, h: 0.08, fill: { color: RED_BAR }, line: { type: "none" } });
  
  if (pageNum) {
    slide.addText(String(pageNum), {
      x: 10.3, y: 7.14, w: 0.4, h: 0.26, isTextBox: true, margin: 0,
      fontFace: "Georgia", fontSize: 11, color: "999999", align: "right"
    });
  }
}

function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.4, y: 0.9, w: 10.0, h: 0.5, isTextBox: true, margin: 0,
    fontFace: "Georgia", fontSize: 26, bold: true, color: RED_BOX
  });
  
  // Subtle decorative line under title
  slide.addShape("rect", { x: 0.4, y: 1.45, w: 1.5, h: 0.04, fill: { color: RED_BAR }, line: { type: "none" } });
  slide.addShape("rect", { x: 1.9, y: 1.45, w: 8.5, h: 0.01, fill: { color: GRAY_LN }, line: { type: "none" } });

  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.4, y: 1.55, w: 10.0, h: 0.35, isTextBox: true, margin: 0,
      fontFace: "Georgia", italic: true, fontSize: 14, color: NAVY
    });
  }
}

/* =========================================================================
   SLIDE 1: Requirement Analysis (Object-Oriented Analysis)
   ========================================================================= */
let s1 = pres.addSlide();
addHeader(s1, 7);
addTitle(s1, "Requirement Analysis", "Object-Oriented Analysis");

// -------------------------------------------------------------------------
// Left Panel: Main User (The Business Owner)
// -------------------------------------------------------------------------
const userX = 0.4, userY = 2.2, userW = 3.2, userH = 4.8;

// Navy Card Background
s1.addShape("rect", {
  x: userX, y: userY, w: userW, h: userH,
  fill: { color: NAVY },
  rectRadius: 0.15,
  shadow: { type: "outer", color: "666666", opacity: 0.3, blur: 5, offset: 3, angle: 45 }
});

// User Icon / Avatar Graphic
const cx = userX + userW / 2;
// A subtle circle behind the avatar
s1.addShape("ellipse", { x: cx - 0.7, y: userY + 0.5, w: 1.4, h: 1.4, fill: { color: "FFFFFF", transparency: 90 } });
s1.addShape("ellipse", { x: cx - 0.5, y: userY + 0.65, w: 1.0, h: 1.0, fill: { color: "FFFFFF" } });
// Shoulders
s1.addShape("ellipse", { x: cx - 0.8, y: userY + 1.7, w: 1.6, h: 0.8, fill: { color: "FFFFFF" } });

// Main User Title
s1.addText("PRIMARY ACTOR", {
  x: userX, y: userY + 2.6, w: userW, h: 0.3,
  fontFace: "Georgia", fontSize: 11, bold: true, color: "A9B4E4", align: "center", charSpacing: 2
});

s1.addText("Business Owner", {
  x: userX, y: userY + 2.9, w: userW, h: 0.5,
  fontFace: "Georgia", fontSize: 22, bold: true, color: "FFFFFF", align: "center"
});

// Description Box inside the Navy Card
s1.addShape("rect", {
  x: userX + 0.2, y: userY + 3.6, w: userW - 0.4, h: 0.9,
  fill: { color: "FFFFFF", transparency: 15 }, rectRadius: 0.1
});
s1.addText("Small food-business owner (e.g., cafe, bakery, or independent restaurant). Requires simple, actionable insights without deep technical expertise.", {
  x: userX + 0.3, y: userY + 3.65, w: userW - 0.6, h: 0.8,
  fontFace: "Georgia", fontSize: 11, color: "FFFFFF", align: "center", lineSpacingMultiple: 1.2
});


// -------------------------------------------------------------------------
// Right Panel: User Requirements Grid
// -------------------------------------------------------------------------
const reqX = userX + userW + 0.4;
const reqY = 2.2;
const reqW = 10.8333 - reqX - 0.4;

s1.addText("System Requirements", {
  x: reqX, y: reqY - 0.1, w: reqW, h: 0.4,
  fontFace: "Georgia", fontSize: 18, bold: true, color: RED_BOX
});
s1.addText("The system should allow the owner to securely and easily:", {
  x: reqX, y: reqY + 0.3, w: reqW, h: 0.3,
  fontFace: "Georgia", italic: true, fontSize: 12, color: TEXT_DARK
});

const reqs = [
  "Register and log in securely.",
  "Create and manage shop information.",
  "Upload/enter historical sales data.",
  "Maintain current inventory records.",
  "Select specific food items for tracking.",
  "Generate item-level demand forecasts.",
  "View predicted demand visually.",
  "Receive daily restock recommendations.",
  "View plain-language explanations of forecasts.",
  "Access historical forecasting & inventory logs."
];

// Draw a grid of modern cards for requirements
const colCount = 2;
const cardW = (reqW - 0.2) / colCount;
const cardH = 0.65;
const startY = reqY + 0.8;
const gapY = 0.15;
const gapX = 0.2;

reqs.forEach((r, idx) => {
  const col = idx % colCount;
  const row = Math.floor(idx / colCount);
  const cx = reqX + (col * (cardW + gapX));
  const cy = startY + (row * (cardH + gapY));

  // Card background
  s1.addShape("rect", {
    x: cx, y: cy, w: cardW, h: cardH,
    fill: { color: GRAY_BG },
    line: { color: GRAY_LN, width: 0.5 },
    rectRadius: 0.05
  });
  
  // Left Accent Bar for card
  s1.addShape("rect", {
    x: cx, y: cy, w: 0.08, h: cardH,
    fill: { color: NAVY },
    rectRadius: 0.02
  });

  // Checkmark/Bullet replacement (small red square or circle)
  s1.addShape("ellipse", {
    x: cx + 0.15, y: cy + (cardH/2) - 0.05, w: 0.1, h: 0.1,
    fill: { color: RED_BOX }
  });

  // Requirement Text
  s1.addText(r, {
    x: cx + 0.35, y: cy + 0.05, w: cardW - 0.4, h: cardH - 0.1,
    fontFace: "Georgia", fontSize: 11, color: TEXT_DARK, align: "left", valign: "middle"
  });
});


/* =========================================================================
   SLIDE 2: Functional & Non-Functional Requirements
   ========================================================================= */
let s2 = pres.addSlide();
addHeader(s2, 8);
addTitle(s2, "Functional & Non-Functional Requirements", "System Specifications");

const colY = 2.1;
const colWidth = 4.8;
const colGap = 0.4;
const fX = 0.4;
const nX = fX + colWidth + colGap;

// Functional Header
s2.addShape("rect", { x: fX, y: colY, w: colWidth, h: 0.5, fill: { color: RED_BOX }, rectRadius: 0.1 });
s2.addText("Functional Requirements", {
  x: fX, y: colY, w: colWidth, h: 0.5,
  fontFace: "Georgia", fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle"
});

// Non-Functional Header
s2.addShape("rect", { x: nX, y: colY, w: colWidth, h: 0.5, fill: { color: NAVY }, rectRadius: 0.1 });
s2.addText("Non-Functional Requirements", {
  x: nX, y: colY, w: colWidth, h: 0.5,
  fontFace: "Georgia", fontSize: 16, bold: true, color: "FFFFFF", align: "center", valign: "middle"
});

// Helper for beautiful requirement rows
function addReqRow(slide, x, y, w, h, id, title, desc, accentColor) {
  // Container card
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: "FFFFFF" },
    line: { color: GRAY_LN, width: 0.5 },
    shadow: { type: "outer", color: "999999", opacity: 0.15, blur: 3, offset: 2, angle: 90 }
  });

  // ID Tag (e.g. FR1)
  slide.addShape("rect", {
    x: x + 0.1, y: y + 0.1, w: 0.6, h: 0.25,
    fill: { color: accentColor },
    rectRadius: 0.05
  });
  slide.addText(id, {
    x: x + 0.1, y: y + 0.1, w: 0.6, h: 0.25,
    fontFace: "Georgia", fontSize: 9, bold: true, color: "FFFFFF", align: "center", valign: "middle"
  });

  // Title
  slide.addText(title, {
    x: x + 0.8, y: y + 0.05, w: w - 0.9, h: 0.3,
    fontFace: "Georgia", fontSize: 11, bold: true, color: TEXT_DARK, align: "left"
  });

  // Description
  slide.addText(desc, {
    x: x + 0.8, y: y + 0.3, w: w - 0.9, h: h - 0.3,
    fontFace: "Georgia", fontSize: 10, color: "555555", align: "left", valign: "top", lineSpacingMultiple: 1.1
  });
}

const fReqs = [
  { id: "FR1", title: "User Authentication", desc: "Register and securely log in." },
  { id: "FR2", title: "Shop Management", desc: "Create and manage shop information." },
  { id: "FR3", title: "Sales Data", desc: "Upload or enter historical item-level sales data." },
  { id: "FR4", title: "Inventory Mgmt.", desc: "Provide and manage current inventory information." },
  { id: "FR5", title: "Forecast Gen.", desc: "Generate item-level daily demand forecasts." },
  { id: "FR6", title: "External Data", desc: "Use weather/holiday info as external factors (Planned)." },
  { id: "FR7", title: "Restock Rec.", desc: "Calculate restock using demand, stock & safety limits." },
  { id: "FR8", title: "Explanation", desc: "Provide plain-language explanation of recommendations." }
];

const nReqs = [
  { id: "NFR1", title: "Performance", desc: "Forecast generation should complete within reasonable time." },
  { id: "NFR2", title: "Usability", desc: "Simple and easy to use for non-technical business owners." },
  { id: "NFR3", title: "Scalability", desc: "Support multiple food items for a single business effortlessly." },
  { id: "NFR4", title: "Reliability", desc: "Provide consistent and accurate results for valid inputs." },
  { id: "NFR5", title: "Security", desc: "Protect user authentication and sensitive business data." },
  { id: "NFR6", title: "Maintainability", desc: "Modular architecture separating ML, API, and UI layers." },
  { id: "NFR7", title: "Portability", desc: "Support cross-platform deployment natively using Flutter." }
];

let currY_F = colY + 0.7;
fReqs.forEach(req => {
  addReqRow(s2, fX, currY_F, colWidth, 0.48, req.id, req.title, req.desc, RED_BOX);
  currY_F += 0.55;
});

let currY_N = colY + 0.7;
nReqs.forEach(req => {
  addReqRow(s2, nX, currY_N, colWidth, 0.48, req.id, req.title, req.desc, NAVY);
  currY_N += 0.55;
});

pres.writeFile({ fileName: "E:/CAP/Documentation/improved_slides.pptx" }).then(() => {
  console.log("Improved slides generated at E:/CAP/Documentation/improved_slides.pptx");
});
