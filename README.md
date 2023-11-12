# RouteAirPollEstimator
A library for estimating spatial-temporal air pollution exposure amounts by dividing routes.


## License
RouteAirPollEstimator / version 0.0.2
- install:

```python
!pip install RouteAirPollEstimator --upgrade

import RouteAirPollEstimator as rae

## make sure geopandas >= 0.14.0
```

## Usage (using sample simulation in library)

###### The RouteAirPollEstimator library creates a 'space-time complete air pollutant concentration surface' and involves the process of 'Overlaying spatiotemporal air pollutant surfaces with bicycle routes'. Preliminary data are required for this, and these data were provided in the form of sample data in the following process.


### 1. Preprocessing: generate space-time complete air pollutant concentration surface

###### This refers to the process of dividing the kriged air pollutant surface, which is provided in hourly intervals (h), into x_min minute intervals to create space-time complete data over a period of t hours.


<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_1.png" alt="Preprocessing(1): generate space-time complete air pollutant concentration surface" width="450"/>
</div>


#### 1.1. merging surface data

###### The first step involves merging the surface data available in hourly increments into a single dataset. The formula is as follows.

$$
ST_{(h,x)} = C_h + \left( \frac{C_{h+1} - C_h}{60} \right) \cdot x_{\text{min}}
$$

where

<i>ST<sub>(h,x)</sub></i> is the function defined for the given hour h and minute x.  
<i>C<sub>h</sub></i> is the air pollutant concentration at hour h.  
<i>C<sub>h+1</sub></i> is the air pollutant concentration at the hour following h.  
<i>x_<sub>min</sub></i> is the minute interval for temporal resolution.  


###### The preliminary data required should consist of air pollutant surface data stored in cell units within a fishnet-patterned shapefile (shp). This data must be saved in hourly increments. The naming convention for the fishnet dataset should follow the format: 'fishnet_[Month][Day][hour]h' (e.g., fishnet_4_16_7h, fishnet_4_16_8h). In this library, the work proceeds using the sample data provided.


``` python
fishnet_4_16_7h, fishnet_4_16_8h, fishnet_4_16_9h = rae.fishnet_4_16_7h, rae.fishnet_4_16_8h, rae.fishnet_4_16_9h

fishnet_4_16_7h.sample(5)
```

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_2_fishnet_sample.png" alt="Sample data of fishnet" width="650"/>
</div>


###### The columns we will use to merge process are 'Id' (the unique identifier for each cell), 'RASTERVALU' (the PM10 value for each cell), and 'geometry' (information on the polygon geometry).


``` python
data_h = rae.process_and_merge_dataframes(start_hour = 7, end_hour = 9, Pollutant_column = 'RASTERVALU', date = '2023_4_16')

data_h.head()
```

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_3_merged_fishnet.png" alt="Merged fishnet data" width="650"/>
</div>

###### Now, we have merged fishnet of air pollutant surface of 1 hour base. 



#### 1.2. Divide the air pollutant concentration surface into x-minute intervals

###### Now, based on the x minutes input by the user, the surface is linearly interpolated at x minute intervals to form time-space complete data. The equation is as follows.





###### T






$$
S_i = \text{Segment}(O, D, t_{\text{start}} + i \cdot x)
$$

where
<i>O</i> is Origin (= bicycle rental place)
<i>D</i> is Destination
 


where

$$
E_{\text{total}} = \sum_{i=1} E_i
$$
$$
E_i = ST_{(h_i)} \cdot \text{duration}(S_i)
$$

<i>S<sub>i</sub></i> is <i>i<sup>th</sup></i> segment in route <i>S</i>
<i>duration(S<sub>i</sub>)</i> equals x