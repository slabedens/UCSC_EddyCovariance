import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
from datetime import datetime

### Functions ###
def create_df(site_index, path, file_ext):
    file = path + site_ID[site_index] + file_ext
    df_fluxnet = pd.read_csv(file, sep=',')
    df_fluxnet['datetime'] = pd.to_datetime(df_fluxnet['TIMESTAMP_END'], format='%Y%m%d%H%M')
    df_fluxnet.set_index('datetime', inplace=True)
    df_fluxnet.sort_index(inplace=True)
    return df_fluxnet

def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + (minutes/60) + (seconds/3600)
    if direction in ['S', 'W']:  # South and West should be negative
        dd *= -1
    return dd

### Site Data Initialization ###
site_name = ['Porter', 'North', 'Yampah', 'Hester', 'Castroville']
site_ID = ['EKP', 'EKN', 'EKY', 'EKH', 'MCP']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    file_ext_INPUT = "_ECdata_fluxnet_QC5.csv"
    df_site = create_df(site_index, path, file_ext_INPUT)
    df_allsites[site_name[site_index]] = df_site

### Coordinate Conversion ###
sites_dms = {
    "Castroville": {"lat": (36, 46, 58.80, 'N'), "lon": (121, 46, 8.40, 'W')},
    "Yampah": {"lat": (36, 48, 37.80, 'N'), "lon": (121, 44, 55.32, 'W')},
    "Porter": {"lat": (36, 51, 20.88, 'N'), "lon": (121, 44, 55.68, 'W')},
    "North": {"lat": (36, 50, 8.52, 'N'), "lon": (121, 43, 58.08, 'W')},
    "Hester": {"lat": (36, 48, 33.84, 'N'), "lon": (121, 45, 8.28, 'W')}
}
sites_dd = {site: {"lat": dms_to_dd(*coords["lat"]), "lon": dms_to_dd(*coords["lon"])}
            for site, coords in sites_dms.items()}

### Page Configuration ###
st.set_page_config(page_title="Sites Overview", page_icon="🌍")
st.title("UCSC Paytan Lab Sites Overview")

# UCSC logo
logo_path = "paytan_lab_logo.png"
st.logo(logo_path)

### Create and display the Folium map with Esri World Imagery ###
m = folium.Map(location=[36.82, -121.76], zoom_start=12)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri World Imagery',
    overlay=False,
    control=True
).add_to(m)

for site, coords in sites_dd.items():
    folium.Marker(
        location=[coords['lat'], coords['lon']],
        popup=f"{site}: {np.round(df_allsites[site]['FC'].sum(), 2)} gC",
        icon=folium.Icon(icon='flag', prefix='fa', color='blue')  # Using Font Awesome icon
    ).add_to(m)

folium.LayerControl().add_to(m)
folium_static(m, width=700, height=500)  # Adjust these values based on your layout needs


# User selects data type
data_type = st.selectbox('Select Data Variable', ['CO2', 'CH4'])

start_date = pd.to_datetime('2022-08-01')
end_date = None  # Initialize to none and update based on data

for site in site_name:
    selected_data = df_allsites[site].copy()
    selected_data.reset_index(inplace=True)
    selected_data['datetime'] = pd.to_datetime(selected_data['datetime'])

    if data_type == 'CO2':
        selected_data['data_gC_m2'] = selected_data['FC'] * 12.0107 * 10**(-6) * 30 * 60
    else:
        selected_data['data_gC_m2'] = selected_data['FCH4'] * 12.0107 * 10**(-9) * 30 * 60

    # Ensure end_date captures the latest date in the data for proper axis scaling
    if end_date is None or selected_data['datetime'].max() > end_date:
        end_date = selected_data['datetime'].max()

    # Monthly aggregation
    monthly_data = selected_data.resample('M', on='datetime')['data_gC_m2'].sum().reset_index()
    monthly_data['Legend'] = monthly_data['data_gC_m2'].apply(lambda x: 'Carbon sink' if x < 0 else 'Carbon source')

    # Plotting the data with bar values
    fig = px.bar(
        monthly_data,
        x='datetime',
        y='data_gC_m2',
        title=f'Monthly {data_type} balance at {site}',
        labels={'datetime': 'Month', 'data_gC_m2': 'gC/m²'},
        text='data_gC_m2',
        color='Legend',
        color_discrete_map={"Carbon source": "#003262", "Carbon sink": "#FDB515"}
    )
    fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')  # Display text outside bars
    fig.update_layout(
        xaxis_tickformat='%Y-%m',
        xaxis_range=[start_date, end_date],
        yaxis_range=[-200, 200] if data_type == 'CO2' else [-1, 1],
        xaxis=dict(
            dtick="M1",  # Tick every three months
            tickformat="%b\n%Y"  # Display abbreviated month and full year
        )
    )
    st.plotly_chart(fig, use_container_width=True)