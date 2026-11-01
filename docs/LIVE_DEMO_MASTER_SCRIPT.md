# RestockIQ: Live Demonstration Master Script

**Presentation Target**: 5 – 7 Minutes Live Mobile Walkthrough  
**Target Hardware**: Connected Android Device (`Redmi Note 10 Pro` via USB)  
**Tone**: Confident, engineering-grounded, clear, and concise.

---

## Quick Reference Table: What to Click vs What to Say

| Phase | Screen / Feature | What You Do (Phone Action) | What You Say (Simple Script) |
| :--- | :--- | :--- | :--- |
| **0. Hook** | Splash / Login Screen | Open app, show bottom server status chip. | *"RestockIQ is an automated demand forecasting and waste-mitigation system designed specifically for perishable artisan retail."* |
| **1. Overview** | Dashboard | Scroll across KPIs (Stock, Forecast, Alerts). | *"In a typical bakery or cafe, 15 to 25% of food is thrown away due to guesswork. RestockIQ replaces guesswork with mathematical inventory control."* |
| **2. Forecast & Graph** | Item Detail (e.g. Croissant / Milk) | Tap item card -> View **Sales vs Prediction** chart & Restock card. | *"Here is our daily demand prediction. The chart shows actual sales up to today (marked with a green dot), followed by our model's forecast for tomorrow. Notice the Restock Formula: it calculates the exact safety stock needed using Newsvendor economics, completely preventing over-ordering."* |
| **3. Mid-Day Pace** | Inventory Check-in -> Tab 1: **Mid-Day Pace** | Show 09:00, 14:00, or 20:00 alert tiers. | *"At 2 PM, if an item is selling slower than expected, the system flags it as an Amber or Red waste risk before it expires, recommending an immediate 20% discount or bundle."* |
| **4. Closing Count & Backfill** | Inventory Check-in -> Tab 2: **Closing Count** | Tap **Closing Count**, toggle between **Today** and **Yesterday (Backfill)**. | *(See Dedicated Walkthrough Below)* |
| **5. Yesterday Review** | Inventory Check-in -> Tab 3: **Yesterday Review** | Tap **Yesterday Review**, show sell-through badges (Green/Blue/Amber/Red). | *(See Dedicated Walkthrough Below)* |
| **6. AI Assistant** | Floating Assistant Button | Tap **"Ask RestockIQ Assistant"** -> Ask *"What needs my attention right now?"* | *"Our AI assistant operates on a strict Zero-Math architecture. It never guesses or hallucinates numbers—it reads real-time database state to provide executive summaries."* |
| **7. Closing** | Demo Sandbox | Tap **Explore Demo Tour** -> Show 60-day dataset replay -> Exit. | *"With self-supervised data backfill, automated waste mitigation, and verified 24.89% WAPE accuracy, RestockIQ cuts retail food waste while protecting stock availability."* |

---

## Deep-Dive 1: What is "Yesterday Backfill" & How to Explain It

### Simple Definition
> **Yesterday Backfill** allows store managers who forgot (or were too busy) to log closing inventory last night to enter yesterday's leftover counts the next morning without breaking data integrity.

### Script to Say
> *"In real retail, managers often close late and forget to count inventory before midnight. If you open RestockIQ the next morning, you simply tap **'Yesterday (Backfill)'**.*  
>  
> *Behind the scenes, RestockIQ does three critical things:*  
> 1. *It calculates yesterday's actual sales: $\text{Sold} = \text{Available} - \text{Leftover}$.*  
> 2. *For perishable items like fresh baguettes, it records leftovers as waste and zeroes out the stale stock.*  
> 3. *It feeds that completed day into our machine learning history, immediately refining today's and tomorrow's forecasts.*  
> *To prevent fraud or tampered history, backfilling is strictly limited to yesterday."*

---

## Deep-Dive 2: What is "Yesterday Review Simulation" & How to Explain It

### Simple Definition
> **Yesterday Review** is the morning operational scorecard. It calculates the **Sell-Through Rate** for every item from yesterday's shift so managers immediately know what sold out and what generated waste.

### Script to Say
> *"When the morning manager arrives, they tap the **'Yesterday Review'** tab.*  
>  
> *Here, the system calculates the exact **Sell-Through Rate**:  
> $$\text{Sell-Through} = \frac{\text{Units Sold}}{\text{Available Stock}}$$  
>  
> *Items are automatically classified into 4 intuitive color tiers:*  
> - 🟢 **High (>90%)**: Excellent demand; item nearly or completely sold out.  
> - 🔵 **Normal (70% - 90%)**: Ideal target balance between sales and stock buffer.  
> - 🟡 **Low (35% - 70%)**: Slow-moving item; triggered mid-day discount warnings.  
> - 🔴 **Critical (<35%)**: Severe excess; generated avoidable perishable waste.*  
>  
> *This closes the feedback loop: managers see yesterday's outcome, and the ML engine updates its priors for the next restock cycle."*

---

## Reviewer Defense & Q&A Cheat Sheet (Short & Crisp)

**Q1: Why GBDT / Statistical Blend instead of Deep Learning (LSTM/Transformers)?**  
*Answer*: Small retail store data is intermittent and scarce (often only 30–60 days). Deep learning overfits severely on short series. Our LightGBM GBDT achieves a benchmark **24.89% WAPE**, outperforming moving averages by 7.6 percentage points with sub-millisecond execution.

**Q2: What happens if a store is brand-new with 0 days of data?**  
*Answer*: We use cold-start category priors (e.g. 24 units for Bakery, 18 for Beverages). Between days 1 and 27, credibility shrinkage ($W = \frac{n}{n+14}$) gradually shifts weight from the category prior to the store's own empirical pace. At 28+ days, it switches to a full own-data blend.

**Q3: How does the AI Assistant avoid hallucinating numbers?**  
*Answer*: The LLM is restricted from performing math. It is provided structured JSON metrics directly from MongoDB (current stock, alerts, restock quantities) and strictly acts as an executive narrator.

**Q4: Can a manager accidentally double-apply a discount or corrupt stock?**  
*Answer*: All discount and restock actions are strictly idempotent. Tapping a 20% discount multiple times will not compound, and restock quantities can never drop below zero.

