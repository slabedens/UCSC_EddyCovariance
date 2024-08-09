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
    df_fluxnet = pd.read_csv(file, sep=',', low_memory=False)
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
site_name = ['Castroville', 'Hester', 'North', 'Porter', 'Yampah']
site_ID = ['MCP', 'EKH', 'EKN', 'EKP', 'EKY']
df_allsites = {}
for site_index in range(len(site_name)):
    path = f"/Users/sylvainlabedens/Library/CloudStorage/GoogleDrive-slabeden@ucsc.edu/Shared drives/Paytan Eddy Covariance/EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    file_ext_INPUT = "_ECdata_fluxnet_QC5.csv"
    df_site = create_df(site_index, path, file_ext_INPUT)
    df_allsites[site_name[site_index]] = df_site

st.title("Research View")

### Site Selection ###
selected_site = st.selectbox("Select a Site", options=site_name)

### Fetch and Display Data ###
selected_data = df_allsites[selected_site].reset_index()
fig = px.line(selected_data, x='datetime', y='FC', title=f'Plotly: Flux of Carbon at {selected_site}',
              labels={'datetime': 'Date Time', 'FC': 'Flux of Carbon (FC)'})
fig.update_xaxes(rangeslider_visible=True)
fig.update_layout(hovermode="x")
st.plotly_chart(fig)