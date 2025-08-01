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
st.sidebar.markdown("v1.0")

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

# --- CONTAINER 1 --------------------------------------------------------------------------------------------------------
with st.container():

    # Split layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Eddy Covariance Site Map")
        folium_static(m, width=None, height=300)

    with col2:
        st.subheader("Cumulative Sum of NEE")

        df_fc_monthly = []
        for site in site_name:
            df = df_allsites[site]
            df['FC_GF_gC_m2'] = df['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60
            monthly_sum = df['FC_GF_gC_m2'].resample('M').sum()
            cumulative = monthly_sum.cumsum()
            temp = pd.DataFrame({
                'Year': cumulative.index,
                'Cumulative NEE [gC/m²]': cumulative.values,
                'Site': site
            })
            df_fc_monthly.append(temp)

        df_fc_plot = pd.concat(df_fc_monthly)

        # Create plot
        fig = px.line(
            df_fc_plot,
            x='Year',
            y='Cumulative NEE [gC/m²]',
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

# --- CONTAINER 2 --------------------------------------------------------------------------------------------------------

with st.container():

    st.subheader(f"")
    st.subheader(f"Daily CO2 and CH4 fluxes balance over time for all the sites")

    # User selects data type
    data_type = st.selectbox('Select Gas fluxes', ['CO2', 'CH4'])    

    start_date = pd.to_datetime('2022-06-01')
    end_date = pd.Timestamp.today() 

    for site in site_name:
        selected_data = df_allsites[site].copy()
        selected_data.reset_index(inplace=True)
        selected_data['datetime'] = pd.to_datetime(selected_data['datetime'])

        if data_type == 'CO2':
            selected_data['data_gC_m2'] = selected_data['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60
            dtick=2

        else:
            selected_data['data_gC_m2'] = selected_data['FCH4_GF'] * 12.0107 * 10**(-9) * 30 * 60
            dtick=2 

        # Ensure end_date captures the latest date in the data for proper axis scaling
        if end_date is None or selected_data['datetime'].max() > end_date:
            end_date = selected_data['datetime'].max()

        # Monthly aggregation
        daily_data = selected_data.resample('D', on='datetime')['data_gC_m2'].sum().reset_index()
        daily_data['Legend'] = daily_data['data_gC_m2'].apply(lambda x: 'Carbon sink' if x < 0 else 'Carbon source')

        # Plotting the data with bar values
        fig = px.bar(
            daily_data,
            x='datetime',
            y='data_gC_m2',
            title=f'Daily {data_type} balance at {site}',
            labels={'datetime': '', 'data_gC_m2': 'gC/m²/day'},
            text='data_gC_m2',
            color='Legend',
            color_discrete_map={"Carbon source": "#1295D8", "Carbon sink": "#FFB511"}
        )
        #fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')  # Display text outside bars
        fig.update_layout(
            plot_bgcolor='white',  # Set plot background to white
            paper_bgcolor='white',  # Set overall figure background to white
            bargap=0.1,  # Adjust space between bars (lower value = wider bars)
            xaxis_tickformat='%Y-%m',
            xaxis_range=[start_date, end_date],
            yaxis_range=[-11, 9]if data_type == 'CO2' else [-0.19,0.19] ,
            xaxis=dict(
                dtick="M1",  # Tick every month
                tickformat="%b\n%Y",  # Display abbreviated month and full year
                tickfont=dict(size=10)
            ),
            legend=dict(
                font=dict(size=10)  # Adjust legend text size
            ),

            yaxis=dict(
                dtick=2 if data_type == 'CO2' else 0.05, 
                showgrid=True,  # Ensure grid lines are visible
                gridcolor='lightgray',  # Set the grid line color
                gridwidth=0.5,  # Set the grid line thickness
                griddash='dot',
                tickfont=dict(size=10)
            ),
            #title_x=0.3,  # Center the title
            title_y=0.85, # Center the title
            title_font=dict(
            size=15  # Adjust the size of the title
            )   
        )
        st.plotly_chart(fig, use_container_width=True)



    