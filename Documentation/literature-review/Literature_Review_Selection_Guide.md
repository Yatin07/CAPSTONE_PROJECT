# Literature Review — Paper Selection Guide

## Instructions for Antigravity (paste this in with all papers attached)

You are helping select the final set of papers for a literature review supporting this problem statement. Evaluate every paper below against the criteria in this guide and produce a scored table plus a final keep/cut recommendation.

---

## Problem Statement (for relevance judging)

Small food businesses (bakeries, cafés, small restaurants) rely on guesswork for daily inventory decisions because affordable, easy-to-use forecasting tools don't exist for them — only expensive enterprise tools do. This causes overstocking (wastage, losses) and understocking (missed sales, unhappy customers). The project builds a mobile app that takes a business owner's own daily sales history, adds external factors (weather, holidays), runs it through a machine learning forecasting model (Prophet), and gives the owner a simple prediction plus a restock recommendation — no data science knowledge needed.

## The Three Research Gaps Every Paper Should Connect To
1. **Data scarcity / cold-start** — forecasting with limited historical data (not big-retailer-scale datasets)
2. **Accessibility gap** — small businesses lack access to affordable/usable forecasting tools
3. **Forecast-to-action gap** — most tools show a trend but don't generate an actual restock/inventory decision

## The Six Topic Sections
1. Forecasting methods (Prophet, ARIMA, LSTM, ensemble models, etc.)
2. Forecasting with small/sparse data
3. AI/ML adoption in small businesses (SMEs)
4. Weather/external factors in demand forecasting
5. Inventory optimization & restock decision systems
6. Mobile/app-based decision support for retail or food businesses

---

## Scoring Rubric — Score Every Paper 1–5 on Each Criterion

| Criterion | 5 (Strong) | 3 (Moderate) | 1 (Weak) |
|---|---|---|---|
| **Topic relevance** | Directly about food/retail demand forecasting, SME AI adoption, or inventory decisions | Adjacent domain (general supply chain, large retail) but same methods | Unrelated domain (manufacturing, energy, unrelated industry) even if same ML method |
| **Gap alignment** | Clearly supports one of the 3 gaps above (small data / accessibility / forecast-to-action) | Loosely touches a gap without directly addressing it | No connection to any of the 3 gaps |
| **Recency** | 2023–2026 | 2021–2022 (only keep if foundational/highly cited) | Pre-2021 |
| **Method usefulness** | Uses Prophet, ARIMA, LSTM, ensemble/RF/XGBoost, or a directly comparable forecasting method we can cite in our methodology section | Uses a related but less directly comparable method | Method has no bearing on our approach |
| **Source quality** | IEEE / peer-reviewed journal or conference | Reputable non-IEEE journal (Springer, Elsevier, MDPI) | Blog, whitepaper, non-peer-reviewed source |

**Total score = sum of all 5 criteria (max 25).**

---

## Decision Rules

- **Score 20–25 → Keep (core paper).** These directly support the argument and should be cited substantively, not just listed.
- **Score 14–19 → Keep only if the topic section is underrepresented** (see coverage check below). Otherwise cut.
- **Score below 14 → Cut**, regardless of how recent or well-published it is.
- **Duplicate/overlapping papers** — if two papers use the same method (e.g. both are "LSTM for retail sales") on a similar problem with similar findings, keep only the higher-scoring one. Cite the other as a supporting reference in a footnote at most, don't give it a full slot.
- **Pre-2021 papers** — only keep if it's a foundational/highly-cited method paper (e.g. the original Prophet paper, a seminal ARIMA/time-series text). Everything else pre-2021 gets cut regardless of score.

---

## Coverage Check (do this after scoring)

Build a count of surviving papers per topic section:

| Topic Section | Target minimum | Current count |
|---|---|---|
| 1. Forecasting methods | 4–5 | — |
| 2. Small/sparse data forecasting | 3–4 | — |
| 3. SME AI adoption | 3–4 | — |
| 4. Weather/external factors | 3–4 | — |
| 5. Inventory optimization / restock | 4–5 | — |
| 6. Mobile/app decision support | 2–3 | — |

**If any section is below its target minimum after cutting low scorers**, pull the best-available paper from that section back in even if its score is in the 14–19 range — a weak paper in an empty section is more valuable than a redundant strong paper in an already-full section. Flag any section that still can't hit its minimum even after this — that's a real gap in the search, not a scoring problem, and the relevant team member should do one more targeted search round rather than forcing in an irrelevant paper.

---

## Target Final Count

You currently have ~24 papers from one member, with ~7 more incoming from each of two teammates (~38 total pooled). Target for the final literature review: **18–22 papers.**

Selection order:
1. Score all pooled papers using the rubric above
2. Cut everything below 14
3. Run the coverage check — pull back any near-miss papers needed to hit section minimums
4. If still above 22 after that, cut the lowest scorers first from whichever section already exceeds its target minimum — don't cut evenly across all sections, cut from the most over-represented one

## Output Format Requested from Antigravity

Produce a table with: Paper title | Topic section | Score (out of 25) | Which gap it supports | Keep/Cut | One-line reason. Sort by topic section, then by score descending within each section.
