import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from streamlit_folium import st_folium

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


# --- PAGE TITLE --------------------------------------------------------------------------------------------------------

st.title("UCSC Greenhouse Gases Monitoring Platform")         

# --- SIDEBAR --------------------------------------------------------------------
with st.sidebar:
    st.header("Data and Time Settings")

    data_type = st.selectbox("Select Gas", ["GHG", "CH4", "CO2"])
    time_type = st.selectbox("Select time aggregation", ["Daily", "Monthly", "Yearly"])

    use_gapfilled = st.toggle("Use gap-filled data", value=True)
    CO2_COL  = "FC_GF"   if use_gapfilled else "FC"
    CH4_COL  = "FCH4_GF" if use_gapfilled else "FCH4"
    version_label = "(gap-filled)" if use_gapfilled else "(no gap-fill)"

    st.divider()
    st.header("Gap-Filling ANN model R²")

    perf = pd.DataFrame(
        {
            "Site": ["Castroville", "Hester", "North", "Porter", "Yampah"],
            "CO2 Flux": ["0.92", "0.48", "0.32", "0.81", "0.81"],
            "CH4 Flux": ["0.58", "0.37", "0.61", "0.11", "0.12"],
        }
    )

    st.sidebar.dataframe(
        perf,
        hide_index=True,
    )
    
    st.caption("")
    st.caption("v1.2")


# --- CONTAINER 1 MAP --------------------------------------------------------------------------------------------------------
with st.container():

    # Split layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Eddy Covariance Site Map")

        m = folium.Map(
            location=[36.82, -121.76],
            zoom_start=12,
            width="100%",      # let Leaflet fill the container
            height=400
        )

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

        # … add markers, layer control, etc.
        folium.LayerControl().add_to(m)

        # this makes it expand to the column width
        st_folium(m, height=400, use_container_width=True)


# --- CONTAINER 1 CUMUL GRAPH ----------------------------------------------------
with col2:
    st.subheader(f"Cumulative {data_type} Flux  {version_label}")

    CH4_GWP = 27
    df_monthly_all = []

    for site in site_name:
        df = df_allsites[site]

        if data_type == 'CO2':
            data_30min = df[CO2_COL] * 12.0107e-6 * 30 * 60
            ylabel = 'Cumulative FC [gC/m²]'
            dtick_type = 200

        elif data_type == 'CH4':
            data_30min = df[CH4_COL] * 12.0107e-9 * 30 * 60
            ylabel = 'Cumulative FCH4 [gC/m²]'
            dtick_type = 2

        else:
            data_30min = (
                df[CO2_COL] * 44e-6 * 30 * 60 +               # CO2 → g CO2
                df[CH4_COL] * 16e-9 * 30 * 60 * CH4_GWP       # CH4 → g CO2eq
            )
            ylabel = 'Cumulative GHG [g-CO₂eq/m²]'
            dtick_type = 500

        # --- key change: keep NaN for months with no data ---
        monthly_sum = data_30min.resample('D').sum(min_count=1)   # empty month → NaN (not 0)

        # cumulative only over valid months; keep NaN where no data so the line breaks
        monthly_cumsum = monthly_sum.copy()
        monthly_cumsum.loc[monthly_sum.notna()] = monthly_sum.dropna().cumsum().round(2).values

        df_monthly_site = pd.DataFrame({
            'Year': monthly_cumsum.index,
            ylabel: monthly_cumsum.values,
            'Site': site
        })
        df_monthly_all.append(df_monthly_site)

    df_plot = pd.concat(df_monthly_all, ignore_index=True)

    # Create plot
    fig = px.line(
        df_plot,
        x='Year',
        y=ylabel,
        color='Site',
        color_discrete_sequence=uc_colors_hex
    )

    # do not connect across gaps
    fig.update_traces(connectgaps=False)

    # Add thick zero line
    fig.add_hline(y=0, line_width=2, line_color='#EEEEEE', line_dash='solid', layer="below")

    # Style layout
    fig.update_layout(
        height=410,
        autosize=False,
        margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(tick0=0, dtick=dtick_type, showgrid=True, gridcolor='#EEEEEE', gridwidth=1),
        xaxis=dict(showgrid=True, gridcolor='#EEEEEE', gridwidth=1),
        legend=dict(
            orientation="h",
            x=-0.01,
            y=10.1,
            xanchor="left",
            yanchor="top",
            itemsizing="constant",
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
        df = df_allsites[site].reset_index()
        df['datetime'] = pd.to_datetime(df['datetime'])

        if data_type == 'CO2':
            df['data_g_m2'] = df[CO2_COL] * 12.0107e-6 * 30 * 60
            yaxis_range_type = [-11, 9]; dtick_type = 2; unit = 'gC/m²'

        elif data_type == 'CH4':
            df['data_g_m2'] = df[CH4_COL] * 12.0107e-9 * 30 * 60
            yaxis_range_type = [-0.19, 0.19]; dtick_type = 0.05; unit = 'gC/m²'

        else:
            CH4_GWP = 27
            df['data_g_m2'] = (df[CO2_COL] * 44e-6 * 30 * 60 + df[CH4_COL] * 16e-9 * 30 * 60 * CH4_GWP)
            yaxis_range_type = [-41, 41]; dtick_type = 10; unit = 'g-CO₂eq/m²'

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
            title=f'{time_type} {data_type} balance at {site} {version_label}',
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
            title_x=0.35,  # Center the title
            title_y=0.85, # Center the title
            title_font=dict(
            size=15  # Adjust the size of the title
            )   
        )
        st.plotly_chart(fig, use_container_width=True)



    