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


###### The example data is gdf format that has 'geometry' column. The columns we will use to merge process are 'Id' (the unique identifier for each cell), 'RASTERVALU' (the PM10 value for each cell), and 'geometry' (information on the polygon geometry).


``` python
data_h = rae.process_and_merge_dataframes(start_hour = 7, end_hour = 9, Pollutant_column = 'RASTERVALU', date = '2023_4_16')

``` 
    # start_hour : start time of the data
    # end_hour : end time of the data
    # Pollutant_column : Column name of air pollution concentration
    # date : date of the data (format: [YYYY]_[MM]_[DD]) that user wants to add.
    # (should be the same name of input data. For example, if the data name is 'fishnet_4_16_7h', date should be '4_16' / if 'fishnet_04_16_7h, '04_16'.)
```
data_h.head()
```

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_3_merged_fishnet.png" alt="Merged fishnet data" width="650"/>
</div>

###### Now, we have merged fishnet of air pollutant surface of 1 hour base.     




#### 1.2. Divide the air pollutant concentration surface into x-minute intervals

###### Now, based on the x minutes input by the user, the surface is linearly interpolated at x minute intervals to form time-space complete data. The equation is as follows.

``` python
dust_7_9_5min = rae.minuteIntervals_surface(data_h, hourRange = [7,9], minuteInterval = 5)

```
    # data_h : data from previous stage (funtion: process_and_merge_dataframes)
    # hourRange : List that specify the start hour and end hour (e.g., [7,9] if 7 to 9)
    # minuteInterval : the minute interval for the time resolution (e.g., 5: 5minute intervals)
```
dust_7_9_5min.head()
```
<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_4_spacetimecomplete.png" alt="space-time complete data" width="650"/>
</div>


###### The example above demonstrates the process of linearly interpolating the air pollutant surface between 7 and 9 a.m. at 5-minute intervals, then assigning it to respective columns to create space-time complete data. The resulting 'dust_7_9_5min' data will later be overlaid with the path files and used to calculate the amount of dust exposure along each route.





### 2. Overlay spatiotemporal Air pollutant surface and bicycle routes    

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_7.png" alt="overlay spatiotemporal air pollutant surface and bicycle routes" width="650"/>
</div>


<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_5_sudocode_overlay.png" alt="pseudo code for overlay" width="650"/>
</div>

###### <i>S</i> represents the route, and <i>j</i> denotes each agent. The starting point <i>O</i> is designated as the closer end of each route, which determines the direction of the route.
###### <i>N</i> becomes the number of segments resulting from dividing the Total duration <i>T</i> by <i>x</i> minutes.
###### Subsequently, a repetition operation from <i>i</i> to <i>N</i> occurs, where <i>Segment start</i> and <i>Segment end</i> are determined using the start time, <i>x</i>, and end time, respectively.
###### For each segment, the <i>ST</i> (air pollutant value from the space-time complete surface) at each time <i>h</i> and <i>x</i> minutes is calculated, and this <i>ST</i> is added to the total Exposure amount (<i>E<sub>total</sub></i>) for each agent's route.





#### 2.1 convert bicycle OD to routes that composes of segment    
 
$$
S_i = \text{Segment}(O, D, t_{\text{start}} + i \cdot x)
$$

where  

<i>O</i> is Origin (= bicycle rental place)  
<i>D</i> is Destination  


###### Here, two GeoDataFrame (gdf) files are needed: 1) a polyline gdf with the bicycle's own OD (origin-destination) information and path line, and 2) a gdf file with the Origin and Destination point information for rental locations. The former is provided as the variable 'bicy_OD_4_16_7_9' in the rae package, and the latter as the variable 'bicy_rental_loc'. During this process, when the user inputs x minutes (referred to as minuteInterval in the code), each route is split into x minute intervals.

``` python
bicy_OD_5min = rae.process_gdf(ODdata = rae.bicy_OD_4_16_7_9, OD_Oid = 'o_cd', OTime = 'o_time', DTime = 'd_time',
                           bicyLocPoints = rae.bicy_rental_loc, Loc_id = 'sta_id', minuteInterval = 5)

```
    # ODdata : Bicycle Origin-Destination table that consists of Origin and Destinaton columns. Don't have to be shp, but need key columns of ID that matches with rental location ID
    # OD_Oid : A column of starting location ID. It should match with rental location ID.
    # OTime : A column of O Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    # DTime : A column of D Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    # bicyLocPoints : A table of bicycle rental location point data. It should be the point shp file that has 'geometry' column.
    # Loc_id : A key column of rental location point ID which matches with OD_Oid
    # minuteInterval : time interval of the result point-route data. Need to be the same value of 'minuteInterval' parameter in minuteIntervals_surface function.
```
bicy_OD_5min[12:17]
```
<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_6_route_div_by_5min.png" alt="routes divided by 5 min interval" width="650"/>
</div>

```
<columns>
- o_time, d_time: origin, destination time
- o_cd: origin location id
- o_nm: origin location name
- d_cd: destination location id
- d_nm: destination location name
- distRe: distance (m)
- durRe: duration (minutes)
```

###### OD_Oid refers to the ID column of the ODdata that has the Origin rental location, matching the Loc_id in bicyLocPoints. OTime and DTime represent the columns that hold the departure and arrival times, respectively.
###### The resulting dataframe (bicy_OD_5min) represents routes split into 5-minute intervals, where each route with a unique ID is segmented into multiple rows for each 5-minute interval. dur_new denotes the duration (in minutes) spent on each route segment.    



 

#### 2.2 Overlay spatiotemporal Air pollutant surface and bicycle routes    

###### Finally, the total exposure amount on the route is calculated by finding the air pollutant surface values that spatially and temporally coincide with each segment.

$$
E_{\text{total}} = \sum_{i=1} E_i
E_i = ST_{(h_i)} \cdot \text{duration}(S_i)
$$

where  

<i>S<sub>i</sub></i> is <i>i<sup>th</sup></i> segment in route <i>S</i>  
<i>duration(S<sub>i</sub>)</i> equals x  


###### <i>E<sub>total</sub></i> represents the total amount of exposure to air pollution, calculated by summing the product of the <i>ST<sub>hi</sub></i>, which is the exposure amount for every <i>i</i>th segment, and the <i>duration S<sub>i</sub></i>, which is the time spent on each segment.



``` python
exposure_5min_7_9_gdf = rae.calculate_dust_exposure(ODdata = bicy_OD_5min, OTime = 'o_time', DTime = 'd_time', spatioTemporalSurface = dust_7_9_5min)

```
    # ODdata : Result gdf of the previous funtion (process_gdf), which have point route info
    # OTime : A column of O Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    # DTime : A column of D Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    # spatioTemporalSurface : The result gdf of minuteIntervals_surface function, which has spatiotemporal air pollutant surface.
```
exposure_5min_7_9_gdf.head()
```

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_8_result.png" alt="Result" width="650"/>
</div>


###### The term dust_con represents the constant exposure amount of dust at each vertex, while dust_exp refers to the total exposure amount of dust along the route. Ultimately, dust_exp is calculated by multiplying dust_con by the duration time dur_new (note that since dur_new is in minutes, it is converted to seconds before multiplying).


---

## Related Document: 
 will be added

## Author

- **Author:** Moongi Choi, Won Do Lee
- **Email:** u1316663@utah.edu
