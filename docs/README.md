# RestockIQ Technical Documentation (`docs/`)

This directory houses the engineering, verification, simulation, and architectural documentation for **RestockIQ**.

---

## Directory Index

| File / Subdirectory | Purpose & Description | Context / Usage |
| :--- | :--- | :--- |
| [`architecture/`](file:///e:/CAP/docs/architecture/) | **System Architecture & Domain Plans** | High-level system design documents. |
| ├── [`Overall_Architecture_Plan.md`](file:///e:/CAP/docs/architecture/Overall_Architecture_Plan.md) | Multi-tier architecture overview | Details how the ML core, FastAPI read-layer, Gemini LLM narrator, and Flutter mobile client interact. |
| └── [`Unsold_Stock_Handling.md`](file:///e:/CAP/docs/architecture/Unsold_Stock_Handling.md) | Inventory carryover & markdown logic | Mathematical formulas for deterministic safety stock, perishable resets, and the Waste Action Engine. |
| [`TESTING_AND_INTEGRITY_REPORT.md`](file:///e:/CAP/docs/TESTING_AND_INTEGRITY_REPORT.md) | **Software Testing & Integrity Audit** | Comprehensive testing report covering 44 Flutter tests (Unit, Widget, Integration), 4 Backend security tests (rate limiting, multi-tenant isolation, Pydantic bounds), dataset quarantine, and manual device testing. |
| [`simulation_report.md`](file:///e:/CAP/docs/simulation_report.md) | **90-Day Inventory Simulation** | Empirical inventory simulation analyzing waste units, stockout days, and gross profit across safety stock levels ($z = 0.0$ to $z = 1.65$). |
| [`backtest_results.csv`](file:///e:/CAP/docs/backtest_results.csv) | **Rolling-Origin Benchmark Results** | Raw CSV metrics comparing RestockIQ Hybrid (23.43% WAPE) against Prophet (21.74%), Seasonal Naive (32.06%), and 4-Week Moving Average (41.63%). |
| [`dataset_audit.txt`](file:///e:/CAP/docs/dataset_audit.txt) | **Raw Dataset Audit & Quarantine Log** | Detailed validation report categorizing 2 usable real-world bakery/retail datasets and quarantining 5 synthetic/cross-sectional files. |

---

> [!NOTE]
> Academic Capstone review slides (Review I, Review II), literature review LaTeX drafts, and research papers are located in [`Documentation/`](file:///e:/CAP/Documentation/).
