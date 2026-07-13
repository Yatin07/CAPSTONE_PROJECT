# Literature Review Breakdown

### 1. A Mobile Application for Inventory Management to Support Digital Transformation in Small Retail Businesses
**Title:** A Mobile Application for Inventory Management to Support Digital Transformation in Small Retail Businesses  
**Author(s) & Year:** Thanakrit Janchidfah, Pisit Chansuek, Pirat Worasiri (2026)  
**Paper details:** This study developed and evaluated "Stock Easy," a lightweight mobile application designed to simplify product data management, stock tracking, and inventory updates for small retail businesses, aiming to facilitate digital transformation.  
**Model/Method used:** Technology Acceptance Model (TAM), descriptive statistics, and Pearson correlation analysis. (No predictive forecasting model used).  
**Dataset used:** Survey data from 132 users (retail owners, online sellers, store managers, and staff in Thailand).  
**Results / Accuracy / Metrics:** Users reported high overall satisfaction (mean = 4.43/5), particularly for ease of use (mean = 4.52/5). A strong positive correlation (r = 0.76) was found between user satisfaction and digital transformation readiness.  
**Limitations:** The scope is strictly limited to manual inventory tracking and usability evaluation; it completely lacks predictive capabilities or demand forecasting.  
**Connection to our PS / gap:** This paper heavily addresses the accessibility gap (2) by demonstrating that small retailers require lightweight, user-friendly mobile tools rather than complex enterprise software. However, it reinforces the forecast-to-action gap (3), as it relies entirely on manual input and offers no proactive restock intelligence.  

**Literature Review Paragraph:**
In addressing the digital transformation needs of small and medium enterprises (SMEs), Janchidfah et al. (2026) demonstrate the efficacy of lightweight, user-centered mobile applications over complex enterprise resource planning systems. The authors developed "Stock Easy," an inventory management tool, and evaluated it using the Technology Acceptance Model (TAM) with 132 retail stakeholders. Their findings indicate that perceived ease of use (mean = 4.52) and process clarity are critical drivers of user satisfaction, which in turn strongly correlates with an organization's readiness for digital transformation (r = 0.76). While the study successfully highlights the necessity of accessible, mobile-first solutions for small retailers, the application remains functionally reactive. It relies on manual stock tracking and lacks predictive analytics. This highlights a significant opportunity for our proposed application, LocalDemand, which will build upon this accessible mobile framework by integrating proactive, machine-learning-driven demand forecasting.

---

### 2. Comparative Evaluation of SARIMA, FB Prophet, and LSTM for Hourly Demand Forecasting in Saudagar Kopi
**Title:** Comparative Evaluation of SARIMA, FB Prophet, and LSTM for Hourly Demand Forecasting in Saudagar Kopi  
**Author(s) & Year:** Kevina Syahla Aqila, Revaldy Arya Kusuma, Muhamad Reynaldi AliSafitrah, Rahma James Galliano Setiardi, Tuga Mauritsius, Eka Miranda (2026)  
**Paper details:** This research empirically evaluated three forecasting models to predict hourly customer demand and peak-hour congestion at a high-traffic coffee shop, aiming to improve resource allocation and reduce service delays.  
**Model/Method used:** SARIMA, FB Prophet, and Stacked LSTM.  
**Dataset used:** Hourly POS sales data from Saudagar Kopi in Jakarta (April–June 2025) comprising 8,903 rows, focusing primarily on their highest-volume product (Long Black).  
**Results / Accuracy / Metrics:** LSTM achieved the lowest forecasting error with an RMSE of 0.1535. FB Prophet achieved an RMSE of 0.46, and SARIMA achieved an RMSE of 0.5265 during the morning rush.  
**Limitations:** The observation period was very brief (three months), the data was limited to a single coffee shop, and the analysis was restricted to forecasting a single high-volume product, ignoring cold-start issues for new items.  
**Connection to our PS / gap:** This study directly addresses the accessibility gap (2) by applying advanced forecasting to a small coffee shop. However, it stops entirely at prediction, strongly reinforcing the forecast-to-action gap (3) because it offers no systematic way to convert these hourly volume predictions into actionable restock recommendations.  

**Literature Review Paragraph:**
Recent advancements in demand forecasting have increasingly targeted the operational inefficiencies of small food and beverage businesses. Aqila et al. (2026) conducted a comparative empirical evaluation of SARIMA, FB Prophet, and LSTM models to predict high-frequency, hourly demand at a Jakarta coffee shop. The authors incorporated exogenous variables, such as rush-hour and holiday indicators, to handle significant demand volatility. Their results revealed that while LSTM provided the highest accuracy (RMSE = 0.1535), FB Prophet also produced highly stable and interpretable forecasts (RMSE = 0.46) by effectively managing weekly and daily seasonality. Despite demonstrating that complex time-series models can successfully anticipate peak congestion in SME environments, the study remains purely analytical. It successfully predicts customer volume but fails to translate these insights into automated inventory decisions. LocalDemand addresses this exact limitation by utilizing a Prophet-based architecture not just to forecast sales, but to explicitly generate actionable daily restock recommendations.

