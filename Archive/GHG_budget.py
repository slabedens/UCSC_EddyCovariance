import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

def dms_to_dd(degrees, minutes, seconds, direction):
    dd = degrees + (minutes/60) + (seconds/3600)
    if direction in ['S', 'W']:  # South and West should be negative
        dd *= -1
    return dd

### Site Data Initialization ###
#site_name = ['Porter', 'North', 'Yampah', 'Hester', 'Castroville']
site_name = ['Porter', 'North', 'Yampah', 'Hester']
#site_ID = ['EKP', 'EKN', 'EKY', 'EKH','MCP']
site_ID = ['EKP', 'EKN', 'EKY', 'EKH']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    df_site = pd.read_csv(f"{path}{site_ID[site_index]}_ECdata_flux_QC5.csv", parse_dates=['datetime'], index_col='datetime')
    df_allsites[site_name[site_index]] = df_site

### Page Configuration ###
st.set_page_config(page_title="GHG Budget")
st.title("Greenhouse Gases Budget of Elkhorn Slough Sites")
st.sidebar.markdown("v0.1")  # Markdown to format as bold

start_date = pd.to_datetime('2022-06-15')
end_date = None  # Initialize to none and update based on data


CH4_GWP=27

for site in site_name:
    selected_data = df_allsites[site].copy()
    selected_data.reset_index(inplace=True)
    selected_data['datetime'] = pd.to_datetime(selected_data['datetime'])

    selected_data['data_gCO2_m2'] = selected_data['FC_GF'] * 44 * 10**(-6) * 30 * 60 + selected_data['FCH4_GF'] * 16 * 10**(-9) * 30 * 60 * CH4_GWP

    # Ensure end_date captures the latest date in the data for proper axis scaling
    if end_date is None or selected_data['datetime'].max() > end_date:
        end_date = selected_data['datetime'].max()

    # Monthly aggregation
    monthly_data = selected_data.resample('D', on='datetime')['data_gCO2_m2'].sum().reset_index()
    monthly_data['Legend'] = monthly_data['data_gCO2_m2'].apply(lambda x: 'Carbon sink' if x < 0 else 'Carbon source')

    # Plotting the data with bar values
    fig = px.bar(
        monthly_data,
        x='datetime',
        y='data_gCO2_m2',
        title=f'Daily GHG budget at {site}',
        labels={'datetime': '', 'data_gCO2_m2': 'g-CO₂eq/m²/day'},
        text='data_gCO2_m2',
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
        yaxis_range=[-30, 30],
        xaxis=dict(
            dtick="M1",  # Tick every month
            tickformat="%b\n%Y",  # Display abbreviated month and full year
            tickfont=dict(size=25)

        ),

        legend=dict(
            font=dict(size=20)  # Adjust legend text size
        ),

        yaxis=dict(
            dtick=5, 
            showgrid=True,  # Ensure grid lines are visible
            gridcolor='lightgray',  # Set the grid line color
            gridwidth=0.5,  # Set the grid line thickness
            griddash='dot',
            tickfont=dict(size=25)

        ),
        title_x=0.36,  # Center the title
        title_y=0.9, # Center the title
        title_font=dict(
        size=30  # Adjust the size of the title
    ),  
    )
    
    st.plotly_chart(fig, use_container_width=True)


yearly_averages = []  # Store the average yearly sums per site

for site in site_name:
    selected_data = df_allsites[site].copy()
    selected_data.reset_index(inplace=True)
    selected_data['datetime'] = pd.to_datetime(selected_data['datetime'])

    selected_data['data_gCO2_m2'] = selected_data['FC_GF'] * 44 * 10**(-6) * 30 * 60 + selected_data['FCH4_GF'] * 16 * 10**(-9) * 30 * 60 * 27

    if site == "North":
        # For North, use only 2024 data
        avg_sum = selected_data[selected_data['datetime'].dt.year == 2024]['data_gCO2_m2'].sum()
    else:
        # Compute sums for each year separately
        sum_2023 = selected_data[selected_data['datetime'].dt.year == 2023]['data_gCO2_m2'].sum()
        sum_2024 = selected_data[selected_data['datetime'].dt.year == 2024]['data_gCO2_m2'].sum()

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
    title="Greenhouse Gases Budget for each site - Average of 2023 and 2024",
    text=df_yearly_avg['Average GHG Budget'].apply(lambda x: f"{x:+.0f}"),
    color='Color',
    color_discrete_map="identity",  # Use assigned colors
    labels={'Average GHG Budget': 'g-CO₂eq/m²/year'}
)

fig_yearly_avg.update_traces(textposition='outside', textfont=dict(size=15))  # Set text size on bars

fig_yearly_avg.update_layout(
    plot_bgcolor='white',
    paper_bgcolor='white',
    title_x=0.3,  # Center the title
    title_font=dict(size=25),  # Set title size to 25
    yaxis=dict(
        title="g-CO₂eq/m²/year",
        title_font=dict(size=18),  # Set y-axis title size
        tickfont=dict(size=18),  # Set y-axis tick labels size
        showgrid=True,
        gridcolor='lightgray',
        gridwidth=1,  # Set grid line width
        griddash='dot',  # **Dotted grid lines**
        range=[-2000, 50]  # **Fixed y-axis limits**
    ),
    xaxis=dict(
        title="",
        title_font=dict(size=18),  # Set x-axis title size
        tickfont=dict(size=18),  # Set x-axis tick labels size
        side="top",  # **Move x-axis labels to the top**
        title_standoff=0  # Adjust spacing
    ),
    showlegend=False,
    bargap=0.5  # **Thinner bars**
)

# Display in Streamlit
st.plotly_chart(fig_yearly_avg, use_container_width=True)