import sys

content = """
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
"""

with open("literature_review.md", "a", encoding="utf-8") as f:
    f.write("\n" + content)
