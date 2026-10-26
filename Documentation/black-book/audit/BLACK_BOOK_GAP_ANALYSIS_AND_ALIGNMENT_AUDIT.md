# RestockIQ: Final Year Capstone Project Black Book Gap Analysis & Alignment Audit

**Project Title:** RestockIQ: Demand Forecasting and Perishable Inventory Optimization for Food Retailers  
*(Formerly documented under early working title: LocalDemand)*  
**Institution:** SVKM's NMIMS, Mukesh Patel School of Technology Management & Engineering (MPSTME), Shirpur Campus  
**Department:** Information Technology Department  
**Program:** Bachelor of Technology in Information Technology (Academic Session 2026–27)  
**Students:**  
- Yatin Patil (Roll No: A201, SAP ID: 70012300043)  
- Chinmay Patil (Roll No: A223, SAP ID: 70012300123)  
- Soumy Raghuvanshi (Roll No: A221, SAP ID: 70012300116)  
**Faculty Mentor & HOD:** Dr. Srikanth Pulipeti  
**Associate Dean:** Dr. Venkatadri Marriboyina  

---

## 1. Executive Summary & Audit Purpose

This comprehensive audit evaluates the current working draft of the Capstone Project Report (**"Black Book"**, saved as `Documentation/reference/Self edited Black book our project.doc` / `docx`) against three reference baselines:
1. **The Mentor Template:** `Template-Project Report (Black Book) - IT.doc` (Official MPSTME Department of Information Technology Capstone Report Guidelines).
2. **The Approved Classmate Benchmark:** `Final_Report_Bordered classmate black book refernce.docx` (High-scoring capstone thesis exhibiting approved styling, page borders, certificates of approval, declaration, comprehensive testing chapters, and IEEE referencing).
3. **The Actual Current Codebase & Verified Empirical Results:** The fully built, tested, and validated RestockIQ system across `ML/`, `Backend/`, `APP/`, and `docs/`.

### Summary of Status & Diagnosis:
* **Current Draft Word Count:** 9,672 words (435 text blocks, 7 preliminary tables).
* **Target Word Count for Production Black Book:** 16,000 – 22,000 words (matching institutional standards for B.Tech Capstone theses).
* **Primary Structural Diagnosis:** The current draft was authored at an early proposal/conceptual stage. Consequently, it employs hypothetical language (*"if implemented"*, *"intended to"*, *"where suitable data is available"*), references a preliminary system name (*LocalDemand*), assumes an unverified model library (*XGBoost*), and contains **zero empirical numbers, zero backtest tables, and zero simulation charts** in Chapter 4.
* **Ground Truth Advantage:** The project has since achieved **state-of-the-art empirical validation**: 38 weekly rolling-origin temporal folds, verified 25.48% GBDT accuracy (+2.47 pp over Prophet baseline), 24.92% GBDT+Calendar accuracy, a rigorous 200-shift weather placebo test proving why weather features should be rejected, a Newsvendor Critical Ratio inventory policy generating €42,752.48 profit at 11.8% waste, an active FastAPI/MongoDB Atlas backend, and a 44/44 test-verified Flutter mobile application.

Integrating these real outputs elevates the Black Book from a generic descriptive student report into an exceptional, publication-grade engineering capstone thesis.

---

## 2. Side-by-Side Structural Comparison

The table below contrasts the structure across all four artifacts:

