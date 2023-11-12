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
    start_hour : start time of the data
    end_hour : end time of the data
    Pollutant_column : Column name of air pollution concentration
    date : date of the data (format: [YYYY]_[MM]_[DD]) that user wants to add.
    (should be the same name of input data. For example, if the data name is 'fishnet_4_16_7h', date should be '4_16' / if 'fishnet_04_16_7h, '04_16'.)
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
    data_h : data from previous stage (funtion: process_and_merge_dataframes)
    hourRange : List that specify the start hour and end hour (e.g., [7,9] if 7 to 9)
    minuteInterval : the minute interval for the time resolution (e.g., 5: 5minute intervals)
    
```


dust_7_9_5min.head()
```
<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_4_spacetimecomplete.png" alt="space-time complete data" width="650"/>
</div>


###### 위 예시에서는 7~9시 사이의 air pollutant surface를 5분 간격으로 선형 보간한 후, 이를 각각의 컬럼에 할당하여 space-time complete data를 만드는 과정을 보여주고 있다. 이제 만들어진 'dust_7_9_5min'데이터는 추후 경로 파일과 overlay되며 각 경로상에서의 dust exposure양을 구할 때 사용된다.


### 2. Overlay spatiotemporal Air pollutant surface and bicycle routes

<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_5_sudocode_overlay.png" alt="pseudo code for overlay" width="650"/>
</div>


#### 2.1 convert bicycle OD to routes that composes of segment

$$
S_i = \text{Segment}(O, D, t_{\text{start}} + i \cdot x)
$$

where
<i>O</i> is Origin (= bicycle rental place)  
<i>D</i> is Destination  


###### 여기서는 1) bicycle자체의 OD정보 및 path line을 가지고 있는 polyline gdf파일과 2) rental location의 Origin과 Destination 포인트 정보를 가지고 있는 gdf 파일이 필요하다. 1)의 경우 rae패키지에서 'bicy_OD_4_16_7_9'의 variable로 제공하며, 2)는 bicy_rental_loc의 variable이다. 이 과정에서는 user가 x minute (코드에서는 minuteInterval)을 넣어주면 각 route를 x minute을 단위로 하여 split한다.


``` python
bicy_OD_5min = rae.process_gdf(ODdata = rae.bicy_OD_4_16_7_9, OD_Oid = 'o_cd', OTime = 'o_time', DTime = 'd_time',
                           bicyLocPoints = rae.bicy_rental_loc, Loc_id = 'sta_id', minuteInterval = 5)

```
    ODdata : Bicycle Origin-Destination table that consists of Origin and Destinaton columns. Don't have to be shp, but need key columns of ID that matches with rental location ID
    OD_Oid : A column of starting location ID. It should match with rental location ID.
    OTime : A column of O Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    DTime : A column of D Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    bicyLocPoints : A table of bicycle rental location point data. It should be the point shp file that has 'geometry' column.
    Loc_id : A key column of rental location point ID which matches with OD_Oid
    minuteInterval : time interval of the result point-route data. Need to be the same value of 'minuteInterval' parameter in minuteIntervals_surface function.
```

bicy_OD_5min[12:17]
```
<div align="center">
<img src="/RouteAirPollEstimator/screenshot/fig_6_route_div_by_5min.png" alt="routes divided by 5 min interval" width="650"/>
</div>

```
o_time, d_time: origin, destination time
o_cd: origin location id
o_nm: origin location name
d_cd: destination location id
d_nm: destination location name
distRe: distance (m)
durRe: duration (minutes)
```

###### OD_Oid는 Origin rental location을 가지고 있는 ODdata의 ID 컬럼을 의미 (bicyLocPoints의 Loc_id와 일치). OTime과 DTime은 각각 출발 시간, 도착 시간을 가지는 컬럼을 의미한다.
###### 결과 df (bicy_OD_5min)는 결국 5분 단위로 split된 routes를 의미하며, 각 uniqID별 route가 5분단위로 잘려 multiple한 row들로 나누어 진 것을 확인할 수 있따. dur_new는 각 route에서 머문 시간 (분)을 의미한다.







$$
E_{\text{total}} = \sum_{i=1} E_i
$$
$$
E_i = ST_{(h_i)} \cdot \text{duration}(S_i)
$$

where

<i>S<sub>i</sub></i> is <i>i<sup>th</sup></i> segment in route <i>S</i>  
<i>duration(S<sub>i</sub>)</i> equals x  