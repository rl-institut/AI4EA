# AI For Enegy Access (AI4EA)
### Reiner Lemoine Instut and Atlas AI for Lacuna Fund

This repository presents the context, code, and results of the Machine Learning (ML) approach to AI For Energy Access (AI4EA) inference component of the initiative.


## Objective

We will use the PeopleSun georeferenced survey responses (restricted access) that contains a reported census of appliances. The applicance counts are a predictor of electricity consumption. The appliance counts will be used to train a machine learning (ML) model to predict, i.e. infer, the estimated appliance types and number for out of sample areas.

Since the survey data were collected in specific zones in Nigeria, "out of sample" in this case implies other inhabited, settled communities in Nigeria and beyond.

In line with the broader goal of the project we will use the model to estimate appliance types and counts in four other countries.


## Summary Exploratory Data Analysis

While many different EDA were performed, some main insights are synthesized:
- the distributions of the number of appliances owned by HH are all right-skewed, i.e. most of the probability weight is in the lower end of the distribution
- for appliances such as laptops, radios, and televisions in particular it might be appropriate to treat the data as categorical, because most HHs either have none or one of each of these. 
- outliers may need to be handled through winsorization. for example, some HHs are reported to have 40 phone chargers, which needs to be handled in label pre-processing


![A count of appliances](figures/appliancesHH.png)


## Webmap

The webmap is provided as a tool to visualize and compare the load profiles generated interactively. 

### Local setup

After setting up a virtual environment, install the requirements with 
`pip install -r webmap/requirements.txt`

You need to download the data from URL and save it into `webmap/static/data`

- `*_stats.geojson` contains some indicators of the load profile: minimum (min), maximum (max), aggregated (sum), and average (mean) are calculated from the yearly minute resolution load profiles for each administrative level 2 (adm2 and adm1 properties). If the adm1 property is set to "dummy", it means that the adm2 property set identifies the regions uniquely. The indicators are also provided per household (same label with "hh_" as prefix, i.e "hh_max") to ease the comparison between regions. The household number (num_hh) and a cluster attribution (from 1 to 3) where generated from the ML model and are available as properties as well. 

- `*_timeseries_daily_avg.nc` This file is obtained from the `{country_iso}_all_intermediate_avg_*.csv` files from Harvard dataverse. See the `webmap/static/data/conversion_script.py` file to produce the `.nc` files yourself.  There is also a description of the same conversion process within the `DemandProfiles/analysis_template_daily_profiles.ipynb` file under the "Exporting data for further use in a webmap" section.