| Section / Chapter | Mentor Template (`Template-IT.doc`) | Classmate Reference (`Final_Report_Bordered.docx`) | Current Draft (`Self edited Black book.docx`) | Proposed Final RestockIQ Black Book |
|---|---|---|---|---|
| **Outer Cover Page** | Standard University Title (24pt), Details (14/12pt) | Bordered, University Logo, Session 2026–27 | Unbordered, Preliminary Title | **Bordered, University Logo, Session 2026–27, Canonical Title** |
| **Certificate** | Signed by Mentor, HOD, Examiner | Signed by Guide, HOD, Associate Dean | Present, lacks examiner line formatting | **Full Academic Certificate with Guide, HOD, External Examiner** |
| **Certificate of Approval** | Optional / In Exam Form | Explicit Certificate of Approval for Oral Exam | **Missing** | **Include Certificate of Approval (External & Internal)** |
| **Declaration** | Mandatory | Mandatory (Signed by all candidates) | **Missing** | **Include Candidate Declaration with SAP IDs & Signatures** |
| **Acknowledgement** | Mentor, HOD, Dean, Faculty | Detailed gratitude, all members | Present (Dr. Pulipeti, Dr. Marriboyina) | **Retain & Refine Acknowledgements** |
| **Abstract** | ~1 page defining problem & work | Detailed 1-page overview with key metrics | 3 paragraphs, conceptual | **Refined 1-page Abstract with empirical metrics (25.48% WAPE, €42.7k profit)** |
| **Preliminary Lists** | TOC, Figures (Roman), Tables (Roman), Abbreviations | Detailed TOC, Figures, Tables, Abbreviations | Basic Tables 0, 1, 2 | **Full Roman-numbered TOC, List of Figures, List of Tables, Abbreviations** |
| **Chapter 1: Introduction** | 1.1 Background, 1.2 Motivation/Scope, 1.3 Problem, 1.4 Contributions, 1.5 Organization | 1. Background, 2. Motivation, 3. Objectives, 4. Scope, 5. Overview, 6. Tech Stack, 7. Organization | 1.1–1.5 Present (Conceptual focus) | **Retain 1.1–1.5; update branding to RestockIQ; align tech stack & contributions** |
| **Chapter 2: Literature Survey** | 2.1 Intro, 2.2 Exhaustive survey (>=10 papers) | 8 Subsections, Comparison Table, Research Gaps | 2.1 Intro, 2.2 Survey (10 papers), Gaps Table | **Expand Chapter 2 with unified Literature Review & Paper Matrix** |
| **Chapter 3: Methodology / Design** | 3.1 Block Diagram, 3.2 Hardware, 3.3 Software, Flowchart / Algorithm | Ch 3 Problem Def & Solution + Ch 4 Design (Architecture, Pipeline, Data Model, API, Security) | 3.1–3.3 Present (References XGBoost, lacks Atlas/FastAPI details) | **Comprehensive Chapter 3: Architecture, MongoDB Atlas Schema, FastAPI REST API, GBDT & Prophet Formulation, Newsvendor CR Derivation** |
| **Chapter 4: Results & Analysis** | Results of actual testing & analysis | Ch 5 Result Analysis: Snapshots (Benchmark data, cross-validation, ablation, UI) | Purely descriptive text; placeholder images; **NO real numbers** | **Empirical Chapter 4: 38-fold temporal backtest, 6 summer folds, Cluster Bootstrap CIs, Sign Tests, Weather Placebo Test, Waste & Profit Curves, App Screenshots** |
| **Chapter 5: Advantages / Limitations / Testing** | 5.1 Advantages, 5.2 Limitations, 5.3 Applications | Ch 6 Testing (Unit, Integration, Security, Protocol Guards, Defects) | 5.1 Advantages, 5.2 Limitations, 5.3 Applications (General statements) | **Chapter 5: Advantages, Limitations, Applications + Software Testing & System Integrity (44 Flutter tests, backend tests, bug post-mortems)** |
| **Chapter 6: Conclusion & Future Scope** | 6.1 Conclusion, 6.2 Future Scope | 7.1 Conclusion, 7.2 Limitations, 7.3 Future Work | 6.1 Conclusion, 6.2 Future Scope | **Chapter 6: Conclusion (Empirical takeaways, production readiness) & Future Work** |
| **References** | Numbered, IEEE format | 50+ IEEE citations | 22 Citations (mixed format) | **Standardized IEEE Citations (matched to text citations)** |
| **Appendix A: Sample Code** | Required | Production code snippets | 2 generic sample scripts | **Verified RestockIQ Code: GBDT Feature Pipeline, Prophet Regressors, Newsvendor Policy, FastAPI Endpoint** |
| **Appendix B: Data Sheets** | Required | Data schemas & specifications | Basic development specs | **Dataset Schema (Guérande Bakery 637-day dataset), Open-Meteo Weather API specs** |
| **Appendix C: List of Components** | Required | Hardware & software bill of materials | Hardware & software tables | **Comprehensive Hardware, Cloud (Atlas, Render), Mobile, and Software Dependencies** |
| **Appendix D: Papers Published / Presented** | Required | Paper details & submissions | Mentions ICIMMI 2026 & ICANET 2027 | **Conference Paper Details, IEEE format manuscript abstract, submission status** |

---

## 3. Parameter-by-Parameter Discrepancy & Deviation Matrix

This matrix details every critical parameter where the current draft diverges from the real project state:

