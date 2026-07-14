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


### 7. Mobile application for the intelligent management of small shops using the GPT-4 model
**Title:** Mobile application for the intelligent management of small shops using the GPT-4 model  
**Author(s) & Year:** Gonzalo Sakuda, Jack Leon, Royer Rojas (2024)  
**Paper details:** This study developed a mobile application powered by GPT-4 for small shop owners in Peru to optimize operations, automate routine tasks, and receive personalized business recommendations via a chatbot interface.  
**Model/Method used:** GPT-4 Large Language Model (as a conversational assistant and recommendation engine).  
**Dataset used:** Real-time user input and shop data (product sales, inventory details) provided by the shop owners via the app. Evaluated via a survey of 15 shop owners.  
**Results / Accuracy / Metrics:** Survey results indicated 66.67% of users rated the application a 4 or 5 out of 5 for usability and effectiveness. (No forecasting error metrics reported as it is an LLM-based assistant).  
**Limitations:** Qualitative evaluation only on a small sample (15 shops). No empirical evidence of increased profitability or reduced stockouts through rigorous mathematical time-series forecasting.  
**Connection to our PS / gap:** This paper addresses the accessibility gap (2) perfectly by showing how small retailers benefit from mobile-first, AI-assisted tools. However, it relies entirely on a generic LLM (GPT-4) for recommendations rather than a dedicated, math-based time-series forecasting model for inventory, leaving a gap in robust, empirical demand prediction (forecast-to-action gap).  

**Literature Review Paragraph:**
The integration of Artificial Intelligence into mobile platforms offers a promising avenue to enhance the operational capabilities of small retailers. Sakuda, Leon, and Rojas (2024) developed an Android application integrating the GPT-4 Large Language Model to act as an intelligent management assistant for small shops in Peru. Their system allowed users to query real-time sales data and receive conversational recommendations on inventory and promotions. A qualitative assessment revealed strong user approval, with 66.67% of surveyed shop owners rating the tool highly for usability. While this effectively demonstrates how to bridge the technological accessibility gap for small businesses, the study relies exclusively on generative AI for its insights rather than empirical forecasting models. It lacks a rigorous mathematical foundation for inventory predictions, relying instead on contextual LLM outputs. LocalDemand addresses this limitation by marrying the accessible mobile-app paradigm demonstrated here with the mathematical robustness of Facebook Prophet, ensuring that recommendations are driven by precise time-series calculations rather than generalized generative AI.

---

### 8. Optimizing Supply Chain Management for Small and Medium-Sized Businesses Using AI: A Comparative Analysis of GPT-4.5, Grok 3, Gemini 2.0, and DeepSeek R-1
**Title:** Optimizing Supply Chain Management for Small and Medium-Sized Businesses Using AI: A Comparative Analysis of GPT-4.5, Grok 3, Gemini 2.0, and DeepSeek R-1  
**Author(s) & Year:** Shreeyash Vyakarnam, Bharath Raju Kanchipuram Baburavi, Lawanya Awasthi, Abheek Abhijit Maiti, Manan Malik, Anumitha Panneerselvan (2025)  
**Paper details:** This research comparatively analyzed modern generative AI models against standard machine learning models (XGBoost, Random Forest) on their capability to solve supply chain tasks—specifically demand planning and vehicle routing—for SMBs.  
**Model/Method used:** Generative AI (GPT-4.5, Grok 3, Gemini 2.0, DeepSeek R-1), XGBoost, Random Forest.  
**Dataset used:** Kaggle "Zara Sales" dataset (for demand forecasting).  
**Results / Accuracy / Metrics:** DeepSeek R-1 demonstrated considerable promise in demand planning. However, none of the generative AI models successfully solved the vehicle routing problem due to computational complexity. (Explicit predictive metrics like RMSE were omitted in the source extract).  
**Limitations:** The models failed to solve complex deterministic logistics problems. The study focused on evaluating generic LLMs rather than implementing a specific, continuous forecasting system.  
**Connection to our PS / gap:** This paper touches on the accessibility gap (2) by exploring how SMBs can use low-cost Generative AI instead of expensive enterprise ERPs. However, it highlights that Generative AI models struggle with complex supply chain mathematics, reinforcing the need for LocalDemand's approach, which uses a specialized time-series model (Prophet) rather than a generalized LLM.  

