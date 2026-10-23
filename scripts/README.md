# RestockIQ Utility & Operational Scripts (`scripts/`)

This directory houses development utilities, operational automation tools, ML backtesting runners, and repository validation scripts for **RestockIQ**.

---

## Directory Index

| Script | Purpose & Description | Execution Command |
| :--- | :--- | :--- |
| **[`audit_datasets.py`](file:///e:/CAP/scripts/audit_datasets.py)** | Scans and validates raw dataset files in `ML/data/raw/`. Checks column headers, row counts, timestamp ranges, and records quarantine decisions in `docs/dataset_audit.txt`. | `python scripts/audit_datasets.py` |
| **[`run_backtest.py`](file:///e:/CAP/scripts/run_backtest.py)** | Executes rolling-origin holdout backtests comparing RestockIQ Hybrid vs. Prophet-only, Seasonal Naive, and 4-Week Moving Average. Generates `docs/backtest_results.csv`. | `python scripts/run_backtest.py` |
| **[`run_waste_simulation.py`](file:///e:/CAP/scripts/run_waste_simulation.py)** | Runs a 90-day daily inventory simulation across 4 safety stock regimes ($z \in \{0.0, 0.5, 1.0, 1.65\}$) measuring waste units, stockout days, and gross profit. | `python scripts/run_waste_simulation.py` |
| **[`build_10slides_deck.js`](file:///e:/CAP/scripts/build_10slides_deck.js)** | Programmatically generates the 10-slide high-readability Software Testing presentation (`docs/software_testing_10slides.pptx`) with Montserrat/Inter fonts, Warm Tech theme, native PPTX shapes, and full speaker notes. | `node scripts/build_10slides_deck.js` |
| **[`build_testing_deck.js`](file:///e:/CAP/scripts/build_testing_deck.js)** | Programmatically generates the 15-slide comprehensive testing presentation (`docs/software_testing_presentation.pptx`). | `node scripts/build_testing_deck.js` |
| **[`manage_test_users.py`](file:///e:/CAP/scripts/manage_test_users.py)** | Database utility to create, list, and reset test tenants in MongoDB Atlas for multi-tenant isolation testing. | `python scripts/manage_test_users.py` |
| **[`manage_demo_user.py`](file:///e:/CAP/scripts/manage_demo_user.py)** | Provisions and seeds demo accounts (`demo@restockiq.com`) with sample bakery inventory items and alerts. | `python scripts/manage_demo_user.py` |
| **`search_repo.ps1` / `.sh`** | Cross-platform repository search helpers wrapping ripgrep. | `.\scripts\search_repo.ps1 "query"` |
| **`setup_search.ps1` / `.sh`** | Search tooling setup script. | `.\scripts\setup_search.ps1` |
| **`validate-all.ps1` / `.sh`** | Runs full test harness validating agents, skills, workflows, templates, and UTF-8 encoding. | `.\scripts\validate-all.ps1` |
| **`validate-agents.ps1` / `.sh`** | Validates agent configuration files and prompt schemas in `.agents/`. | `.\scripts\validate-agents.ps1` |
| **`validate-skills.ps1` / `.sh`** | Validates skill YAML frontmatter in `.agents/skills/`. | `.\scripts\validate-skills.ps1` |
| **`validate-workflows.ps1` / `.sh`** | Validates workflow markdown templates in `.agent/workflows/`. | `.\scripts\validate-workflows.ps1` |
| **`validate-templates.ps1` / `.sh`** | Validates template files in `.gsd/templates/`. | `.\scripts\validate-templates.ps1` |
| **`validate-encoding.ps1` / `.sh`** | Verifies clean UTF-8 encoding across all text and code files. | `.\scripts\validate-encoding.ps1` |
