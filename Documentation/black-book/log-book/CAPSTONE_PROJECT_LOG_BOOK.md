# Appendix A.7: Log Book for Capstone Project

**Mukesh Patel School of Technology Management & Engineering (MPSTME)**  
**SVKM's NMIMS (Deemed-to-be University), Shirpur Campus**  

* **Department:** Information Technology  
* **Program:** Bachelor of Technology  
* **Semester:** VII  
* **Project Title:** RestockIQ: Demand Forecasting and Perishable Inventory Optimization for Food Retailers  
* **Name of Faculty Mentor:** Dr. Srikanth Pulipeti (Associate Professor & Head of Department)  

---

## 1. Student Details

| Std No. | Roll No | Name | Contact (per. email) |
| :---: | :---: | :--- | :--- |
| **Student 1** | **A201** | **Yatin Patil** | yatin.patil043@nmims.in |
| **Student 2** | **A223** | **Chinmay Patil** | chinmay.patil123@nmims.in |
| **Student 3** | **A221** | **Soumy Raghuvanshi** | soumy.raghuvanshi116@nmims.in |

---

## 2. Group Members (Evaluation & Grades)

| Roll No. | Name | Sign (Students) | Grades (By Faculty Mentor) |
| :---: | :--- | :---: | :---: |
| **A201** | Yatin Patil | `_______________` | |
| **A223** | Chinmay Patil | `_______________` | |
| **A221** | Soumy Raghuvanshi | `_______________` | |

---

## 3. Project Log Entries (15 Weeks)

**Project Title:** RestockIQ: Demand Forecasting and Perishable Inventory Optimization for Food Retailers  

