import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- DATA DOWNLOAD --------------------------------------------------------------------------------------------------------

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
def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + (minutes/60) + (seconds/3600)
    if direction in ['S', 'W']:  # South and West should be negative
        dd *= -1
    return dd

sites_dd = {site: {"lat": dms_to_dd(*coords["lat"]), "lon": dms_to_dd(*coords["lon"])}
            for site, coords in sites_dms.items()}


# --- PAGE CONFIGURATION --------------------------------------------------------------------------------------------------------

st.set_page_config(page_title="Sites Overview", page_icon="🌍")
st.title("UCSC Greenhouse Gases Monitoring Platform")
logo_path = "paytan_lab_logo.png"
st.logo(logo_path)            


# --- SIDEBAR --------------------------------------------------------------------------------------------------------

data_type = st.sidebar.selectbox('Select Gas', ['GHG', 'CH4','CO2']) 
time_type = st.sidebar.selectbox('Select time aggregation', ['Daily', 'Monthly','Yearly']) 
st.sidebar.markdown("v1.1")


# --- CONTAINER 1 MAP --------------------------------------------------------------------------------------------------------
with st.container():

    # Split layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Eddy Covariance Site Map")

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

        folium_static(m, width=None, height=400)


# --- CONTAINER 1 CUMUL GRAPH --------------------------------------------------------------------------------------------------------
    
    with col2:
        st.subheader(f"Cumulative {data_type} Flux")
        
        CH4_GWP=27
        df_monthly_all = []

        for site in site_name:
            df = df_allsites[site]

            if data_type == 'CO2':
                data_30min = df['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60
                ylabel = 'Cumulative FC [gC/m²]'
                dtick_type = 200

            elif data_type == 'CH4':
                data_30min = df['FCH4_GF'] * 12.0107 * 10**(-9) * 30 * 60
                ylabel = 'Cumulative FCH4 [gC/m²]'
                dtick_type = 2

            else :
                data_30min = df['FC_GF'] * 44 * 10**(-6) * 30 * 60 + df['FCH4_GF'] * 16 * 10**(-9) * 30 * 60 * CH4_GWP
                ylabel = 'Cumulative GHG [g-CO₂eq/m²]'
                dtick_type = 500

            monthly_cumsum = data_30min.resample('M').sum().cumsum().round(2)
            df_monthly_site = pd.DataFrame({
                'Year': monthly_cumsum.index,
                ylabel: monthly_cumsum.values,
                'Site': site
            })
            df_monthly_all.append(df_monthly_site)

        df_plot = pd.concat(df_monthly_all)

        # Create plot
        fig = px.line(
            df_plot,
            x='Year',
            y=ylabel,
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
            height=410,
            autosize=False,
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis=dict(
                tick0=0,
                dtick=dtick_type,
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
                orientation="h",        # horizontal
                x=-0.01,                  # centré horizontalement
                y=10.1,                 # en dessous de l'axe (tu peux ajuster, ex -0.1 ou -0.25)
                xanchor="left",
                yanchor="top",          # y est la position de son bord supérieur
                #bgcolor="rgba(255,255,255,0.7)",
                itemsizing="constant",
                #itemwidth=30
                #bordercolor="lightgray",
                #borderwidth=0.8
            )
        )

        st.plotly_chart(fig, use_container_width=True)

# --- CONTAINER 2 --------------------------------------------------------------------------------------------------------

with st.container():

    #st.subheader(f"")
    #st.subheader(f"Daily {data_type} balance over time for all the sites")

    start_date = pd.to_datetime('2022-06-01')
    end_date = pd.Timestamp.today() 

    for site in site_name:
        df = df_allsites[site]
        df.reset_index(inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'])


        if data_type == 'CO2':
            df['data_g_m2'] = df['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60
            yaxis_range_type = [-11, 9]
            dtick_type = 2
            unit = 'gC/m²'
        elif data_type == 'CH4':
            df['data_g_m2'] = df['FCH4_GF'] * 12.0107 * 10**(-9) * 30 * 60
            yaxis_range_type = [-0.19,0.19]
            dtick_type = 0.05
            unit = 'gC/m²'
        else :
            df['data_g_m2'] = df['FC_GF'] * 44 * 10**(-6) * 30 * 60 + df['FCH4_GF'] * 16 * 10**(-9) * 30 * 60 * CH4_GWP
            yaxis_range_type = [-41,41]
            dtick_type = 10
            unit = 'g-CO₂eq/m²'

        # Select time aggregation
        if time_type == 'Monthly':
            data_agg = df.resample('M', on='datetime')['data_g_m2'].sum().round(2).reset_index()
            yaxis_range_type = [x * 25 for x in yaxis_range_type] 
            dtick_type = dtick_type *20
            freq = 'month'
        elif time_type == 'Yearly':
            data_agg = df.resample('Y', on='datetime')['data_g_m2'].sum().round(2).reset_index().assign(
          datetime=lambda d: d['datetime'].dt.to_period('Y').dt.to_timestamp() + pd.DateOffset(months=6)
      )


            yaxis_range_type = [x * 70 for x in yaxis_range_type] 
            dtick_type = dtick_type *50
            freq = 'year'
        else :
            data_agg = df.resample('D', on='datetime')['data_g_m2'].sum().round(3).reset_index()
            yaxis_range_type = [x * 1 for x in yaxis_range_type] 
            freq = 'day'

        data_agg['Legend'] = data_agg['data_g_m2'].apply(lambda x: 'Carbon sink' if x < 0 else 'Carbon source')
        ylabel_agg = f"{unit}/{freq}"

        # Plotting the data with bar values
        fig = px.bar(
            data_agg,
            x='datetime',
            y='data_g_m2',
            title=f'{time_type} {data_type} balance at {site}',
            labels={'data_g_m2': ylabel_agg},
            #text=np.round(data_agg['data_g_m2'],2),
            color='Legend',
            color_discrete_map={"Carbon source": "#1295D8", "Carbon sink": "#FFB511"}
        )

        # Forcer position selon le signe : toujours 'outside'
        #textpos = ["outside" for _ in data_agg['data_g_m2']]
        #fig.update_traces(
        #    texttemplate="<b>%{text:.2f}</b>",
        #    textposition="outside",
        #    cliponaxis=False
        #)
        #fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')  # Display text outside bars
        fig.update_layout(
            plot_bgcolor='white',  # Set plot background to white
            paper_bgcolor='white',  # Set overall figure background to white
            bargap=0.1,  # Adjust space between bars (lower value = wider bars)
            xaxis_tickformat='%Y-%m',
            xaxis_range=[start_date, end_date],
            yaxis_range=yaxis_range_type ,
            xaxis=dict(
                title="",
                dtick="M1",  # Tick every month
                tickformat="%b\n%Y",  # Display abbreviated month and full year
                tickfont=dict(size=10)
            ),
            legend=dict(
                font=dict(size=10)  # Adjust legend text size
            ),

            yaxis=dict(
                dtick=dtick_type, 
                showgrid=True,  # Ensure grid lines are visible
                gridcolor='lightgray',  # Set the grid line color
                gridwidth=0.5,  # Set the grid line thickness
                griddash='dot',
                tickfont=dict(size=10)
            ),
            title_x=0.0,  # Center the title
            title_y=0.85, # Center the title
            title_font=dict(
            size=15  # Adjust the size of the title
            )   
        )
        st.plotly_chart(fig, use_container_width=True)



    