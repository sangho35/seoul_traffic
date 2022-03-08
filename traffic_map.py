import pandas as pd
import numpy as np
import re
import folium
import streamlit as st
from streamlit_folium import folium_static

raw_df = pd.read_excel('data/01월 교통량_데이터(2022).xlsx', sheet_name=1)
raw_df = raw_df.drop('요일',axis=1)
raw_df['일자'] = pd.to_datetime(raw_df['일자'], format='%Y%m%d')

traffic_df = pd.melt(raw_df, id_vars=['일자','지점명','지점번호','방향','구분'],var_name = ['hour'], value_name ='traffic')
traffic_df['weekday'] = traffic_df['일자'].dt.weekday
traffic_df['is_weekend'] = traffic_df['weekday'] // 5
traffic_df['traffic'] = traffic_df['traffic'].fillna(0)

traffic_final = traffic_df.groupby(['is_weekend','hour','지점번호','지점명'])[['traffic']].sum().reset_index()
traffic_final['hour'] = traffic_final['hour'].apply(lambda x : re.sub(r'[^0-9]', '', x)).astype('int')
# traffic_final =traffic_df.groupby(['is_weekend','지점번호','지점명'])[['traffic']].sum().reset_index()
traffic_final['is_weekend'] = traffic_final['is_weekend'].replace(1, '주말')
traffic_final['is_weekend'] = traffic_final['is_weekend'].replace(0, '주중')

meta_df = pd.read_excel('data/01월 교통량_데이터(2022).xlsx', sheet_name=2).dropna(subset=['지점명칭'])
# meta_df = meta_df.rename(columns = {'지점명칭' : '지점명'})

col = ['지점번호','지점명칭','위도','경도']

meta_df = meta_df[col]

traffic_map = pd.merge(traffic_final, meta_df, how='left' ,on = ['지점번호'])
traffic_map = traffic_map.drop('지점명칭', axis=1)

st.set_page_config(layout='wide')

selected_hour = st.slider('Hour', 0,23)
@st.cache
def load_data(hour):
    data = traffic_map[traffic_map['hour'] == hour]
    data = data.reset_index().drop('index', axis = 1)
    return data
hour_traffic = load_data(selected_hour)

group_list = list(hour_traffic['is_weekend'].unique())

# st.dataframe(hour_traffic)
m = folium.Map(location=[37.502088, 127.024615], zoom_start=12)

for group in group_list:
    traffic_group = hour_traffic[hour_traffic['is_weekend'] == group]
    traffic_group = traffic_group.reset_index().drop('index', axis=1)

    sub_group = folium.FeatureGroup(name=str(group), show=False)
    m.add_child(sub_group)

    for i in range(len(traffic_group)):
        popup = folium.Popup(str(traffic_group['지점명'][i]) + ', traffic:' + str(int(traffic_group['traffic'][i])),
                             max_width='500')

        folium.CircleMarker(
            location=[traffic_group['위도'][i], traffic_group['경도'][i]],
            popup=popup,
            color='red',
            fill = True,
            fill_color = 'blue',
            opacity = 0.5,
            fill_opacity = 0.3,
            radius=traffic_group['traffic'][i] / 4000
        ).add_to(sub_group)

folium.LayerControl(collapsed=False).add_to(m)
folium_static(m, width=1600, height=950)