| Week No. | Duration | Work Carried Out (Aligned with Review 1 & 2 Gantt Charts) | Remarks by Faculty Mentor | Sign | Git Traceability Commits |
|:---:|---|---|---|:---:|---|
| **1** | 13 Jul 2026<br>to<br>19 Jul 2026 | Formed the project group under faculty mentor Dr. Srikanth Pulipeti. Initiated Literature Review & Requirement Finalization. Investigated operational challenges of daily food wastage and stockouts in artisan bakeries. Defined project aim, primary research questions, and structured the LaTeX review paper template. | | | `65dbe8d1`, `26474a42`, `31e13ff2`, `7085887f`, `35df1e82`, `528d501c`, `ede72fa3`, `9c15a54a` |
| **2** | 20 Jul 2026<br>to<br>26 Jul 2026 | Conducted extensive literature survey covering 25+ papers on statistical time series (ARIMA, SARIMA, Prophet) and stochastic inventory theory (Newsvendor). Commenced Dataset Collection & Verification: sourced candidate POS transaction logs. Prepared the Interim Development Plan (IDP). | | | *(Literature Survey & IDP Phase)* |
| **3** | 27 Jul 2026<br>to<br>02 Aug 2026 | Acquired and ingested French artisan bakery POS dataset (2021–2022). Audited data quality, cleaned transaction logs, and mapped store closure days (Mondays and Wednesdays). Analyzed day-of-week sales variation and synthesized domain findings for requirements. | | | `715d16d3`, `9ca8a51d`, `23a83158`, `1f589757`, `16ca4d8b`, `a739c81d`, `2096def4` |
| **4** | 03 Aug 2026<br>to<br>09 Aug 2026 | Completed Literature Review & Requirement Finalization (100% completed). Finalized functional (FR1–FR7) and non-functional requirements. Prepared Review-I presentation deck. Presented Review-I to the faculty panel (**Milestone: Review 1 Cleared at Week 4**). | | | `6ff83375`, `43186858`, `7ca6020a`, `b884a34d`, `b3ceedad`, `956827cf`, `636c8ebb`, `647351b5`, `c9e626e7`, `d8bca670` |
| **5** | 10 Aug 2026<br>to<br>16 Aug 2026 | Completed Dataset Collection & Verification (100% completed). Commenced Flutter App Development Setup: configured Flutter cross-platform repository, Material 3 design tokens, theme palette, and screen navigation architecture for store managers. | | | `6915cf14`, `19d1b8f3`, `1b099922`, `77922a4a`, `330242ef`, `34c8100b`, `fef6ccea`, `5315d5d6`, `7c558aa1` |
| **6** | 17 Aug 2026<br>to<br>23 Aug 2026 | Flutter App Development: built core mobile screens (dashboard overview, inventory cards, item list). Implemented baseline forecasting models (7-day rolling average, 4-week same-weekday average, seasonal naive) establishing benchmark lower bounds (WAPE 30.39%). | | | `21905257` |
| **7** | 24 Aug 2026<br>to<br>30 Aug 2026 | Flutter App Development: built item detail view and manual stock check-in screens. Commenced Model Training (Prophet + XGBoost): implemented baseline Facebook Prophet model capturing weekly and yearly additive seasonality. Explored Google Gemini LLM for operational briefings. | | | `a62cdb82`, `7f4f0b71`, `0cd0392f` |
| **8** | 31 Aug 2026<br>to<br>06 Sep 2026 | Advanced Flutter App Development to ~90% (waste alert UI, settings view). Explored GBDT regressors on Prophet residuals; observed extreme sparsity on low-volume individual SKU series. Prepared Review-II slide deck (`G1-PPT-Review-II.pptx`) with re-baselined Gantt chart. | | | `5769595d`, `36a5d376`, `fff4876a` |
| **9** | 07 Sep 2026<br>to<br>13 Sep 2026 | Presented academic Review-II to the departmental faculty review panel: demonstrated Flutter mobile application (95% complete) and initial forecasting baseline (30% model training progress). Received panel approval to proceed with backend API and cloud database integration (**Milestone: Review 2 Cleared at Week 9**). | | | `7a6e4172`, `a5c8c2ea`, `8fb01551`, `976f6ae9` |
| **10** | 14 Sep 2026<br>to<br>20 Sep 2026 | Completed Model Training (remaining 70%): overcame SKU sparsity by transitioning from individual tree models to a pooled gradient-boosted decision tree (LightGBM) trained across all items with lag and calendar features. Implemented adaptive fallback for sparse items. | | | `d4eba6ef`, `d0348323`, `9828e258`, `63de13b7`, `6d8d843e`, `995ea144`, `6db91e48`, `3ef83ff1` |
| **11** | 21 Sep 2026<br>to<br>27 Sep 2026 | Locked the production hybrid ML architecture. Completed remaining 5% of Flutter App Development (100% complete): finalized dynamic state management, real-time forecast binding, and waste alert cards. Integrated teammate pull requests and froze frontend interfaces. | | | `707028b6`, `f7290941`, `2d358b59`, `27ea55fe`, `3d0a344f`, `e54846ef`, `fd1b4e08`, `f4ed55ee`, `905aa69f` |
| **12** | 28 Sep 2026<br>to<br>04 Oct 2026 | Provisioned and configured MongoDB Atlas cloud database cluster (`restockiq`). Designed collections for users, items, and batch forecasts. Conducted repository security audit, sanitized exposed credentials, and hardened `.gitignore` against secret leaks. | | | `f3853a93`, `12abb445`, `a3f91c48`, `9fe8ed83`, `84575b6f` |
| **13** | 05 Oct 2026<br>to<br>11 Oct 2026 | Implemented Backend API, Restock Logic & LLM Narrator: built FastAPI REST service with JWT auth, waste mitigation discount tiers (HIGH 20%, MEDIUM 10%), and Google Gemini API (`gemini-3-flash-preview`) with zero-math prompt grounding. Completed System Integration (`verify_e2e.py`). | | | `aca34365`, `022624a6`, `c8fea8e1`, `82eb1725`, `a6421074`, `85af1c75`, `07fa1350`, `af3ac8ad`, `75a76a8e`, `6446aee8` |
| **14** | 12 Oct 2026<br>to<br>18 Oct 2026 | Containerized FastAPI backend using Docker and deployed live to Render cloud hosting. Configured GitHub Actions CI/CD workflows, automated keepalive health pings, nightly batch forecasting scheduler, and reverse-proxy rate limiting. | | | `33f7f2d3`, `b93e5b4b`, `b0262ff6`, `d3dc5fca`, `b0662a25`, `6b294a5e`, `e747e6d7`, `46584eb5`, `ce316b4d`, `f05aa7af`, `af92146c`, `d9549061`, `47bca314` |
| **15** | 19 Oct 2026<br>to<br>26 Oct 2026 | Testing & Evaluation: executed 38-fold weekly backtesting (Model A 26.06% pooled WAPE, Canonical Hybrid 22.51% summer folds), 200-iteration circular weather placebo test (weather rejected), and 68,883-unit Newsvendor simulation. Passed 55/55 test suite across all 5 tiers. Compiled Black Book and tagged `v1.0-submission`. | | | `931ac2ab`, `510e0be4`, `7e20414c`, `dd1b8211`, `15b98b22`, `49caa0ef`, `c4b47245`, `e6782c9e`, `f634c186`, `76c31115`, `6d91bbcc`, `685d02fc` |

---

## 4. Verification & Faculty Mentor Sign-Off

| Date & Location | Faculty Mentor Authorization |
| :--- | :--- |
| **Date:** `____________________`<br>**Place:** Shirpur | `________________________________________`<br>**Dr. Srikanth Pulipeti**<br>Faculty Mentor<br>Department of Information Technology, MPSTME, Shirpur |

---
*Generated Microsoft Word Document:* [`CAPSTONE_PROJECT_LOG_BOOK.docx`](file:///e:/CAP/Documentation/black-book/log-book/CAPSTONE_PROJECT_LOG_BOOK.docx)  
*Printable PDF Document:* [`CAPSTONE_PROJECT_LOG_BOOK.pdf`](file:///e:/CAP/Documentation/black-book/log-book/CAPSTONE_PROJECT_LOG_BOOK.pdf)