**Literature Review Paragraph:**
As the capabilities of generative AI expand, its applicability to supply chain optimization for small and medium-sized businesses (SMBs) has garnered significant attention. Vyakarnam et al. (2025) conducted a comparative analysis of prominent generative models—including GPT-4.5, Grok 3, Gemini 2.0, and DeepSeek R-1—evaluating their capacity to execute demand planning and logistics tasks typically reserved for expensive ERP systems. While models like DeepSeek R-1 demonstrated promise in synthesizing demand planning insights from retail datasets, the authors found that all generative models failed to resolve complex, deterministic mathematical challenges such as the Vehicle Routing Problem. This reveals a critical limitation: while generative AI is highly accessible and cost-effective, it is fundamentally unsuited for rigorous numerical optimization in supply chains. This finding strongly supports the architectural decision behind LocalDemand. Rather than relying on generalized LLMs for mathematical forecasting, LocalDemand employs Facebook Prophet—a dedicated, purpose-built statistical engine—to ensure that inventory predictions are mathematically sound while maintaining the accessibility SMBs require.

---

### 9. Performance Analysis of Time Series Models to Predict Sales Activity of SMEs
**Title:** Performance Analysis of Time Series Models to Predict Sales Activity of SMEs  
**Author(s) & Year:** Justine Christian Susanto, Maureen Letitia Wiratama, Patrick Christian Nathaniel, Ivan Diryana Sudirman (2026)  
**Paper details:** This study evaluated forecasting models for an SME operating on a pre-order system, dealing with highly unstable daily sales, sporadic demand spikes, and frequent zero-transaction days (zero inflation).  
**Model/Method used:** XGBoost regression, 7-day Moving Average (MA(7)).  
**Dataset used:** Daily sales data from an SME (2023 to 2025).  
**Results / Accuracy / Metrics:** XGBoost struggled to consistently capture the sporadic sales dynamics due to extreme data sparsity. The simple 7-day Moving Average provided the most stable baseline results. (Exact error metrics were omitted from the extract).  
**Limitations:** Concludes that continuous daily regression approaches are insufficient for data with heavy zero-inflation, suggesting probabilistic or classification models might be better suited for pre-order models.  
**Connection to our PS / gap:** This paper directly addresses the data scarcity gap (1), specifically focusing on zero-inflation (days with zero sales) which is common in small businesses. However, it stops at prediction and does not convert the insights into actionable inventory replenishment recommendations (3).  

**Literature Review Paragraph:**
Forecasting for small enterprises is frequently complicated by highly irregular demand patterns and data sparsity. Susanto et al. (2026) investigated the efficacy of time-series models in predicting sales for an SME operating under a pre-order framework, a system characterized by sporadic demand spikes and high frequencies of zero-transaction days (zero inflation). The authors benchmarked an XGBoost regression model against a simple 7-day Moving Average. They discovered that despite its sophistication, XGBoost struggled to accurately capture the discontinuous nature of the pre-order data, with the basic moving average providing more stable baseline estimates. The study concluded that continuous regression models are fundamentally challenged by zero-inflated, low-volume data environments. This directly highlights the exact data scarcity gap that LocalDemand addresses. By acknowledging that standard regression models fail under sparse conditions, LocalDemand utilizes Facebook Prophet—which inherently handles missing data points and trend shifts more gracefully—and incorporates external regressors to stabilize predictions even when historical daily sales volumes are intermittent or zero-inflated.


### 10. Predictive Marketing and Sales Analytics Using Machine Learning for Small and Medium E-Commerce Enterprises
**Title:** Predictive Marketing and Sales Analytics Using Machine Learning for Small and Medium E-Commerce Enterprises  
**Author(s) & Year:** Swati Srivastava, Ramneek Kelsang Bawa, Neha Nagar, Richa Srivastava, Sadhana Sargam (2026)  
**Paper details:** This study explored the theoretical and practical application of machine learning techniques for predictive marketing and sales analytics in small and medium e-commerce enterprises, aiming to improve customer targeting and demand forecasting.  
**Model/Method used:** Classification, regression, and ensemble learning (General discussion/framework proposition).  
**Dataset used:** N/A (Theoretical review and framework paper).  
**Results / Accuracy / Metrics:** N/A (The paper discusses challenges, integration frameworks, and theoretical benefits rather than reporting specific empirical numerical performance).  
**Limitations:** It is primarily a theoretical review paper proposing a framework rather than an empirical study with a novel implementation. It lacks concrete numerical evidence of forecasting accuracy.  
**Connection to our PS / gap:** This paper confirms the accessibility gap (2) by acknowledging that budget constraints, perceived model complexity, and a lack of data infrastructure are major barriers for SMEs adopting machine learning. It reinforces the market need for highly accessible frameworks like LocalDemand.  

