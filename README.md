# AI For Enegy Access (AI4EA)
### Reiner Lemoine Instut and Atlas AI for Lacuna Fund

This repo presents the context, code, and results of the Machine Learning (ML) approach to AI For Energy Access (AI4EA) inference component of the initiative.




## Summary Exploratory Data Analysis

While many different EDA were performed, some main insights are synthesized:
- the distributions of the number of appliances owned by HH are all right-skewed, i.e. most of the probability weight is in the lower end of the distribution
- for appliances such as laptops, radios, and televisions in particular it might be appropriate to treat the data as categorical, because most HHs either have none or one of each of these. 
- outliers may need to be handled through winsorization. for example, some HHs are reported to have 40 phone chargers, which needs to be handled in label pre-processing


![A count of appliances](figures/appliancesHH.png)