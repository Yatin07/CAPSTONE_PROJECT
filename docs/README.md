# RestockIQ Technical Documentation (`docs/`)

This directory houses the engineering, verification, simulation, and architectural documentation for **RestockIQ**.

---

## 📂 Subdirectories

| Directory | Description | Key Contents |
| :--- | :--- | :--- |
| [`architecture/`](file:///e:/CAP/docs/architecture/) | **System Architecture & Domain Plans** | High-level system design documents, inventory carryover & unsold stock handling. |
| [`review/`](file:///e:/CAP/docs/review/) | **Code Audits & Walkthroughs** | Independent audit reports (`CODEX_FINDINGS.md`), structural walkthroughs, and integrity checklists. |
| [`final/`](file:///e:/CAP/docs/final/) | **Final Verification Milestones** | Milestone verification logs (`FINAL_VERIFICATION.md`) and pre-defense release checks. |
| [`qa/`](file:///e:/CAP/docs/qa/) | **Quality Assurance & Behavior Guides** | Expected app behaviors, operational state transition guides, and error handling protocols. |
| [`blackbook_assets/`](file:///e:/CAP/docs/blackbook_assets/) | **Black Book Academic Assets** | Figures, diagrams, and benchmark charts formatted for the university capstone report. |

---

## 📄 Key Engineering Documents

| Document | Purpose & Scope |
| :--- | :--- |
| [`ADAPTIVE_FORECAST.md`](file:///e:/CAP/docs/ADAPTIVE_FORECAST.md) | **Adaptive Real-Time Demand Engine Specification**<br>Details the 5-candidate rolling tournament, Bayesian shrinkage ($w = n/(n+K)$), 5% churn margin guard, Newsvendor safety stock, and strict leakage prevention (`$lt: for_date`). |
| [`TESTING_AND_INTEGRITY_REPORT.md`](file:///e:/CAP/docs/TESTING_AND_INTEGRITY_REPORT.md) | **Software Testing & Integrity Audit Report**<br>Comprehensive report detailing 124 automated tests (46 Flutter tests + 78 Backend tests), multi-tenant isolation, decision table rules, and CFG basis path coverage. |
| [`LIVE_DEMO_MASTER_SCRIPT.md`](file:///e:/CAP/docs/LIVE_DEMO_MASTER_SCRIPT.md) | **Live Demonstration Master Script**<br>Minute-by-minute step guide for running the live demonstration (store setup, inventory check-in, midday pace, AI daily briefing, waste mitigation). |
| [`simulation_report.md`](file:///e:/CAP/docs/simulation_report.md) | **90-Day Inventory Simulation Report**<br>Empirical financial and waste evaluation across 35 bakery SKUs (68,908 observed demand units), analyzing gross profit, stockouts, and waste savings (+€2,416.88 margin). |
| [`FINAL_RESULTS.md`](file:///e:/CAP/docs/FINAL_RESULTS.md) | **Consolidated Empirical Results**<br>WAPE benchmarks, cluster bootstrap confidence intervals, and ablation experiment summaries. |
| [`DEPLOY_CHECKLIST.md`](file:///e:/CAP/docs/DEPLOY_CHECKLIST.md) | **Production Deployment & Keep-Alive Runbook**<br>Pre-flight verification checklist for Render cloud deployment, environment secrets, and GitHub Actions cron keepalive. |
| [`PHONE_TEST_RUNBOOK.md`](file:///e:/CAP/docs/PHONE_TEST_RUNBOOK.md) | **Mobile Device Testing Runbook**<br>Step-by-step physical device and emulator validation procedures for Android. |

---

## 📊 Presentation Decks

* [`software_testing_10slides.pptx`](file:///e:/CAP/docs/software_testing_10slides.pptx): **10-Slide High-Readability Testing Deck** (Warm Tech design system, native shapes/charts, zero image pastes, spoken speaker notes).
* [`software_testing_presentation.pptx`](file:///e:/CAP/docs/software_testing_presentation.pptx): **15-Slide Comprehensive Technical Testing Deck** (EP/BVA boundaries, decision tables, state transitions, white-box $V(G)=5$ cyclomatic complexity).

---

## 📈 Experiment & Benchmark Datasets (CSV)

* `accuracy_experiments_v3.csv` / `accuracy_experiments_v3.md`: 38-fold temporal rolling-origin accuracy benchmark results.
* `ordering_policy_experiment_v3_verified.csv`: 90-day inventory simulation dataset across $z \in \{0.0, 0.5, 1.0, 1.65\}$.
* `weather_experiment_v2.csv` / `weather_placebo_results.csv`: Weather sensitivity and placebo covariate experiments.
* `model_a_controls_and_cluster_bootstrap.csv`: Control models and cluster bootstrap standard errors.
* `backtest_results.csv`: Historical rolling-origin baseline benchmarks.
* `dataset_audit.txt`: Raw dataset audit and data integrity report.