| Parameter / Dimension | Current Draft Statement | Actual Verified Reality (`e:\CAP`) | Deviation Category | Required Fix in Black Book |
|---|---|---|---|---|
| **System Branding** | Named **"LocalDemand"** throughout (42 occurrences) | Repository, App, APK, and Presentations are named **"RestockIQ"** | **Nomenclature Misalignment** | Systematically update name to **RestockIQ**; note that early conceptualization was titled LocalDemand. |
| **GBDT Algorithm Class** | Specifies **"XGBoost"** (30 occurrences) | Implemented using **`sklearn.ensemble.HistGradientBoostingRegressor`** | **Algorithm Misalignment** | Correct all references to **Histogram-based Gradient Boosted Decision Trees (HistGradientBoostingRegressor)**; explain why native Scikit-Learn histogram binning was chosen (deterministic binning, zero external C++ dependencies, rapid inference). |
| **Primary Model Architecture** | Assumes 2-stage Prophet + XGBoost residual hybrid is the best model | Empirical backtest proves pure day-ahead GBDT (**Control 3, 25.48%**) beats Prophet (27.95%) and Canonical Hybrid (28.26%) | **Architectural Finding** | Document the complete hierarchy: Prophet Baseline &rarr; Canonical Hybrid (22.37% summer) &rarr; Pure Day-Ahead GBDT (25.48% across 38 folds) &rarr; GBDT + Calendar (24.92%). |
| **Weather Feature Integration** | States weather is actively incorporated to improve forecasts | Weather was tested and **REJECTED** after 200-shift placebo test ($p = 0.3800$, adds no value over GBDT lags) | **Scientific Finding (Negative Result)** | Present the end-to-end weather pipeline (Open-Meteo archive & forecast APIs) and document the **Weather Placebo Experiment** as a high-value empirical rejection. |
| **Evaluation Suite Scope** | Mentioned vaguely as "testing on historical data" | Rigorous **38 weekly rolling-origin folds** (Jan 2022 – Sep 2022) + **6 summer high-demand folds** | **Missing Empirical Data** | Insert full benchmark tables with Pooled WAPE, Fold-Mean WAPE, Fold Wins, and 95% Cluster Bootstrap CIs. |
| **Statistical Rigor** | No statistical tests or confidence intervals mentioned | **Paired whole-week cluster bootstrap** (38 blocks, 2000 draws) + **Exact two-sided binomial sign-tests** | **Missing Statistical Proof** | Include sign-test $p$-values (e.g., Control 3 vs Prophet: $p = 0.0138$; Control i vs Prophet: $p < 0.0001$). |
| **Inventory Optimization Model** | Simple heuristic: $\text{Restock} = \max(0, \text{Demand} + \text{Safety} - \text{Stock})$ | **Newsvendor Critical Ratio Policy**: $CR = \frac{C_u}{C_u + C_o} = 0.60 \implies z = +0.2533$ (COGS 40%) | **Theoretical Under-specification** | Provide formal mathematical derivation of Newsvendor Critical Ratio under asymmetric stockout vs spoilage costs. |
| **Inventory Simulation Scope** | Speculative statements on waste reduction | Evaluated on **68,883 units** over 88 trading days; proves CR policy achieves **€42,752.48 profit** at **11.8% waste** | **Missing Simulation Results** | Insert the Profit vs Service Level Frontier curve showing why 95% service level destroys bakery profitability (€35.7k profit, 27.5% waste). |
| **Out-of-Sample Bias Handling** | Not addressed | OOS bias adjustment calibrated on trailing 28 days of training data | **Missing Methodological Detail** | Detail the 28-day sliding window bias correction mechanism in Chapter 3 and Chapter 4. |
| **Bakery Calendar Truth** | Draft assumes bakery closed on Wednesdays throughout | Analyzed 637 calendar days: bakery operated **7 days a week (zero closures) in June, July, August**; Wednesday closures only in off-season | **Domain Misalignment** | Explain the seasonal calendar dynamics and the mid-August peak to September demand collapse (-50% drop). |
| **Backend & Cloud Architecture** | Generic Python mentioned; no database specified | **FastAPI** REST backend (`Backend/main.py`), **MongoDB Atlas** cloud database, JWT Bearer auth, Pydantic v2 schemas | **Missing Architecture Details** | Document complete backend architecture: collections (`users`, `items`, `forecasts`, `intraday_sales`), endpoints, and Render deployment. |
| **Mobile Application Architecture** | Flutter mentioned in general terms | **Flutter 3.38+**, Provider state management, 8 distinct operational screens, offline fallback, master 5-item catalog | **Under-specified UI/UX** | Document the Flutter application architecture, provider state lifecycle, and include real high-resolution screenshots. |
| **Testing & Quality Assurance** | No testing section in draft | Dedicated **44/44 Flutter tests passed** (21 unit, 23 widget/integration), backend unit tests, and pipeline integrity audit | **Missing Testing Chapter** | Dedicate Section 5.4 or Chapter 6 to Software Testing, defect post-mortems (login timeout, AI assistant fallback, ghost items), and test execution tables. |