**Literature Review Paragraph:**
The transition from reactive to predictive analytics remains a significant hurdle for smaller digital businesses. Srivastava et al. (2026) provided a comprehensive review of how machine learning—specifically regression, classification, and ensemble methods—can be leveraged by small and medium e-commerce enterprises for demand forecasting and targeted marketing. While the authors effectively argue that machine learning dramatically outperforms traditional statistical summaries by capturing dynamic consumer behavior, their primary contribution lies in identifying the barriers to entry. The study highlights that budget constraints, perceived model complexity, and inadequate data infrastructure prevent widespread ML adoption among SMEs. Although this research is largely theoretical and lacks empirical error metrics, it perfectly frames the "accessibility gap" that plagues the SME sector. It validates the core premise of LocalDemand: for advanced predictive analytics to be viable for small businesses, they must be abstracted away from complex data infrastructure and delivered through highly accessible, user-friendly mobile interfaces that require zero technical expertise to operate.

---

### 11. Smart Sales Forecasting Machine Learning Models for Demand Prediction in Retail
**Title:** Smart Sales Forecasting Machine Learning Models for Demand Prediction in Retail  
**Author(s) & Year:** Sandeep V, Dr. Gowri R, Dr. Kandavel N, Thirumalai Murugan R, R Saivenkat, Zahid Hussain J (2025)  
**Paper details:** This research investigated how integrating external environmental variables (such as weather and fuel prices) alongside historical sales data into machine learning models can uncover demand patterns that traditional autoregressive techniques miss.  
**Model/Method used:** Hierarchical Agglomerative Clustering (HAC), K-Means Clustering, Decision Trees, and Linear Regression.  
**Dataset used:** Big Mart Sales (2013) dataset and a Dutch retail bicycle accessories dataset.  
**Results / Accuracy / Metrics:** The study concluded that grouping products via clustering prior to forecasting significantly improves scalability and prediction accuracy, though explicit error metrics (like MASE or RMSE) were omitted from the summary extract.  
**Limitations:** The models were evaluated on traditional, static datasets rather than being deployed in a live, highly volatile SME environment. The primary focus was on clustering product categories rather than generating daily, actionable restock quantities.  
**Connection to our PS / gap:** This paper validates the absolute necessity of integrating exogenous regressors (like weather) to improve accuracy, aligning closely with LocalDemand's architecture. However, it relies heavily on historical depth and static dataset testing, leaving the cold-start and actionability gaps (1 & 3) largely unresolved for new small businesses.  

**Literature Review Paragraph:**
Traditional forecasting methods that rely solely on historical sales data frequently fail to capture the nuances of consumer purchasing behavior, which is heavily influenced by the external environment. Sandeep et al. (2025) addressed this by developing a machine learning framework that incorporates external variables—such as weather conditions and economic indicators—into retail demand prediction. Utilizing K-Means and Hierarchical Agglomerative Clustering, the authors grouped products with similar demand profiles before applying decision trees and linear regression. Their findings indicate that augmenting historical data with environmental regressors significantly enhances forecasting adaptability and accuracy. While the study provides a strong methodological justification for using external data, its reliance on established, static datasets (e.g., Big Mart Sales) limits its applicability to the highly volatile, data-scarce reality of micro-SMEs. LocalDemand adopts the core philosophy of this research—specifically the integration of weather and holiday variables—but executes it using Facebook Prophet to explicitly handle the data scarcity and cold-start problems that standard regression and clustering algorithms struggle to manage.

---

### 12. State-Level Drug Retail Sales Forecasting Using XGBoost and Facebook Prophet
**Title:** State-Level Drug Retail Sales Forecasting Using XGBoost and Facebook Prophet  
**Author(s) & Year:** Mohit Kamboj, Deepti Kamboj, Khadija Naveed, Sonjoy Ranjon Das, Bilal Hassan, Touseef Tahir (2025)  
**Paper details:** This study developed a hybrid forecasting framework that combined Facebook Prophet (for robust time-series pattern decomposition) and XGBoost (to capture nonlinear effects of sales drivers on the residual) to predict state-by-day sales for a large German drugstore chain.  
**Model/Method used:** Hybrid Facebook Prophet + XGBoost (benchmarked against naive, SARIMA, Holt-Winters, and stand-alone models).  
**Dataset used:** Rossmann drugstore chain dataset in Germany (State-by-day sales data).  
**Results / Accuracy / Metrics:** The proposed hybrid algorithm delivered consistent improvements, cutting the median state-wise Mean Absolute Percentage Error (MAPE) by 12% to 18% compared to the best non-hybrid baselines.  
**Limitations:** The model was applied to a massive, multi-regional corporate retail chain (Rossmann). The forecasting was aggregated at the macro (state) level rather than the micro (individual store/product) level required for daily restocking.  
**Connection to our PS / gap:** This is highly relevant as it empirically validates Facebook Prophet’s superiority in retail contexts, specifically its ability to handle seasonality, holidays, and promotions. However, because it targets macro-level forecasting for a corporate enterprise, it leaves the SME accessibility gap (2) and the micro-level forecast-to-action gap (3) unresolved, which LocalDemand is specifically engineered to address.  

