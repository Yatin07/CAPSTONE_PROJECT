# Capstone Project Log Book (Semester VII & VIII)

**Mukesh Patel School of Technology Management & Engineering (MPSTME)**  
**SVKM's NMIMS (Deemed-to-be University), Shirpur Campus**  
**Department:** Information Technology  
**Program:** Bachelor of Technology in Information Technology  
**Academic Session:** 2026–2027  

---

## 1. Project Identification

* **Project Title:** RestockIQ: Demand Forecasting and Perishable Inventory Optimization for Food Retailers  
* **Faculty Mentor:** Dr. Srikanth Pulipeti (Head of Department & Associate Professor, IT Department)  
* **Associate Dean:** Dr. Venkatadri Marriboyina  

---

## 2. Student Details

| Std No. | Roll No. | SAP ID | Student Name | Institutional Email |
| :---: | :---: | :---: | :--- | :--- |
| **Student 1** | **A201** | 70012300043 | **Yatin Patil** | yatin.patil043@nmims.in |
| **Student 2** | **A223** | 70012300123 | **Chinmay Patil** | chinmay.patil123@nmims.in |
| **Student 3** | **A221** | 70012300116 | **Soumy Raghuvanshi** | soumy.raghuvanshi116@nmims.in |

---

## 3. Evaluation & Signature Sheet

| Roll No. | Student Name | Student Signature | Remarks / Grades (By Faculty Mentor) |
| :---: | :--- | :---: | :---: |
| **A201** | Yatin Patil | `_______________` | |
| **A223** | Chinmay Patil | `_______________` | |
| **A221** | Soumy Raghuvanshi | `_______________` | |

---

## 4. Weekly Project Log Entries (15 Weeks - Mapped to Real Git Commits)

