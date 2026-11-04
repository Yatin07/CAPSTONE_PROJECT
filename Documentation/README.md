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
└── tools/                         # Slide automation scripts and pptx presentation tools
```

---

## 📑 Detailed Component Catalog

### 1. [`academic-reviews/`](file:///e:/CAP/Documentation/academic-reviews/)
* **`G1-PPT-Review-I.pptx`**: Capstone Review I presentation covering problem statement, domain overview, literature survey, and preliminary system design.
* **`G1-PPT-Review-II.pptx`**: Capstone Review II presentation covering ML forecasting methodology, Prophet/GBDT ablation studies, and Flutter prototype.
* **`improved_slides.pptx`**: Redesigned presentation slides implementing enhanced typographic hierarchy and layout cards.

### 2. [`black-book/`](file:///e:/CAP/Documentation/black-book/)
* **`final/`**: Master University Capstone Project Report (`RestockIQ_Black_Book.docx` & `RestockIQ_Black_Book.pdf`).
* **`drafts/`**: Pre-submission and intermediate review drafts (`CAPSTONE_PROJECT_BLACK_BOOK.*`, `Restock_citated_chinmay*`).
* **`log-book/`**: Completed project log book deliverables (`CAPSTONE_PROJECT_LOG_BOOK.*`).
* **`audit/`**: Gap analysis and alignment audit documentation.
* **`assets/`**: High-resolution figures and extracted diagrams for report chapters.

### 3. [`literature-review/`](file:///e:/CAP/Documentation/literature-review/)
* **`LocalDemand_LitReview_IEEE.tex`**: Literature review formatted in standard two-column IEEE Conference template with BibTeX citations.
* **`LocalDemand_Final_Literature_Review.tex`**: Extended LaTeX literature review manuscript.
* **`LocalDemand_Final_Literature_Review.md`**: Markdown version of the final literature review for fast search and reading.
* **`LocalDemand_Final_Paper_Table.md`**: Comparative matrix cross-referencing authors, models (ARIMA, Prophet, LSTM, XGBoost), datasets, and reported accuracy metrics.
* **`Literature_Review_Selection_Guide.md`**: Rationales and relevance criteria for selecting each surveyed paper.

### 4. [`research-paper/`](file:///e:/CAP/Documentation/research-paper/)
* **`IEEE_Conference_Paper.docx`**: Camera-ready IEEE format conference manuscript.
* **`generate_paper.py`**: Automated script for assembling the manuscript sections from verified repository data.
* **[`latex/`](file:///e:/CAP/Documentation/research-paper/latex/)**: Self-contained IEEE LaTeX conference paper suite:
  * `main.tex`: Modular manuscript with `\input` tables and `\includegraphics` figures.
  * `main_standalone.tex`: Inlined single-file LaTeX source for Overleaf submission.
  * `paper_v2.tex`: Extended benchmark revision manuscript.
  * `references.bib`: Complete BibTeX bibliography resolving all 25 cited keys.
  * `IEEEtran.cls` & `IEEEtran.bst`: Official IEEE conference document class and bibliography style.
  * `figures/`: High-resolution figures (`architecture.jpg`, `fig_accuracy_benchmark.png`, `fig_weather_placebo_distribution.png`, `fig_profit_waste_frontier.png`).
  * `tables/`: Auto-generated LaTeX tables (`table_38fold.tex`, `table_summer.tex`, `table_simulation.tex`, `table_weather.tex`, `table_citations.tex`).
  * `RestockIQ_IEEE_Overleaf.zip` & `RestockIQ_Overleaf_Single_Main.zip`: Ready-to-upload Overleaf project bundles.
  * `notes.txt` & `refs25.txt`: Context notes and claim mappings for the 25 cited papers.

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
* **`merge_pptx4.py`**: PPTX merging utility to assemble final multi-section presentation decks.
* **`check_layouts.py` / `dump_pptx.py`**: Layout inspection utilities to parse shapes, placeholders, and coordinates from existing presentations.