---

### 3. Enhanced sales forecasting of perishable and non-perishable goods using weather data with insights on Imports and price sensitivity
**Title:** Enhanced sales forecasting of perishable and non-perishable goods using weather data with insights on Imports and price sensitivity  
**Author(s) & Year:** Lalitha R, Sreelekha Ponugoti, Aisvarya S, Hanne Jenifer R, Dhanusree A R (2025)  
**Paper details:** This project developed a system to forecast restaurant sales and optimize dynamic pricing by analyzing how external factors—specifically real-time weather conditions and ingredient prices—affect the demand for perishable and non-perishable goods.  
**Model/Method used:** Random Forest and ARIMA.  
**Dataset used:** [Not explicitly specified in source extract; relies on aggregated historical sales, weather, and ingredient price data].  
**Results / Accuracy / Metrics:** The model achieved a Mean Squared Error (MSE) of 53.97.  
**Limitations:** The system relies on continuous real-time data streams (weather, live ingredient costs) which can be cost-prohibitive or technically complex for small businesses to maintain.  
**Connection to our PS / gap:** This paper touches on the forecast-to-action gap (3) by using predictions to drive dynamic pricing. However, it applies actionability to pricing rather than inventory restocking, meaning the gap regarding physical inventory management for small businesses remains partially unaddressed.  

**Literature Review Paragraph:**
External environmental variables, particularly weather and market fluctuations, play a critical role in consumer dining behavior. Lalitha et al. (2025) integrated historical sales, local weather data, and ingredient costs into a machine learning framework to forecast restaurant demand for perishable and non-perishable goods. Utilizing Random Forest and ARIMA models, the authors achieved a high predictive accuracy (MSE = 53.97) and developed a dynamic pricing engine capable of adjusting menu prices in real-time based on fluctuating external drivers. While this approach successfully moves beyond mere prediction by implementing an actionable pricing strategy, it is highly reliant on continuous, real-time data streams that may be inaccessible to smaller enterprises. Furthermore, the actionability is focused entirely on revenue maximization through pricing rather than physical inventory control. LocalDemand pivots from this pricing-centric model to focus on the operational side, using similar external regressors (like weather) to generate accessible, automated restock recommendations for SMEs.

---

### 4. Evaluation of Optimized LSTM and Moving Average in SME Inventory Forecasting and Simulation
**Title:** Evaluation of Optimized LSTM and Moving Average in SME Inventory Forecasting and Simulation  
**Author(s) & Year:** Intan Rahmatillah, Patah Herwanto, Ivan Diryana Sudirman (2026)  
**Paper details:** This study evaluated daily demand forecasting for a food and beverage SME (specifically for ice cream) by comparing a basic 7-day moving average against a Grid Search-optimized LSTM. It uniquely extended its evaluation into a weekly purchasing cycle simulation to assess real-world operational impacts on inventory.  
**Model/Method used:** 7-day Moving Average (MA(7)) and Long Short-Term Memory (LSTM) optimized via Grid Search.  
**Dataset used:** Daily POS transaction data from an SME (March 2023 to December 2025, approximately 1,030 daily observation points).  
**Results / Accuracy / Metrics:** The optimized LSTM outperformed the baseline with an RMSE of 1.65 and MAPE of 45.06% (compared to MA(7)’s RMSE of 1.84 and MAPE of 46.60%). The LSTM simulation completely eliminated lost demand, though it yielded a slight excess inventory of 1.57 units.  
**Limitations:** Focuses on a single established product with a long history, ignoring cold-start scenarios for new items. The simulation was strictly unit-based and lacked explicit cost-dynamic modeling.  
**Connection to our PS / gap:** This paper actively bridges the forecast-to-action gap (3) by taking raw predictions and running them through an inventory purchasing simulation, proving that algorithmic forecasting can tangibly eliminate stockouts. It also touches on data scarcity (1) by modeling daily SME data, though it relies on years of historical data rather than addressing cold-start items.  

**Literature Review Paragraph:**
While many forecasting studies stop at calculating error metrics, Rahmatillah, Herwanto, and Sudirman (2026) emphasize the necessity of translating predictive accuracy into operational inventory metrics. The authors compared an optimized LSTM network against a baseline 7-day moving average using daily sales data from an ice cream SME. The optimized LSTM not only achieved a superior predictive accuracy (RMSE = 1.65, MAPE = 45.06%), but more importantly, it eliminated lost demand entirely when applied to a simulated weekly purchasing cycle. Despite generating a negligible overstock of 1.57 units, the study successfully validates the premise that deep learning can directly inform SME procurement strategies. However, the model relied on a rich dataset (nearly 1,000 days of history for a single item) and did not address the integration of external regressors. LocalDemand builds upon this operational simulation approach but adapts it for Prophet-based predictions, integrating weather data and specifically designing around the cold-start limitations where such extensive historical data is unavailable.

---

