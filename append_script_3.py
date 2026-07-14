import sys

content = """
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
"""

with open("literature_review.md", "a", encoding="utf-8") as f:
    f.write("\n" + content)