**Literature Review Paragraph:**
The increasing complexity of modern retail environments has led to the adoption of hybrid machine learning architectures that combine statistical interpretability with nonlinear pattern recognition. Kamboj et al. (2025) demonstrated this by developing a hybrid forecasting framework using Facebook Prophet and XGBoost to predict state-level sales for the Rossmann drugstore chain in Germany. Prophet was utilized to achieve robust time-series decomposition (handling holidays and seasonality), while XGBoost was applied to the residuals to capture the nonlinear effects of internal promotions and competitor proximity. The hybrid model outperformed classical baselines like SARIMA and Holt-Winters, reducing the median state-wise MAPE by 12% to 18%. This study provides powerful empirical validation for Facebook Prophet’s efficacy in retail demand forecasting, particularly regarding its handling of exogenous events like holidays. However, the study’s focus on macro-level (state-wide) forecasting for a massive corporate enterprise means its findings are not directly actionable for single-location SMEs. LocalDemand scales this advanced Prophet-based methodology down to the micro-level, applying it directly to individual menu items to generate accessible, localized restock recommendations for small food businesses.


### 13. Technology Acceptance and Security Influences on AI Adoption among Small and Medium Enterprises
**Title:** Technology Acceptance and Security Influences on AI Adoption among Small and Medium Enterprises  
**Author(s) & Year:** Yuniarty, Hartiwi Prabowo, Ridho Bramulya Ikhsan, Noe Enriquez (2025)  
**Paper details:** This study utilized the Technology Acceptance Model (TAM) to investigate the factors influencing the intention of Indonesian SMEs to adopt AI technologies, focusing on perceived ease of use, usefulness, and security.  
**Model/Method used:** Partial Least Squares–Structural Equation Modeling (PLS-SEM) on survey data.  
**Dataset used:** Survey data collected from 131 Indonesian SME owners and managers.  
**Results / Accuracy / Metrics:** The analysis revealed that perceived security and perceived ease of use are critical determinants of AI adoption intention. Interestingly, perceived usefulness alone did not substantially drive adoption intention without the presence of robust security and usability.  
**Limitations:** The study is purely survey-based and investigates managerial perceptions rather than evaluating the technical implementation or forecasting accuracy of a specific AI model.  
**Connection to our PS / gap:** This paper strongly reinforces the accessibility gap (2). It proves that small business owners will not adopt AI—regardless of its predictive power—unless the tool is exceptionally easy to use and secure. This heavily justifies LocalDemand’s design philosophy as a user-friendly, mobile-first application rather than a complex enterprise dashboard.  

**Literature Review Paragraph:**
The technological superiority of an AI model does not guarantee its adoption by small business owners. Yuniarty et al. (2025) explored this phenomenon by applying the Technology Acceptance Model (TAM) to survey 131 SME owners in Indonesia regarding their intention to adopt AI tools. Utilizing Partial Least Squares–Structural Equation Modeling (PLS-SEM), the researchers discovered that perceived ease of use and perceived security were the primary drivers of technology adoption. Surprisingly, the perceived usefulness (the actual functional capability) of the AI did not significantly drive adoption intention if the system was deemed difficult to use or insecure. This finding is highly consequential for the design of forecasting tools in the SME sector, directly highlighting the technological accessibility gap. It confirms that providing a mathematically sound forecast is insufficient; the delivery mechanism must be friction-less. LocalDemand is architected around this exact behavioral insight. By abstracting the complex Facebook Prophet mathematics behind a simple, secure, and intuitive Flutter mobile interface, LocalDemand ensures that the barrier to entry for SME owners is minimized, driving actual adoption and practical utility.

---

