#!/usr/bin/env python
# coding: utf-8

# In[30]:


import geopandas as gpd
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
from tqdm.auto import tqdm


# In[2]:


print(gpd.__version__)


# ## data

# In[3]:


# change path to relative path - only for publishing
current_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_directory)

fishnet_path = "./sampleData/AirPollutantSurface/"
fishnet_4_16_7h = gpd.read_file(fishnet_path + 'fishnet_100m_4_16_07h.shp')
fishnet_4_16_8h = gpd.read_file(fishnet_path + 'fishnet_100m_4_16_08h.shp')
fishnet_4_16_9h = gpd.read_file(fishnet_path + 'fishnet_100m_4_16_09h.shp')

locPath = "./sampleData/bicy_rental_loc/"
bicy_rental_loc = gpd.read_file(locPath + 'bicy_rental_loc.shp')

routePath = "./sampleData/bicy_route/"
bicy_OD_4_16_7_9 = gpd.read_file(routePath + 'bicy_sim_7_09.shp', encoding='utf-8')


# # 1. Preprocessing: spatiotemporal Surface data
# ## 1.1. merging surface data

# In[41]:


def process_and_merge_dataframes(start_hour, end_hour, Pollutant_column, date):
    
    '''
    Merge air pollution concentration fishnet .shp data into a single file, and format the column as a continuous date.
    Names of fishnet dataset should follow this format: 'fishnet_[Month]_[Day]_[hour]h' (e.g., fishnet_4_16_7h, fishnet_4_16_8h) and 1 hour interval
    
    Parameters
    ----------
    start_hour : start time of the data
    end_hour : end time of the data
    Pollutant_column : Column name of air pollution concentration
    date : date of the data (format: [YYYY]_[MM]_[DD]) that user wants to add.
    (should be the same name of input data. For example, if the data name is 'fishnet_4_16_7h', date should be '4_16' / if 'fishnet_04_16_7h, '04_16'.)

    Returns
    -------
    DataFrame
        A comma-separated values (csv) file is returned as two-dimensional
        data structure with labeled axes.

    Examples
    --------
    >>> import RouteAirPollEstimator as rae
    >>> fishnet_4_16_7h, fishnet_4_16_8h, fishnet_4_16_9h = rae.fishnet_4_16_7h, rae.fishnet_4_16_8h, rae.fishnet_4_16_9h
    >>> data_h = process_and_merge_dataframes(start_hour = 7, end_hour = 9, Pollutant_column = 'RASTERVALU', date = '2023_4_16')
    
    '''
    
    def process_dataframe(df, h):
        new_column_name = 'dust_' + str(h)
        df = df.rename(columns={Pollutant_column: new_column_name})
        return df
    
    data = None
    
    date_h = "_".join(date.split('_')[1:])
    date = date.replace('_', '-')
    # 날짜 형식을 datetime 객체로 변환
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    date_ymd = date_obj.strftime('%Y-%m-%d')
    
    
    
    for h in range(start_hour, end_hour+1):
        # 전역 변수에서 해당 시간의 DataFrame 가져오기
        df = globals().get('fishnet_' + date_h + '_' + str(h) + 'h')
        if df is not None:
            # DataFrame 처리
            processed_df = process_dataframe(df, h)
            # 첫 번째 시간대의 경우, data 변수에 할당
            if h == start_hour:
                data = processed_df
            # 그 외의 시간대의 경우, 기존 data DataFrame과 병합
            else:
                data = pd.merge(data, processed_df[['dust_' + str(h)]], left_index=True, right_index=True)
        else:
            print(f"DataFrame for hour {h} not found")
    
    #delete -9999
    data = data[data != -9999].dropna()
    
    #add date column
    data['date'] = date_ymd
    
    # 컬럼 재정렬
    first_columns = [col for col in data.columns if col.upper() in ['FID', 'TARGET_FID', 'ID']]
    dust_columns = [col for col in data.columns if col.startswith('dust_')]
    date_columns = ['date']
    last_columns = [col for col in ['geometry'] if col in data.columns]
    new_column_order = first_columns + dust_columns + date_columns + last_columns

    data = data[new_column_order]
    
    return data


# ## 1.2. Divide the air pollutant concentration surface data into x-minute intervals

# In[25]:


# 컬럼 이름 수정