---

## 4. Chapter-by-Chapter Action Plan for the Final Black Book

### Front Matter
- [x] Apply standard NMIMS border layout (matching `Final_Report_Bordered classmate black book refernce.docx`).
- [x] Add **Certificate of Approval** (for Oral Defense Examiners).
- [x] Add **Declaration** signed by Yatin Patil, Chinmay Patil, and Soumy Raghuvanshi.
- [x] Update **Certificate** with institutional signature blocks (Guide: Dr. Srikanth Pulipeti, HOD, External Examiner).
- [x] Refine **Acknowledgement** to acknowledge Dr. Srikanth Pulipeti, Dr. Venkatadri Marriboyina, and faculty.
- [x] Overhaul **Abstract** to include concrete empirical highlights (25.48% WAPE, €42.7k profit, 44/44 tests).
- [x] Rebuild Roman-numbered **Table of Contents**, **List of Figures**, **List of Tables**, and **Abbreviations**.

### Chapter 1: Introduction
- [x] Update project name to **RestockIQ**.
- [x] Clarify the **Forecast-to-Action Gap** in small food retail (perishable items with 1-day shelf life).
- [x] Specify the three core pillars: (1) Machine Learning Demand Forecasting, (2) Newsvendor Inventory Decision Optimization, (3) Cloud-Connected Mobile Retail Application.
- [x] Align salient contributions with the real system capabilities.

### Chapter 2: Literature Survey
- [x] Consolidate the 10+ core literature papers on time-series forecasting (ARIMA, Prophet, DeepAR, GBDTs, hybrid models) and perishable retail inventory (Newsvendor, multi-echelon, shelf-life constraints).
- [x] Maintain the comprehensive Comparative Analysis and Research Gaps table.
- [x] Highlight the gap: Existing solutions either provide complex time-series tools without inventory decisions, or generic inventory software without localized demand prediction.

### Chapter 3: Methodology and Implementation
- [x] **Block Diagram & End-to-End Pipeline:** Show data flow from raw POS sales & weather &rarr; Preprocessing & Feature Engineering &rarr; Prophet Decomposition & GBDT Modeling &rarr; Out-of-Sample Bias Correction &rarr; Newsvendor Reorder Engine &rarr; FastAPI Backend & MongoDB Atlas &rarr; Flutter Mobile Client.
- [x] **Hardware & Development Environment:** Actual developer specs (AMD Ryzen / Intel Core i7, 16GB RAM, Android physical testbed).
- [x] **Software Architecture:**
  - ML Pipeline: Python 3.10, Prophet 1.3, Scikit-Learn 1.7 (`HistGradientBoostingRegressor`).
  - Backend: FastAPI, Pydantic, Motor/PyMongo, MongoDB Atlas, Render.
  - Mobile App: Flutter 3.38, Dart 3, Provider, Material Design 3.
- [x] **Mathematical Formulations:**
  - Prophet Generalized Additive Model: $y(t) = g(t) + s(t) + h(t) + \sum \beta_j X_j(t) + \epsilon_t$.
  - GBDT Autoregressive Formulation: $y_t = f(y_{t-1}, \bar{y}_{t-7}, y_{t-7}^{cal}, \text{dow}, \text{month}, \text{tourist}, \text{item})$.
  - Canonical Hybrid Residual Formulation: $\hat{y}_t = \hat{y}_{t}^{prophet} + \hat{r}_t^{gbdt}$.
  - Newsvendor Critical Ratio Derivation: $\min \mathbb{E}[C_o \max(0, Q - D) + C_u \max(0, D - Q)] \implies Q^* = \hat{D} + z \cdot \hat{\sigma}$, where $z = \Phi^{-1}\left(\frac{C_u}{C_u + C_o}\right)$.
- [x] **Database Schema:** Document MongoDB Atlas collections (`users`, `items`, `forecasts`, `intraday_sales`) with field descriptions.
- [x] **REST API Specifications:** Table of `/api/v1/` endpoints (Auth, Items, Forecasts, Intraday, Assistant).

### Chapter 4: Result and Analysis (The Core Empirical Chapter)
- [x] **Benchmark Dataset Description:** 637 calendar days (Jan 1, 2021 to Sep 30, 2022), 600 trading days, 35 artisan bakery SKUs from Guérande, France.
- [x] **Experimental Protocol:** 38 rolling weekly origins, 7-day forecast horizon, no lookahead leakage.
- [x] **Forecasting Accuracy Results Table:**
  - Prophet-only Baseline: 27.95% pooled WAPE.
  - Control 3 (GBDT lag_1, no Prophet): 25.48% pooled WAPE (+2.47 pp gain, 27/38 wins, $p = 0.0138$).
  - Model A (1-day-ahead Hybrid): 26.07% pooled WAPE (+1.88 pp gain, 28/38 wins).
  - Model (iv) (GBDT + Calendar): 24.92% pooled WAPE (+3.03 pp gain, 29/38 wins).
  - Control (i) (Linear residual correction): 33.04% pooled WAPE (severely degraded, rejected).
  - 6 Summer Peak Folds: Prophet 21.74%, Canonical Hybrid 22.37%.
