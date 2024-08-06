import streamlit as st
import pandas as pd
import plotly.express as px

# Create your dictionary of DataFrames
site_name = ['Castroville', 'Hester', 'North', 'Porter', 'Yampah']
site_ID = ['MCP', 'EKH', 'EKN', 'EKP', 'EKY']

def create_df(site_index, path, file_ext):
    file = path + site_ID[site_index] + file_ext
    df_fluxnet = pd.read_csv(file, sep=',')
    df_fluxnet['datetime'] = pd.to_datetime(df_fluxnet['TIMESTAMP_END'], format='%Y%m%d%H%M')
    df_fluxnet.set_index('datetime', inplace=True)
    df_fluxnet.sort_index(inplace=True)
    return df_fluxnet

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"/Users/sylvainlabedens/Library/CloudStorage/GoogleDrive-slabeden@ucsc.edu/Shared drives/Paytan Eddy Covariance/EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    file_ext_INPUT = "_ECdata_fluxnet_QC0.csv"
    df_site = create_df(site_index, path, file_ext_INPUT)
    df_allsites[site_name[site_index]] = df_site

# Streamlit App
st.title('Eddy Covariance Data Visualization')

# Create Streamlit widgets
site_selector = st.sidebar.selectbox('Select Site', list(df_allsites.keys()))
date_range = st.sidebar.date_input(
    'Select Date Range',
    value=[df_allsites[site_selector].index.min().date(), df_allsites[site_selector].index.max().date()],
    min_value=df_allsites[site_selector].index.min().date(),
    max_value=df_allsites[site_selector].index.max().date()
)

# Filter data based on selection
df_selected = df_allsites[site_selector]
filtered_df = df_selected[(df_selected.index.date >= date_range[0]) & (df_selected.index.date <= date_range[1])]

# Create the Plotly graph
fig = px.line(
    filtered_df,
    x=filtered_df.index,
    y='FC',
    title=f'FC over Time for {site_selector}'
)

# Display the graph in the Streamlit app
st.plotly_chart(fig)
