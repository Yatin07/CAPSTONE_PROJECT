# RestockIQ Academic Documentation & Research Archive (`Documentation/`)

This directory houses the academic deliverables, university capstone reports, literature reviews, curated research papers, and slide generation tooling for the **RestockIQ Capstone Project** (NMIMS MPSTME, Course 702IT0E035).

---

## 📂 Directory Organization

```
Documentation/
├── README.md                      # This index and context catalog
├── academic-reviews/              # Formal capstone review presentation decks (.pptx)
├── black-book/                    # University Final Project Report (Black Book) docx & assets
├── literature-review/             # Literature review manuscripts (IEEE LaTeX & Markdown)
├── research-paper/                # IEEE conference paper documents & generation scripts
├── research-papers/               # Curated library of 25 reference papers collected by team
├── summaries/                     # Text transcripts, notes, and structured JSON summaries
└── tools/                         # Slide automation scripts, pptx mergers, and raw dumps
```

---

## 📑 Detailed Component Catalog

### 1. [`academic-reviews/`](file:///e:/CAP/Documentation/academic-reviews/)
* **`G1-PPT-Review-I.pptx`**: Capstone Review I presentation covering problem statement, domain overview, literature survey, and preliminary system design.
* **`G1-PPT-Review-II.pptx`**: Capstone Review II presentation covering ML forecasting methodology, Prophet/GBDT ablation studies, and Flutter prototype.
* **`improved_slides.pptx`**: Redesigned presentation slides implementing enhanced typographic hierarchy and layout cards.

### 2. [`black-book/`](file:///e:/CAP/Documentation/black-book/)
* Master University Capstone Project Report ("Black Book") deliverables:
  * Chapter 1: Introduction & Problem Statement
  * Chapter 2: Literature Review & Gap Analysis
  * Chapter 3: Methodology & Proposed System Architecture
  * Chapter 4: Empirical Results, Accuracy Benchmarks & Simulation
  * Chapter 5: Software Implementation & User Interface Design
  * Chapter 6: Testing, Quality Assurance & Defect Lifecycle
  * Frontmatter: Certificates, declarations, acknowledgements, table of contents, and list of figures/tables.

### 3. [`literature-review/`](file:///e:/CAP/Documentation/literature-review/)
* **`LocalDemand_LitReview_IEEE.tex`**: Literature review formatted in standard two-column IEEE Conference template with BibTeX citations.
* **`LocalDemand_Final_Literature_Review.tex`**: Extended LaTeX literature review manuscript.
* **`LocalDemand_Final_Literature_Review.md`**: Markdown version of the final literature review for fast search and reading.
* **`LocalDemand_Final_Paper_Table.md`**: Comparative matrix cross-referencing authors, models (ARIMA, Prophet, LSTM, XGBoost), datasets, and reported accuracy metrics.
* **`Literature_Review_Selection_Guide.md`**: Rationales and relevance criteria for selecting each surveyed paper.

### 4. [`research-paper/`](file:///e:/CAP/Documentation/research-paper/)
* **`IEEE_Conference_Paper.docx`**: Camera-ready IEEE format conference manuscript.
* **`generate_paper.py`**: Automated script for assembling the manuscript sections from verified repository data.

### 5. [`research-papers/`](file:///e:/CAP/Documentation/research-papers/)
Curated collection of primary academic literature across 25 peer-reviewed papers:
* **`Keep chinmay/`**: 6 research papers focusing on retail demand forecasting, small business optimization, and restaurant sensitivity.
* **`Keep soumy/`**: 4 research papers focusing on sustainable food supply chains, predictive analytics, and automated warehousing.
* **`Keep yatin/`**: 15 research papers analyzing SARIMA vs Prophet vs LSTM, weather integration with SHAP, SME digital adoption, and perishable inventory management.

### 6. [`summaries/`](file:///e:/CAP/Documentation/summaries/)
* **`cap.docx` / `cap.txt`**: Consolidated project summary and domain synthesis.
* **`CHINMAY_CAP.docx` / `CHINMAY_CAP.txt`**: Capstone domain notes and research contributions.
* **`LocalDemand_Literature_Review.docx` / `LocalDemand_Literature_Review.txt`**: Word docx version of literature survey.
* **`literature_review.md`**: Markdown synthesis of key literature insights.
* **`summary.json`**: Structured JSON representation of paper attributes and findings.
* **`docs_text.txt`**: Extracted plain text for document searching.

### 7. [`tools/`](file:///e:/CAP/Documentation/tools/)
Automation tooling for programmatic PowerPoint creation and layout verification:
* **`improved_slides.js`**: Node.js script using `pptxgenjs` to programmatically build styled slides.
* **`create_ppt2.py` / `create_final_slides.py` / `design_pro_slides.py`**: Python-pptx generation scripts for Review II deck.
* **`merge_pptx.py` (v1–v4)**: PPTX merging utilities to assemble final multi-section presentation decks.
* **`check_layouts.py` / `dump_pptx.py`**: Layout inspection utilities to parse shapes, placeholders, and coordinates from existing presentations.
* **`dumps/`**: Intermediate text dumps (`all_papers_text.txt`, `dump.txt`, `dump_utf8.txt`, `dump_merged_utf8.txt`, `extraction_results.json`).
* **`archive/`**: Obsolete/scratch test files (`Trash/analyze_datasets.py`, `Trash/test.py`).