### 14. Technology Adoption of MSMEs in Food Supply Chain: The Role of AI in Traceability and Transparency
**Title:** Technology Adoption of MSMEs in Food Supply Chain: The Role of AI in Traceability and Transparency  
**Author(s) & Year:** Teerarat Aree, Pittawat Ueasangkomsate (2025)  
**Paper details:** This research examined the impact of AI technology adoption on traceability and transparency within the food supply chains of micro, small, and medium enterprises (MSMEs) in Thailand.  
**Model/Method used:** Linear regression analysis on survey data.  
**Dataset used:** Online questionnaire from 92 MSMEs in Thailand.  
**Results / Accuracy / Metrics:** Statistical analysis indicated that AI significantly and positively influences firm performance regarding traceability and transparency. However, the study emphasized that MSMEs severely lack the budget and know-how for technological investment.  
**Limitations:** The research focuses on qualitative supply chain metrics (traceability/transparency) via surveys rather than evaluating quantitative time-series forecasting accuracy for inventory optimization.  
**Connection to our PS / gap:** This paper further validates the accessibility gap (2) by explicitly confirming that MSMEs face severe financial and educational barriers to AI adoption. This justifies LocalDemand's approach of providing an automated, low-cost solution that requires zero technical know-how from the user.  

**Literature Review Paragraph:**
The integration of AI into food supply chains offers significant operational benefits, yet its penetration into the micro, small, and medium enterprise (MSME) sector remains stalled by resource constraints. Aree and Ueasangkomsate (2025) investigated the role of AI in enhancing traceability and transparency among 92 MSMEs in the Thai food supply chain. Through linear regression analysis, the study confirmed that AI adoption significantly improves supply chain integrity and firm performance. Crucially, however, the authors identified a massive barrier to entry: MSMEs fundamentally lack both the financial capital and the technical "know-how" required to invest in and operate standard AI solutions. This directly validates the accessibility gap that LocalDemand seeks to bridge. The study underscores that enterprise-grade AI supply chain solutions are economically and operationally out of reach for micro-businesses. By delivering automated inventory forecasting through a low-cost, low-code mobile platform, LocalDemand democratizes access to AI, allowing SMEs to optimize their supply chains without requiring dedicated IT budgets or data science expertise.

---

### 15. Weather-Integrated Recommendations for Food Choices with SHAP Explanation
**Title:** Weather-Integrated Recommendations for Food Choices with SHAP Explanation  
**Author(s) & Year:** Nikunj Jain, Priyanshu Jha, Jawed Hawari, K Dinesh Kumar (2024)  
**Paper details:** This study explored the use of machine learning to predict weather patterns and correlate them with shifting consumer food preferences for cloud kitchens, utilizing SHAP (SHapley Additive exPlanations) for model interpretability.  
**Model/Method used:** Random Forest, k-Nearest Neighbors (kNN), Decision Tree, Naïve Bayes, and Support Vector Machine.  
**Dataset used:** Weather History data alongside consumer food choice data.  
**Results / Accuracy / Metrics:** The study successfully demonstrated that machine learning classifiers can generate adaptive food menu suggestions based on prevailing weather conditions, helping to mitigate the estimated 30-40% mismatch between predicted and actual sales caused by weather fluctuations.  
**Limitations:** The system functions primarily as a classification/recommendation engine for menu items rather than providing continuous time-series forecasts of expected daily sales volumes for specific inventory management.  
**Connection to our PS / gap:** This paper directly addresses the forecast-to-action gap (3) and the necessity of external regressors. It proves that weather significantly impacts food demand and must be accounted for to reduce food waste. LocalDemand takes this concept further by using Prophet and weather regressors not just to recommend menu items, but to calculate the exact numerical quantities of ingredients to restock.  

**Literature Review Paragraph:**
Unpredictable weather fluctuations are a primary driver of demand volatility and subsequent food waste in the restaurant and cloud kitchen industry. Jain et al. (2024) addressed this challenge by developing a machine learning framework that correlates weather patterns with shifting consumer food preferences. Utilizing algorithms such as Random Forest and Support Vector Machines, augmented with SHAP for interpretability, the authors demonstrated that weather-integrated models could successfully generate adaptive menu recommendations. Their research highlighted a critical industry inefficiency: up to 40% of predicted sales in the food sector fail to materialize due to unforeseen external factors like weather. This study strongly validates the necessity of incorporating exogenous variables into demand planning to close the forecast-to-action gap. However, while Jain et al. focused on recommending which dishes to serve, LocalDemand advances this concept into quantitative inventory management. By utilizing Facebook Prophet configured with specific weather regressors, LocalDemand moves beyond qualitative menu suggestions to generate exact, mathematically derived restocking quantities, directly translating weather-integrated demand predictions into actionable supply chain decisions for SME owners.
