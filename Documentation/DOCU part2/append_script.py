import sys

content = """
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
"""

with open("literature_review.md", "a", encoding="utf-8") as f:
    f.write("\n" + content)