| Week No. | Duration | Real Git Commits | Work Carried Out (Grouped by Theme) | Remarks by Faculty Mentor | Sign |
|:---:|---|---|---|---|:---:|
| **Week 1** | **12 Jul 2026 to 18 Jul 2026** | `65dbe8d1`, `26474a42`, `31e13ff2`, `7085887f`, `35df1e82`, `528d501c`, `ede72fa3`, `9c15a54a` | **Project Inception & Review Paper:** Formed project group. Held initial meeting with faculty mentor Dr. Srikanth Pulipeti. Explored food wastage and stockouts in artisan bakeries. Created LaTeX research paper template (`.tex`) and formulated the problem statement and review presentation. | Problem domain and review paper topic approved. Focus on short-shelf-life retail. | `______` |
| **Week 2** | **19 Jul 2026 to 25 Jul 2026** | *(No commits — Literature Review Phase)* | **Deep Literature Survey:** Read and synthesized 25+ academic papers covering statistical time series (ARIMA, Prophet), gradient boosting (GBDT), and inventory theory (Newsvendor). Documented research gaps in existing demand planning software. | Exhaustive survey completed. Ensure clear differentiation from generic ERPs. | `______` |
| **Week 3** | **26 Jul 2026 to 01 Aug 2026** | `715d16d3`, `9ca8a51d`, `23a83158`, `1f589757`, `16ca4d8b`, `a739c81d`, `2096def4` | **Data Acquisition & Baseline Setup:** Set up development virtual environment. Acquired Rossmann and French artisan bakery POS datasets. Conducted initial data quality checks and built first experimental Prophet baseline model. | Real retail data acquired. Verify chronological ordering of training series. | `______` |
| **Week 4** | **02 Aug 2026 to 08 Aug 2026** | `6ff83375`, `43186858`, `7ca6020a`, `b884a34d`, `b3ceedad`, `956827cf`, `636c8ebb`, `647351b5`, `c9e626e7`, `d8bca670` | **Problem Statement Refinement & App Scaffolding:** Initialized Flutter mobile application repository. Refined the core scope: retail decision support connecting forecasts to inventory restocking. Introduced LLM narrative layer concept for non-technical store managers. | Conceptual evolution approved. Keep mobile interface minimal and intuitive. | `______` |
| **Week 5** | **09 Aug 2026 to 15 Aug 2026** | `6915cf14`, `19d1b8f3`, `1b099922`, `77922a4a`, `330242ef`, `34c8100b`, `fef6ccea`, `5315d5d6`, `7c558aa1` | **Unsold Stock Mitigation & Architecture Planning:** Formulated waste mitigation strategy for perishable stock approaching closing hours. Cleaned project directories and structured the modular engineering roadmap between ML and mobile app frontend. | Practical waste handling component is a strong capstone contribution. | `______` |
| **Week 6** | **16 Aug 2026 to 22 Aug 2026** | `21905257` | **Model Training & Feature Exploration:** Evaluated preliminary time-series regressors on historical bakery transactions. Formatted daily aggregations and audited calendar dates. | Continue iterative validation. Avoid future lookahead in training splits. | `______` |
| **Week 7** | **23 Aug 2026 to 29 Aug 2026** | `a62cdb82`, `7f4f0b71`, `0cd0392f` | **AI Integration Setup & Baseline Refinement:** Explored Google Gemini API for operational store briefing. Continued tuning baseline Prophet parameters (yearly and weekly additive seasonality). | Ensure LLM is strictly grounded and performs zero hallucinated math. | `______` |
| **Week 8** | **30 Aug 2026 to 05 Sep 2026** | `5769595d`, `36a5d376`, `fff4876a` | **Repository Maintenance & Documentation:** Maintained code formatting, updated technical markdown documents, and refined project requirements. | Good engineering hygiene. Prepare for Review-II presentation. | `______` |
| **Week 9** | **06 Sep 2026 to 12 Sep 2026** | `7a6e4172`, `a5c8c2ea`, `8fb01551`, `976f6ae9` | **Academic Review-II Presentation:** Finalized Review-II slide deck (`G1-PPT-Review-II.pptx`). Presented methodology, system architecture, and initial forecasting experiments to the departmental review panel. | Review-II presented successfully. Proceed with full backend and cloud DB. | `______` |
| **Week 10** | **13 Sep 2026 to 19 Sep 2026** | `d4eba6ef`, `d0348323`, `9828e258`, `63de13b7`, `6d8d843e`, `995ea144`, `6db91e48`, `3ef83ff1` | **Prophet & Tree Residual Experiments:** Built multi-part Prophet pipeline. Experimented with gradient boosted decision trees on residuals; identified data sparsity challenges on individual low-volume SKUs. | Tree overfitting on sparse residuals observed. Focus on pooled modeling. | `______` |
| **Week 11** | **20 Sep 2026 to 26 Sep 2026** | `707028b6`, `f7290941`, `2d358b59`, `27ea55fe`, `3d0a344f`, `e54846ef`, `fd1b4e08`, `f4ed55ee`, `905aa69f` | **Architecture Lockdown & UI Redesign:** Locked the production hybrid architecture. Re-architected Flutter UI with Material 3 design tokens. Completed core machine learning training scripts and merged teammate pull requests. | Architecture finalized. Proceed with database integration and API layer. | `______` |
| **Week 12** | **27 Sep 2026 to 03 Oct 2026** | `f3853a93`, `12abb445`, `a3f91c48`, `9fe8ed83`, `84575b6f` | **Cloud Database & Security Hardening:** Created MongoDB Atlas cloud cluster (`restockiq`). Implemented connection logic and removed exposed credentials from Git history. Prepared FastAPI application skeleton. | Cloud persistence established. Ensure strict multi-tenant access controls. | `______` |
| **Week 13** | **04 Oct 2026 to 10 Oct 2026** | `aca34365`, `022624a6`, `c8fea8e1`, `82eb1725`, `a6421074`, `85af1c75`, `07fa1350`, `af3ac8ad`, `75a76a8e`, `6446aee8` | **6-Step Backend Implementation & App Binding:** Implemented full FastAPI REST service (`main.py`): JWT auth, items CRUD, batch forecasting read layer, waste action engine, and end-to-end audit (`verify_e2e.py`). Integrated Flutter mobile app to live backend. | Full-stack data flow established end to end. | `______` |
| **Week 14** | **11 Oct 2026 to 17 Oct 2026** | `33f7f2d3`, `b93e5b4b`, `b0262ff6`, `d3dc5fca`, `b0662a25`, `6b294a5e`, `e747e6d7`, `46584eb5`, `ce316b4d`, `f05aa7af`, `af92146c`, `d9549061`, `47bca314` | **Cloud Deployment, CI & Security Hardening:** Integrated Google Gemini LLM (`gemini-3-flash-preview`). Containerized via Docker and deployed to Render (`render.yaml`). Added GitHub Actions CI, keepalive, and nightly forecast workflows. Implemented reverse-proxy rate limiting. | Production cloud service is operational. Begin rigorous validation. | `______` |
| **Week 15** | **18 Oct 2026 to 26 Oct 2026** | `931ac2ab`, `510e0be4`, `7e20414c`, `dd1b8211`, `15b98b22`, `49caa0ef`, `c4b47245`, `e6782c9e`, `f634c186`, `76c31115`, `6d91bbcc`, `685d02fc` | **Empirical Validation, Testing & Final Report:** Executed 38-fold weekly backtest, 200-shift weather placebo test (weather rejected), and 68,883-unit Newsvendor simulation. Passed 44/44 Flutter tests and backend security tests. Resolved DEF-001 through DEF-007. Compiled Black Book. | Project work is fully verified, robustly tested, and ready for defense. | `______` |

---

## 5. Milestone Verification Sign-Off

* **Internal Guide / Faculty Mentor:** Dr. Srikanth Pulipeti `______________________`  
* **Head of Department:** Dr. Srikanth Pulipeti `______________________`  
* **Date:** October 26, 2026  
* **Place:** MPSTME, SVKM's NMIMS Shirpur Campus (M.H.), India  