- [x] **Statistical Hypothesis Testing & Cluster Bootstrap:**
  - Paired 38-block cluster bootstrap confidence intervals.
  - Exact binomial sign-test $p$-values.
- [x] **Weather Pipeline Verification & Placebo Experiment:**
  - Open-Meteo archive and forecast APIs (HTTP 200, no API key).
  - 200 random circular shift placebo distribution ($p = 0.3800$).
  - Definitive scientific justification for rejecting weather features in production.
- [x] **Inventory Spoilage & Profit Simulation Results:**
  - 68,883 units replayed across 88 trading days.
  - Operational frontier table across policies ($z \in \{0.0, 0.2533, 0.5, 0.84, 1.0, 1.28, 1.65\}$).
  - Demonstration that the Critical Ratio policy ($z = +0.2533$) maximizes gross profit at **€42,752.48** with **11.8% waste**.
- [x] **Application Interface & Walkthrough Snapshots:**
  - Login screen, Dashboard screen, Item Detail Forecast screen, Inventory Check-In screen, Waste Alerts screen, and AI Assistant screen.

### Chapter 5: Advantages, Limitations, Applications & System Integrity
- [x] **Advantages:** Real economic value quantified (+€2,351 profit gain, 8 pp waste reduction vs baselines).
- [x] **Limitations:** Cold-start items require category fallback; models assume daily sales data availability; weather does not yield reliable signal for daily bakery items.
- [x] **Applications:** Bakeries, patisseries, artisan cafes, ready-to-eat delis, daily fresh food producers.
- [x] **Software Testing & Integrity Verification:**
  - 44/44 Flutter tests passed (Unit & Integration).
  - Backend pytest suites (tenant isolation, JWT auth, CRUD).
  - Defect post-mortems and resolutions (login timeout fix, resilient assistant engine, catalog synchronization).

### Chapter 6: Conclusion and Future Scope
- [x] **Conclusion:** Summarize major achievements: overcoming the forecast-to-action gap, proving non-linear GBDT superiority over static statistical baselines, establishing the Newsvendor profit peak, and delivering a cross-platform mobile decision tool.
- [x] **Future Scope:** Automated midnight sales rollup daemons, multi-store franchise support, dynamic pricing discount actuators, and real-time POS barcode integration.

### Appendices & References
- [x] **References:** 30+ standardized IEEE citations.
- [x] **Appendix A (Sample Code):** HistGradientBoosting feature extractor, Prophet additive regressor model, Newsvendor reorder calculator, FastAPI endpoint implementation.
- [x] **Appendix B (Data Sheets):** French Bakery POS dataset schema, Open-Meteo API parameter reference.
- [x] **Appendix C (List of Components):** Hardware, software libraries, cloud services.
- [x] **Appendix D (List of Papers):** Research manuscript submission details (Target: ICIMMI 2026 / ICANET 2027).

---

## 5. Log Book Alignment & Overview

In accordance with `Refernce log book classmate.docx`, a comprehensive **15-Week Capstone Project Log Book** has been compiled in `Documentation/black-book/log-book/CAPSTONE_PROJECT_LOG_BOOK.md`.

It tracks the project chronologically across 15 development weeks:
* **Weeks 1–3:** Problem identification, domain study of perishable food retail, mentor meetings, literature survey, and aim/objectives formulation.
* **Weeks 4–6:** Dataset acquisition (French bakery POS), exploratory data analysis, seasonal closure audit, and data preprocessing pipelines.
* **Weeks 7–9:** Baseline modeling (Prophet), GBDT feature engineering, residual learning experiments, and Open-Meteo weather integration.
* **Weeks 10–11:** 38-fold weekly rolling-origin backtesting, paired cluster bootstrap, sign-testing, and the 200-shift weather placebo experiment.
* **Weeks 12–13:** Day-ahead Newsvendor inventory simulation, profit vs service level curves, FastAPI backend development, and MongoDB Atlas integration.
* **Weeks 14–15:** Flutter mobile application development, UI integration, end-to-end 44-test verification, defect fixes, Black Book compilation, and final mentor review.