def minuteIntervals_surface(data_h, hourRange, minuteInterval):

    '''
    Divide the 1-hour based air pollution concentration into x-minute intervals
    
    Parameters
    ----------
    data_h : data from previous stage (funtion: process_and_merge_dataframes)
    hourRange : List that specify the start hour and end hour (e.g., [7,9] if 7 to 9)
    minuteInterval : the minute interval for the time resolution (e.g., 5: 5minute intervals)
    
    Returns
    -------
    DataFrame
        A comma-separated values (csv) file is returned as two-dimensional
        data structure with labeled axes.

    Examples
    --------
    >>> dust_7_9_5min = minuteIntervals_surface(data_h, hourRange = [7,9], minuteInterval = 5)
    
    '''
    
    
    df = data_h.copy()
    
    for col in df.columns:
        if col.startswith('dust_'):
            num = int(col.split('_')[1])
            if num < 10:
                new_col = col.replace(f"dust_{num}", f"dust_0{num}") # dust_ 뒤에 오는 숫자가 10보다 작으면 0을 붙이기. 예로 dust_9이면 dust_09로.
                df.rename(columns={col: new_col}, inplace=True)

    
    # Now divide the surface by time interval
    n_timeBetHour = int(60/minuteInterval) # n_timeBetHour: hour 사이에 몇개 만들래? n-1 개(10분 -> n_timeBetHour = 6 -> 6-1 = 5개)
    # print(n_timeBetHour)
    for hour in range(hourRange[0], hourRange[1]):

        if hour < 9: 
            dust_preT_list = list(df['dust_0' + str(hour)]) #기준이 되는 이전 시간의 dust 값: 예로 9시 ~ 10시면 9시
            dust_postT_list = list(df['dust_0' + str(hour + 1)]) #기준이 되는 이후 시간의 dust 값: 예로 9시 ~ 10시면 10시

        elif hour == 9:
            dust_preT_list = list(df['dust_0' + str(hour)]) #기준이 되는 이전 시간의 dust 값: 예로 9시 ~ 10시면 9시
            dust_postT_list = list(df['dust_' + str(hour + 1)]) #기준이 되는 이후 시간의 dust 값: 예로 9시 ~ 10시면 10시            

        else:            
            dust_preT_list = list(df['dust_' + str(hour)]) #기준이 되는 이전 시간의 dust 값: 예로 9시 ~ 10시면 9시
            dust_postT_list = list(df['dust_' + str(hour + 1)]) #기준이 되는 이후 시간의 dust 값: 예로 9시 ~ 10시면 10시

        # Step 1: 두 리스트 (dust_preT_list, dust_postT_list)에서 각 매칭되는 값을 빼서 새로운 리스트 생성
        dust_deviation_list = [post - pre for pre, post in zip(dust_preT_list, dust_postT_list)]
    #     print(dust_deviation_list[0:5])

        # Step 2: newList에 minuteInterval/60을 곱함
        dust_deviation_list = [val * (minuteInterval / 60) for val in dust_deviation_list] # dust_deviation_list은 이제 minuteInterval 해당하는 편차가 됌.
        #print("dust_deviation_list:", dust_deviation_list[0:10])  


        for t, t_Interv in enumerate(range(1, n_timeBetHour)):   # 이제 각 interval time마다 overlay를 만들 것임.
            minute = t_Interv*minuteInterval # minute은 이제 사이의 분이 됌.
            #print(minute)
            dust_deviation_list_minute = [x * (t+1) for x in dust_deviation_list] #해당 분에 해당하는 편차 값 - 10분이면 9~10시 사이 편차값 * 10/60 * 1, 20분이면 편차값 * 10/60 * 2
            globals()['dust_' + str(hour) + "_" + str(minute)] = [x + y for x, y in zip(dust_preT_list, dust_deviation_list_minute)] #preTime의 dust + 편차 값 더하기

            # 생성된 list를 원본 데이터에 합치기 
            if hour < 10:
                if minute < 10:
                    df['dust_0' + str(hour) + "_0" + str(minute)] = globals()['dust_' + str(hour) + "_" + str(minute)]
                else:
                    df['dust_0' + str(hour) + "_" + str(minute)] = globals()['dust_' + str(hour) + "_" + str(minute)]
            else:
                if minute < 10:
                    df['dust_' + str(hour) + "_0" + str(minute)] = globals()['dust_' + str(hour) + "_" + str(minute)]
                else:
                    df['dust_' + str(hour) + "_" + str(minute)] = globals()['dust_' + str(hour) + "_" + str(minute)]



    # column 정렬
    first_columns = [col for col in df.columns if col.upper() in ['FID', 'TARGET_FID', 'ID']]
    dust_columns = sorted([col for col in df.columns if col.startswith('dust')])
    date_clumns = ['date']
    last_columns = [col for col in ['geometry'] if col in df.columns]
    new_column_order = first_columns + dust_columns + date_clumns + last_columns

    df = df[new_column_order]

    return df


