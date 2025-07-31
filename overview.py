import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + (minutes/60) + (seconds/3600)
    if direction in ['S', 'W']:  # South and West should be negative
        dd *= -1
    return dd

### Site Data Initialization ###
site_name = ['Castroville', 'Hester', 'North', 'Porter', 'Yampah']
site_ID = ['MCP', 'EKH', 'EKN', 'EKP','EKY']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    df_site = pd.read_csv(f"{path}{site_ID[site_index]}_ECdata_QC9.csv", parse_dates=['datetime'], index_col='datetime')
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
st.title("UCSC Carbon Monitoring Platform")
st.sidebar.markdown("v0.1")

# UCSC logo
logo_path = "paytan_lab_logo.png"
st.logo(logo_path)

### Create and display the Folium map with UC brand colors ###
m = folium.Map(location=[36.82, -121.76], zoom_start=12)

# Esri satellite basemap
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri',
    name='Esri World Imagery',
    overlay=False,
    control=True
).add_to(m)

# Use UC brand hex colors
uc_colors_hex = ['#005581', '#72CDF4', '#FFB511', '#FFE552', '#7C7E7F']

# Use CircleMarker for color control
for i, site in enumerate(site_name):
    coords = sites_dd[site]
    folium.CircleMarker(
        location=[coords['lat'], coords['lon']],
        radius=8,
        popup=f"{site}",
        color='black',
        fill=True,
        fill_color=uc_colors_hex[i],
        fill_opacity=0.9
    ).add_to(m)

folium.LayerControl().add_to(m)

# Split layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Eddy Covariance Site Map")
    folium_static(m, width=400, height=300)

with col2:
    st.subheader("Cumulative Sum of FC")

    df_fc_monthly = []
    for site in site_name:
        df = df_allsites[site]
        df['FC_GF_gC_m2'] = df['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60
        monthly_sum = df['FC_GF_gC_m2'].resample('M').sum()
        cumulative = monthly_sum.cumsum()
        temp = pd.DataFrame({
            'Year': cumulative.index,
            'Cumulative FC [gC/m²]': cumulative.values,
            'Site': site
        })
        df_fc_monthly.append(temp)

    df_fc_plot = pd.concat(df_fc_monthly)




    # Create plot
    fig = px.line(
        df_fc_plot,
        x='Year',
        y='Cumulative FC [gC/m²]',
        color='Site',
        color_discrete_sequence=uc_colors_hex
    )

    # Add thick zero line
    fig.add_hline(
        y=0,
        line_width=2,
        line_color='#EEEEEE',
        line_dash='solid',
        layer="below"
    )

    # Style layout
    fig.update_layout(
        height=310,
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(
            tick0=0,
            dtick=100,
            showgrid=True,
            gridcolor='#EEEEEE',
            gridwidth=1
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='#EEEEEE',
            gridwidth=1
        ),
        legend=dict(
            x=0,
            y=0,
            xanchor='left',
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.7)',
            bordercolor='lightgray',
            borderwidth=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)


    