### 5. Factors influencing audit quality through the acceptance and use of AI by auditors in Thailand, affiliated with SMEs audit firms
**Title:** Factors influencing audit quality through the acceptance and use of AI by auditors in Thailand, affiliated with SMEs audit firms  
**Author(s) & Year:** Kacha Somjaipeng, Watchareewan Jitsakul (2026)  
**Paper details:** This research investigated the technological, organizational, and environmental drivers that influence how SME-affiliated professionals accept and use AI tools, utilizing structured modeling to determine how adoption impacts service quality.  
**Model/Method used:** Technology Acceptance Model (TAM), Technology-Organization-Environment (TOE) framework, and Partial Least Squares - Structural Equation Modeling (PLS-SEM). (No predictive forecasting model used).  
**Dataset used:** Survey data collected from 120 auditors working at small and medium-sized companies in Thailand.  
**Results / Accuracy / Metrics:** The structural model explained 73.73% of the variance in perceived AI benefits and 71.24% in AI acceptance and use. Legal regulations/environmental factors showed a statistically significant positive relationship with perceived benefits (β = 0.562, p < .05).  
**Limitations:** The study is qualitative, survey-based, and highly specific to the auditing domain and Thai regulatory environment, lacking any application to physical inventory or time-series prediction.  
**Connection to our PS / gap:** This paper informs the accessibility gap (2) from a behavioral standpoint. It demonstrates that for SME professionals to adopt advanced AI tools, environmental factors and clear perceived benefits are paramount. It does not address the data scarcity (1) or forecast-to-action (3) gaps.  

**Literature Review Paragraph:**
Understanding the behavioral and environmental drivers behind SME technology adoption is critical for ensuring the successful deployment of AI solutions. Somjaipeng and Jitsakul (2026) utilized the Technology-Organization-Environment (TOE) framework and the Technology Acceptance Model (TAM) to evaluate AI adoption among 120 SME-affiliated auditors in Thailand. Using PLS-SEM analysis, they found that environmental factors—particularly regulatory frameworks—had a significant positive influence (β = 0.562) on the perceived benefits of AI, explaining over 70% of the variance in AI acceptance. Although this study operates within the auditing sector rather than food service, it yields a crucial insight for the development of SME-focused technology: algorithmic superiority alone does not guarantee adoption. Solutions must be perceived as highly beneficial and environmentally aligned with the user’s daily constraints. This principle underpins the design philosophy of LocalDemand, which addresses the SME accessibility gap by wrapping complex Prophet forecasting within an intuitive, highly accessible Flutter mobile interface that requires minimal technical expertise from the business owner.

---

### 6. LSTM-Based Hourly Sales Forecasting in SME Food and Beverage Retail
**Title:** LSTM-Based Hourly Sales Forecasting in SME Food and Beverage Retail  
**Author(s) & Year:** Moch Azis Munawar, Ivan Diryana Sudirman (2026)  
**Paper details:** Attempted to optimize inventory and reduce over/understocking costs for a culinary SME by predicting hourly ice cream sales. The study evaluated an LSTM network against standard baseline approaches that struggle to capture strong daily seasonal patterns.  
**Model/Method used:** LSTM, Naive Forecast, 7-hour Moving Average (MA7), and Daily Seasonal Naive.  
**Dataset used:** Hourly Point-of-Sale (POS) transaction data from an SME culinary business.  
**Results / Accuracy / Metrics:** LSTM attained the best performance, yielding smaller MAE and RMSE compared to the Naive and MA7 models. Cost-based simulations demonstrated that LSTM successfully reduced potential losses from overstocking and understocking.  
**Limitations:** The model explicitly excludes external factors such as promotions, weather, and holidays, relying solely on internal historical time-series patterns.  
**Connection to our PS / gap:** This paper targets both the accessibility gap (2) and the forecast-to-action gap (3). It translates LSTM predictions into cost-based inventory simulations to prove financial viability for SMEs. However, its exclusion of exogenous regressors leaves a gap in accuracy that LocalDemand seeks to fill.  

**Literature Review Paragraph:**
The volatility of hourly sales in the food and beverage industry frequently causes inventory mismatches, leading to either costly spoilage or missed revenue. Munawar and Sudirman (2026) explored this issue by applying an LSTM network to forecast hourly ice cream sales in a culinary SME, benchmarking it against Naive, Moving Average, and Daily Seasonal Naive models. Their findings established that the LSTM model achieved the lowest MAE and RMSE by successfully capturing complex intra-day seasonal patterns that baseline models missed. Crucially, the authors extended their analysis to include cost-based simulations, demonstrating that LSTM-driven predictions actively reduce the financial penalties associated with overstocking and understocking. However, the authors explicitly acknowledged a major limitation: the model did not incorporate external drivers such as weather, holidays, or promotional events. LocalDemand directly addresses this recognized limitation. By utilizing Facebook Prophet configured with exogenous regressors for weather and holidays, LocalDemand captures the external demand shocks that purely autoregressive models miss, ultimately providing a more robust foundation for its automated restock recommendations.
