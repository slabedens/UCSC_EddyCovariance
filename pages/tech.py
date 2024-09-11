import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import plotly.express as px
from datetime import datetime

### Functions ###
@st.cache_resource
def create_df(site_index, path, file_ext):
    file = path + site_ID[site_index] + file_ext
    df_fluxnet = pd.read_csv(file, sep=',', low_memory=False)
    df_fluxnet['datetime'] = pd.to_datetime(df_fluxnet['TIMESTAMP_END'], format='%Y%m%d%H%M')
    df_fluxnet.set_index('datetime', inplace=True)
    df_fluxnet.sort_index(inplace=True)
    return df_fluxnet

### Site Data Initialization ###
site_name = ['Porter', 'North', 'Yampah', 'Hester', 'Castroville']
site_ID = ['EKP', 'EKN', 'EKY', 'EKH', 'MCP']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    file_ext_INPUT = "_ECdata_fluxnet_QC0.csv"
    df_site = create_df(site_index, path, file_ext_INPUT)
    df_allsites[site_name[site_index]] = df_site

# Page configuration
st.title("Technician view")
st.sidebar.markdown("v0.1")  # Markdown to format as bold
logo_path = "paytan_lab_logo.png"
#st.sidebar.image(logo_path)

# Sidebar - Site and Date Range Selection
selected_site = st.sidebar.selectbox('Select Site', site_name)
site_data = df_allsites[selected_site]
min_date, max_date = site_data.index.min(), site_data.index.max()

# Adjust the date slider to handle date ranges properly
date_range = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="YYYY-MM-DD"
)

# Convert selected dates to pandas Timestamps for filtering
start_datetime, end_datetime = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
df_filtered = site_data[(site_data.index >= start_datetime) & (site_data.index <= end_datetime)]

# Sections for CO2 and CH4 Analyzers
st.header("CO2 Analyzer")
st.write("CO2 analysis details would go here.")

st.header("CH4 Analyzer")
st.write("CH4 analysis details would go here.")

# CH4 Analyzer with Bar Graph for CH4 variables
ch4_vars = [
    'INST_LI7700_NOT_READY', 'INST_LI7700_NO_SIGNAL', 'INST_LI7700_RE_UNLOCKED',
    'INST_LI7700_BAD_TEMP', 'INST_LI7700_LASER_T_UNREG', 'INST_LI7700_BLOCK_T_UNREG',
    'INST_LI7700_MOTOR_SPINNING', 'INST_LI7700_PUMP_ON', 'INST_LI7700_TOP_HEATER_ON',
    'INST_LI7700_BOTTOM_HEATER_ON', 'INST_LI7700_CALIBRATING', 'INST_LI7700_MOTOR_FAILURE',
    'INST_LI7700_BAD_AUX_TC1', 'INST_LI7700_BAD_AUX_TC2', 'INST_LI7700_BAD_AUX_TC3',
    'INST_LI7700_BOX_CONNECTED'
]
# Remove 'INST_LI7700_' prefix and calculate percentages
ch4_data = {var.replace('INST_LI7700_', ''): 100 * np.mean(df_filtered[var] != 0) for var in ch4_vars if var in df_filtered.columns}
ch4_df = pd.DataFrame(list(ch4_data.items()), columns=['Variable', 'Percentage'])

# Plotting
fig_ch4 = px.bar(
    ch4_df, 
    x='Variable', 
    y='Percentage', 
    title="CH4 Analyzer Status",
    labels={'Variable': ' ', 'Percentage': 'Percentage of occurrence'},
    range_y=[0, 100],  # Ensures y-axis ranges from 0% to 100%
    color_discrete_sequence=['#1295D8']
)
st.plotly_chart(fig_ch4)

# Biomet Data Visualization
st.header("Biomet")
biomet_vars = ['LWIN_1_1_1', 'LWOUT_1_1_1', 'NDVI_1_1_1', 'PPFDR_1_1_1', 'PPFD_1_1_1', 'P_RAIN_1_1_1', 'RH_1_1_1', 'SHF_1_1_1', 'SHF_1_1_2', 'SHF_1_1_3', 'SWIN_1_1_1', 'SWOUT_1_1_1', 'TA_1_1_1', 'TS_1_1_1', 'TS_1_2_1', 'TS_1_3_1', 'TS_1_4_1', 'TS_1_5_1', 'TS_1_6_1', 'TS_2_1_1', 'TS_2_2_1', 'TS_2_3_1', 'TS_2_4_1', 'TS_2_5_1', 'TS_2_6_1', 'TS_3_1_1', 'TS_3_2_1', 'TS_3_3_1', 'TS_3_4_1', 'TS_3_5_1', 'TS_3_6_1', 'TW_1_1_1', 'WL_1_1_1']
selected_vars = st.multiselect('Select Biomet Variables', biomet_vars, default=biomet_vars[:5])
for var in selected_vars:
    if var in df_filtered.columns:
        fig = px.line(df_filtered, x=df_filtered.index, y=var, title=f"{var} Data at {selected_site}", color_discrete_sequence=['#FFB511'])
        st.plotly_chart(fig)