# # 2. Preprocessing: Overlay spatiotemporal Air pollutant surface and bicycle routes
# ## 2.1. convert bicycle OD to routes that composes of segment

# In[42]:


def process_gdf(ODdata, OD_Oid, OTime, DTime, bicyLocPoints, Loc_id, minuteInterval = 10): # minute을 넣으면 o -> d 방향으로 minute만큼 라인을 잘라 point를 생성함. point는 중간 지점이 됌.
    
    
    '''
    Divide the 1-hour based air pollution concentration into x-minute intervals
    
    Parameters
    ----------
    ODdata : Bicycle Origin-Destination table that consists of Origin and Destinaton columns. Don't have to be shp, but need key columns of ID that matches with rental location ID
    OD_Oid : A column of starting location ID. It should match with rental location ID.
    OTime : A column of O Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    DTime : A column of D Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    bicyLocPoints : A table of bicycle rental location point data. It should be the point shp file that has 'geometry' column.
    Loc_id : A key column of rental location point ID which matches with OD_Oid
    minuteInterval : time interval of the result point-route data. Need to be the same value of 'minuteInterval' parameter in minuteIntervals_surface function.
        
    
    Returns
    -------
    DataFrame
        A comma-separated values (csv) file is returned as two-dimensional
        data structure with labeled axes.

    Examples
    --------
    >>> bicy_OD_5min = process_gdf(ODdata = rae.bicy_OD_4_16_7_9, OD_Oid = 'o_cd', OTime = 'o_time', DTime = 'd_time',
                           bicyLocPoints = rae.bicy_rental_loc, Loc_id = 'sta_id', minuteInterval = 5)
    
    '''
    
    gdf = ODdata.copy()
    new_rows = []
    for index, row in tqdm(gdf.iterrows(), total = len(ODdata), desc = 'Od to point routes...'):
        # Find the starting point in bicyLocPoints that matches o_cd
        # bike point의 sta_id와 input data의 o_cd가 비슷한 곳-> 출발 지점. 이 지점을 기준으로 d 방향으로 라인을 잘라야 하기 때문.
        start_point = bicyLocPoints.loc[bicyLocPoints[Loc_id] == row[OD_Oid], 'geometry'].iloc[0] #
        
        # Find the nearest point on the line to the start point - 이 작업이 바로 origin point 위치를 찾아주는 것.
        nearest = nearest_points(row['geometry'], start_point)
        start_nearest = nearest[0]
        
        # Replace the start point of the line with the nearest point
        line = LineString([start_nearest, row['geometry'].coords[-1]])
        
        # 시간 자르기: o_time과 d_time은 minuteInterval 비율로 자른 라인에 따라 다시 설정됌.
        o_time = datetime.strptime(row[OTime], '%Y-%m-%d %H:%M:%S')
        d_time = datetime.strptime(row[DTime], '%Y-%m-%d %H:%M:%S')
        duration = (d_time - o_time).total_seconds() / 60.0 # in minutes

        line: LineString = row['geometry']
        num_segments = int(np.ceil(duration / minuteInterval))
        
        segment_durations = [minuteInterval for _ in range(num_segments - 1)]
        last_segment_duration = duration - sum(segment_durations)
        segment_durations.append(last_segment_duration)
        
        # 포인트 생성하기
        segment_points = []
        accumulated_ratio = 0
        for i, dur in enumerate(segment_durations):
            new_o_time = o_time + timedelta(minutes=sum(segment_durations[:i]))
            new_d_time = new_o_time + timedelta(minutes=dur)
            
            segment_ratio = dur / duration
            point = line.interpolate(accumulated_ratio + segment_ratio / 2, normalized=True)
            segment_points.append(point)
            
            accumulated_ratio += segment_ratio

            new_row = row.copy()
            new_row['o_time'] = new_o_time.strftime('%Y-%m-%d %H:%M:%S')
            new_row['d_time'] = new_d_time.strftime('%Y-%m-%d %H:%M:%S')
            new_row['dur_new'] = dur
            new_row['geometry'] = point  # 이 부분을 추가합니다.
            new_rows.append(new_row)
        
    # 새로운 컬럼 'dur_new'를 기존 컬럼 리스트에 추가
    new_columns = list(gdf.columns) + ['dur_new']
    new_gdf = gpd.GeoDataFrame(new_rows, columns=new_columns)

    # set same crs
    new_gdf.crs = ODdata.crs
    
    # reset index
    new_gdf.reset_index(drop = True, inplace = True)
    
    return new_gdf


