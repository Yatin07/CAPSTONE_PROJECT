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

## 2. Machine Learning Feedback Loop (XGBoost Residuals)
If food is not selling, the historical sales data (`y`) being fed back into the Prophet + XGBoost model drops. 

1. **Trend Correction (Prophet):** Prophet will detect that the overall trend for that item is dropping and will automatically lower the baseline prediction for the following weeks.
2. **Shock Correction (XGBoost):** This is where XGBoost shines. If the food didn't sell because of an external shock (e.g., a sudden thunderstorm or a public holiday where the cafe was empty), XGBoost analyzes that weather/holiday data. The next time a thunderstorm is predicted, XGBoost will aggressively slash the Prophet forecast (the "residual correction" mentioned on Slide 9), ensuring the owner bakes significantly less food that day.

---

## Summary for the Panel / Viva
If the panel asks you this question, here is your 30-second script:

*"That is exactly why we built the **Restock Logic** layer instead of just giving the user the raw AI prediction. The AI predicts the demand, but our deterministic Python logic takes that demand and subtracts the **Current Inventory on Hand**. If we ordered 50 cakes yesterday and sold zero, the system sees 50 cakes on the shelf and recommends ordering zero today. Furthermore, those zero sales are fed back into our XGBoost model, which learns the negative trend and lowers all future predictions, ensuring the waste doesn't happen again."*
