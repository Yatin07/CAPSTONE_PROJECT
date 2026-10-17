# 90-Day Inventory Waste vs. Stockout Simulation Report

**Generated On:** 2026-10-17 23:54:15  
**Evaluation Scope:** 90-day historical replay (2022-07-03 to 2022-09-30)  
**Dataset:** French Bakery Daily Production (`primary_items.csv`, 35 SKUs)  

---

## 1. Simulation Methodology & Core Assumptions

1. **Perishable Daily Inventory Life-Cycle:**
   - Bakery products are fresh items baked daily morning.
   - Unsold stock at the end of day cannot be sold next day (spoilage/donation rate = 100%).
   - Daily ending inventory resets to zero at start of day.
2. **Order & Restock Policy:**
   - Restock Order = $\max(0, \text{Round}(\hat{y} + \text{Safety Stock}))$
   - Lead time is 1 day (orders baked for morning opening based on preceding evening forecast).
3. **Safety Stock Formulation:**
   - Safety Stock = $z \times \sigma_{\text{item}}$
   - Service level target = 95% ($z = 1.65$).
   - $\sigma_{\text{item}}$ is calculated strictly on out-of-fold historical residuals prior to the simulation window.
4. **Economics & Cost Modeling:**
   - Retail Price ($P$): Realized price per article from dataset (mean ~€1.15 / baguette €0.90 / banette €1.05).
   - Cost of Goods Sold (COGS): Standard bakery COGS baseline = 40% of retail price.
   - Gross Margin: 60%.
   - Waste Cost: $\text{Wasted Units} \times \text{COGS}$.
   - Lost Sales Opportunity Cost: $\text{Stockout Units} \times \text{Retail Price}$.

---

## 2. Replay Performance Comparison

| Metric | RestockIQ Model (Prophet+GB) | Seasonal Naive (Lag 7) | 7-Day Moving Average |
| :--- | :---: | :---: | :---: |
| **Total Orders Placed** | **109,316** | 113,225 | 113,229 |
| **Total Realized Sales** | **68,145** | 67,520 | 67,604 |
| **Wasted Units (Spoilage)** | **41,171** | 45,705 | 45,625 |
| **Waste % of Production** | **37.66%** | 40.37% | 40.29% |
| **Wasted Production Cost** | **€22,440.74** | €24,614.50 | €24,562.78 |
| **Stockout Units (Unmet Demand)**| **738** | 1,363 | 1,279 |
| **Unmet Demand Rate** | **1.07%** | 1.98% | 1.86% |
| **Stockout Incidents (SKU-Days)**| **124** | 235 | 148 |
| **Service Level (In-Stock %)** | **95.77%** | 91.98% | 94.95% |
| **Estimated Gross Profit** | **€29,537.86** | €26,868.80 | €26,982.08 |

---

## 3. Comparative Delta & Business Impact

- **Waste Reduction vs. Seasonal Naive:** **-9.92%** (-4,534 units)
- **Waste Reduction vs. 7-Day MA:** **-9.76%** (-4,454 units)
- **Stockout Delta vs. Seasonal Naive:** **-45.85%** (-625 units)
- **Stockout Delta vs. 7-Day MA:** **-42.30%** (-541 units)
- **Net Profit Delta vs. Seasonal Naive:** **+€2,669.06** over 90 days
- **Net Profit Delta vs. 7-Day MA:** **+€2,555.78** over 90 days

---

## 4. Key Takeaways

1. **Superior Seasonal Ramp Handling:** The hybrid Prophet + Gradient Boosting model captures French holiday and tourist season shifts substantially better than the 7-day MA or seasonal naive approaches, which lag behind structural demand swings.
2. **Waste Mitigation without Service Degradation:** By dynamically sizing forecasts rather than relying on moving averages, the system reduces spoiled inventory without creating supply shortfalls during peak hours.
3. **Safety Stock Alignment:** The $1.65 \times \sigma$ safety buffer ensures that in-stock service level exceeds 90% across top products while controlling excess spoilage.