# ## 2.2. Overlay spatiotemporal Air pollutant surface and bicycle routes

# In[59]:


def calculate_dust_exposure(ODdata, OTime, DTime, spatioTemporalSurface):
       

    '''
    Overlay spatiotemporal Air pollutant concentration surface and bicycle point routes
    
    Parameters
    ----------
    ODdata : Result gdf of the previous funtion (process_gdf), which have point route info
    OTime : A column of O Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    DTime : A column of D Time. Format of this should be '%Y-%m-%d %H:%M:%S' (e.g., 2023-04-16 08:13:02)
    spatioTemporalSurface : The result gdf of minuteIntervals_surface function, which has spatiotemporal air pollutant surface.
    
    
    Returns
    -------
    DataFrame
        A comma-separated values (csv) file is returned as two-dimensional
        data structure with labeled axes.
        
        
    dur_new : Duration time spending on the route (min)
    o_time_dt :	Start time 
    d_time_dt : End time
    dust_con : The instant exposure amount of air pollutant regardless of time
    dust_exp : The exposure amount of air pollutant for 'dur_new' (dur_new * 60 * dust_cos)

    Examples
    --------
    >>> exposure_5min_7_9_gdf = calculate_dust_exposure(ODdata = bicy_OD_5min, OTime = 'o_time', DTime = 'd_time', spatioTemporalSurface = dust_7_9_5min)
    
    '''
    
    # 좌표체계
    print('initialize crs...')
    ODdata = ODdata.to_crs(spatioTemporalSurface.crs)
    
    # OTime date 추출
    ODdata['date'] = ODdata[OTime].str.split(' ').str[0]  # 날짜
    ODdata['o_time_dt'] = pd.to_datetime(ODdata[OTime])
    ODdata['d_time_dt'] = pd.to_datetime(ODdata[DTime])

    print('spatial join...')
    # 공간적으로 겹치는지 확인
    joined_gdf = gpd.sjoin(ODdata, spatioTemporalSurface, predicate='within')

    # 날짜가 일치하는 행만 필터링
    joined_gdf = joined_gdf[joined_gdf['date_left'] == joined_gdf['date_right']]
    
#     display(joined_gdf)
#     display(joined_gdf)

    tqdm.pandas(desc="Processing overlay") 
    
    # 시간과 날짜가 일치하는지 확인
    def find_dust_con(row):
        # 중간 시간 계산
        o_time = row['o_time_dt']
        d_time = row['d_time_dt']
        mid_time = o_time + (d_time - o_time) / 2
        mid_hour = mid_time.hour
        mid_minute = mid_time.minute
        
        # 중간 시간에 가장 가까운 dust 컬럼 찾기
        if mid_minute == 0:
            closest_dust_col = f"dust_{mid_hour:02d}"
        else:
            closest_dust_col = f"dust_{mid_hour:02d}_{(mid_minute // 10) * 10:02d}"

                
        # "_00" 제거
        if closest_dust_col.endswith("_00"):
            closest_dust_col = closest_dust_col[:-3]
#             print("Modified:", closest_dust_col)

        # dust_con 값 찾기
        if closest_dust_col in row.index:
            return row[closest_dust_col]
        else:
            return None

    # dust_con 컬럼 생성
    joined_gdf['dust_con'] = joined_gdf.progress_apply(find_dust_con, axis=1)

    # 최종 노출량 계산
    joined_gdf['dust_exp'] = joined_gdf['dur_new'] * joined_gdf['dust_con'] * 60 ## 현재 1분 단위이기 때문에 이를 1초 단위로 바꿔줌.
    

    # 명시적으로 병합
    ODdata = ODdata.merge(joined_gdf[['dust_con', 'dust_exp']], left_index=True, right_index=True, how='left')
    
#     display(ODdata)

    # NaN 처리
#     ODdata['dust_con'].fillna(np.nan, inplace=True)
#     ODdata['dust_exp'].fillna(np.nan, inplace=True)
    


#     ODdata = ODdata[columns]
    
    return ODdata