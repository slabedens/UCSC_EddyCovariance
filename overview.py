import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
from datetime import datetime

def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + (minutes/60) + (seconds/3600)
    if direction in ['S', 'W']:  # South and West should be negative
        dd *= -1
    return dd

### Site Data Initialization ###
site_name = ['Porter', 'North', 'Yampah', 'Hester', 'Castroville']
#site_name = ['Porter', 'North', 'Yampah', 'Hester']
site_ID = ['EKP', 'EKN', 'EKY', 'EKH','MCP']
#site_ID = ['EKP', 'EKN', 'EKY', 'EKH']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    df_site = pd.read_csv(f"{path}{site_ID[site_index]}_ECdata_flux_QC5.csv", parse_dates=['datetime'], index_col='datetime')
    df_allsites[site_name[site_index]] = df_site

### Coordinate Conversion ###
sites_dms = {
 #   "Castroville": {"lat": (36, 46, 58.80, 'N'), "lon": (121, 46, 8.40, 'W')},
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
st.sidebar.markdown("v0.1")  # Markdown to format as bold


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
        popup=f"{site}: {np.round(df_allsites[site]['FC_GF'].sum(), 2)} gC",
        icon=folium.Icon(icon='flag', prefix='fa', color='blue')  # Using Font Awesome icon
    ).add_to(m)

folium.LayerControl().add_to(m)
folium_static(m, width=700, height=500)  # Adjust these values based on your layout needs

# User selects data type
data_type = st.selectbox('Select Data Variable', ['CO2', 'CH4'])

start_date = pd.to_datetime('2022-06-01')
end_date = None  # Initialize to none and update based on data

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
    monthly_data = selected_data.resample('D', on='datetime')['data_gC_m2'].sum().reset_index()
    monthly_data['Legend'] = monthly_data['data_gC_m2'].apply(lambda x: 'Carbon sink' if x < 0 else 'Carbon source')

    # Plotting the data with bar values
    fig = px.bar(
        monthly_data,
        x='datetime',
        y='data_gC_m2',
        title=f'Daily {data_type} balance at {site}',
        labels={'datetime': '', 'data_gC_m2': 'gC/m²/day'},
        text='data_gC_m2',
        color='Legend',
        color_discrete_map={"Carbon source": "#1295D8", "Carbon sink": "#FDB515"}
    )
    #fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')  # Display text outside bars
    fig.update_layout(
        plot_bgcolor='white',  # Set plot background to white
        paper_bgcolor='white',  # Set overall figure background to white
        bargap=0.1,  # Adjust space between bars (lower value = wider bars)
        xaxis_tickformat='%Y-%m',
        xaxis_range=['2023-01-01', '2024-12-31'],
        yaxis_range=[-25, 10]if data_type == 'CO2' else [-0.19,0.19] ,
        xaxis=dict(
            dtick="M1",  # Tick every month
            tickformat="%b\n%Y",  # Display abbreviated month and full year
            tickfont=dict(size=25)
        ),
        legend=dict(
            font=dict(size=20)  # Adjust legend text size
        ),

        yaxis=dict(
            dtick=2 if data_type == 'CO2' else 0.05, 
            showgrid=True,  # Ensure grid lines are visible
            gridcolor='lightgray',  # Set the grid line color
            gridwidth=0.5,  # Set the grid line thickness
            griddash='dot',
            tickfont=dict(size=25)
        ),
        title_x=0.4,  # Center the title
        title_y=0.9, # Center the title
        title_font=dict(
        size=30  # Adjust the size of the title
        )   
    )
    st.plotly_chart(fig, use_container_width=True)



yearly_averages = []  # Store the average yearly sums per site

for site in site_name:
    selected_data = df_allsites[site].copy()
    selected_data.reset_index(inplace=True)
    selected_data['datetime'] = pd.to_datetime(selected_data['datetime'])

    selected_data['data_gC_m2'] = selected_data['FC_GF'] * 12.0107 * 10**(-6) * 30 * 60

    if site == "North":
        # For North, use only 2024 data
        avg_sum = selected_data[selected_data['datetime'].dt.year == 2024]['data_gC_m2'].sum()
    else:
        # Compute sums for each year separately
        sum_2023 = selected_data[selected_data['datetime'].dt.year == 2023]['data_gC_m2'].sum()
        sum_2024 = selected_data[selected_data['datetime'].dt.year == 2024]['data_gC_m2'].sum()

        # Compute the average of the sums
        avg_sum = (sum_2023 + sum_2024) / 2

    yearly_averages.append({'Site': site, 'Average GHG Budget': avg_sum})

# Create a DataFrame for the yearly summary
df_yearly_avg = pd.DataFrame(yearly_averages)

# Define colors: carbon source (blue), carbon sink (orange)
df_yearly_avg['Color'] = df_yearly_avg['Average GHG Budget'].apply(lambda x: "#1295D8" if x > 0 else "#FDB515")

# Create bar plot for yearly averages
fig_yearly_avg = px.bar(
    df_yearly_avg,
    x='Site',
    y='Average GHG Budget',
    title="Yearly NEE Budget for each site - Average of 2023 and 2024",
    text=df_yearly_avg['Average GHG Budget'].apply(lambda x: f"{x:+.0f}"),
    color='Color',
    color_discrete_map="identity",  # Use assigned colors
    labels={'Yearly NEE Budget': 'gC/m²/year'}
)

fig_yearly_avg.update_traces(textposition='outside')
fig_yearly_avg.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    title_x=0.4,  # Center the title
    yaxis=dict(
        title="gC/m²/year",
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1,   # Set grid line width
        griddash='dot',  # **Dotted grid lines**
        range=[-1600, 50]  # **Fixed y-axis limits**
    ),
    xaxis=dict(
        title="",
        #showgrid=True,
        #gridcolor='lightgray',
        #gridwidth=1,
        #griddash='dot',
        side="top",  # **Move x-axis labels to the top**
        title_standoff=0  # Adjust spacing
    ),
    showlegend=False,
    bargap=0.5  # **Thinner bars**
)

# Display in Streamlit
st.plotly_chart(fig_yearly_avg, use_container_width=True)