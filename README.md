# RouteAirPollEstimator
A library for estimating spatial-temporal air pollution exposure amounts by dividing routes.


## License
RouteAirPollEstimator / version 0.0.2
- install:

```python
!pip install RouteAirPollEstimator --upgrade
```

## Usage (using sample simulation in library)

###### RouteAirPollEstimator는 ‘space-time complete air pollutant concentration surface’를 만들고, ~ 과정으로 되어있음. 이를 위해 선행적인 데이터들이 필요하며, 이 데이터들은 밑의 과정에서 sample data의 형태로 제공되었음.


### 1. Preprocessing: generate space-time complete air pollutant concentration surface

###### 다음과 같이 한시간 단위 (h)로 되어있는 t 시간동안의 krigged air pollutant surface를 x_min단위로 분할하여 space-time complete data로 만드는 과정을 의미한다.

<img src="/RouteAirPollEstimator/screenshot/fig_1.png" alt="Preprocessing(1): generate space-time complete air pollutant concentration surface" width="450"/>




#### 1.1. merging surface data

###### 첫번쨰로는 한 시간 단위의 surface data를 하나로 합쳐주는 과정을 가진다. 수식은 다음과 같다.

$$
ST_{(h,x)} = C_h + \left( \frac{C_{h+1} - C_h}{60} \right) \cdot x_{\text{min}}
$$

where

<i>ST<sub>(h,x)</sub></i> is the function defined for the given hour h and minute x.  
<i>C<sub>h</sub></i> is the air pollutant concentration at hour h.  
<i>C<sub>h+1</sub></i> is the air pollutant concentration at the hour following h.  
<i>x_<sub>min</sub></i> is the minute interval for temporal resolution.  


###### 선행적으로 가지고 있어야 할 데이터는 fishnet 형태의 shp파일로 저장된 cell단위의 air pollutant surface가 있어야 한다. 이 데이터는 한 시간단위로 저장이 되어있어야 한다. Names of fishnet dataset should follow this format: 'fishnet_[Month]_[Day]_[hour]h' (e.g., fishnet_4_16_7h, fishnet_4_16_8h)






