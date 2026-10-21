# Handling Unsold Stock & Perishable Inventory Carryover

One of the most critical questions asked during a presentation on inventory forecasting is: 
**"What happens if we order food based on the prediction, but nobody buys it? Does the system just tell us to order more tomorrow, creating a massive pile of unsold food?"**

The answer is **No**. Our architecture specifically prevents this through a combination of **Deterministic Restock Logic** and **Machine Learning Feedback**.

Here is exactly how the RestockIQ system handles unsold stock.

---

## 1. The Mathematical Safety Net (Restock Logic)
As shown on **Slide 9 (Proposed Methodology)**, our system does not just blindly output the AI's predicted demand as the final answer. It passes the prediction through a mathematical "Restock Logic" filter.

The core formula running in our Python backend is:
> **Restock Quantity = (Predicted Demand + Safety Stock) - Current Inventory on Hand**

### Scenario A: Semi-Perishable Goods (e.g., Coffee Beans, Bottled Drinks, Frozen Dough)
Imagine the AI predicts you will sell 20 bottles of water tomorrow. However, yesterday was heavily rained out, and you sold **zero** of the 20 bottles you ordered. 
*   **Predicted Demand:** 20
*   **Current Inventory:** 20 (unsold from yesterday)
*   **Restock Output:** (20 + 0) - 20 = **0**

The Flutter app will recommend the owner order **0 bottles**. The system inherently protects against compounding over-ordering because it always subtracts physical, on-hand stock before making a recommendation.

### Scenario B: Highly Perishable Goods (e.g., Fresh Croissants, Hot Food)
For items that must be thrown away at the end of the day, the "Current Inventory" automatically resets to 0 (because the unsold items become waste). 
If the AI predicts a demand of 15 croissants for tomorrow, the restock recommendation will be 15. 
However, the AI is not stupid—it learns from the waste, which brings us to the second layer of protection.

---

## 2. Machine Learning Feedback Loop (Pooled Global XGBoost & Lags)
If food is not selling, the historical sales data (`y`) being fed back into the ML pipeline drops. 

1. **Trend Extraction (Prophet):** Prophet acts as our structural baseline. It will detect that the overall long-term trend for that item is dropping and will mathematically lower the seasonal curve for the following weeks.
2. **Immediate Shock Correction (Global XGBoost):** This is where the pooled global gradient-boosting model shines. It does not just look at Prophet's long-term trend; it cross-references it against yesterday's actual sales (`lag_1`) and the 7-day rolling average (`rolling_7day_mean`). Because it is trained globally across all items, it has learned a robust rule: *if Prophet predicts a massive seasonal spike, but `lag_1` is very low, ignore the seasonal spike.* If the food didn't sell due to a sudden shock (like a thunderstorm), the XGBoost layer detects the drop in the lag features and aggressively clamps down on Prophet's forecast for the next day, ensuring the owner bakes significantly less food until the actual sales velocity recovers.

---

## Summary for the Panel / Viva
If the panel asks you this question, here is your 30-second script:

*"That is exactly why we built the **Restock Logic** layer instead of just giving the user the raw AI prediction. The AI predicts the demand, but our deterministic Python logic takes that demand and subtracts the **Current Inventory on Hand**. If we ordered 50 cakes yesterday and sold zero, the system sees 50 cakes on the shelf and recommends ordering zero today. Furthermore, those low sales are fed back into our ML model as lag features. The pooled XGBoost engine sees the low sales from yesterday, learns the negative shock, and mathematically suppresses Prophet's future predictions, ensuring the waste doesn't compound."*
