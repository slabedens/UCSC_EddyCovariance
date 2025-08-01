import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

### Functions ###
def plot_variable_plotly(df, variables):
    # UC priority colors
    uc_colors = ["#1295D8", "#FFB511", "#005581", "#72CDF4", "#FFE552", "#7C7E7F", "#00A3AD"]

    # keep only numeric columns
    variables = [v for v in variables if pd.api.types.is_numeric_dtype(df[v])]
    if not variables:
        st.info("Select at least one numeric variable to plot.")
        return

    fig = go.Figure()
    for i, v in enumerate(variables):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[v],
            mode="lines",
            name=v,
            line=dict(color=uc_colors[i % len(uc_colors)])  # cycle through colors
        ))

    fig.update_layout(
        template="plotly",
        xaxis=dict(rangeslider=dict(visible=True), type="date"),
        height=400,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    st.plotly_chart(fig, use_container_width=True)


### Site Data Initialization ###
site_name = ['Castroville', 'Hester', 'North', 'Porter', 'Yampah']
site_ID = ['MCP', 'EKH', 'EKN', 'EKP','EKY']

df_allsites = {}
for site_index in range(len(site_name)):
    path = f"EC_Data/{site_name[site_index]}/{site_ID[site_index]}_processed/"
    df_site = pd.read_csv(f"{path}{site_ID[site_index]}_ECdata_QC9.csv", parse_dates=['datetime'], index_col='datetime')
    df_allsites[site_name[site_index]] = df_site

### Page configuration ###
st.title("Explore raw data after QA/QC")
st.sidebar.markdown("v1.0")  # Markdown to format as bold
logo_path = "paytan_lab_logo.png"
#st.sidebar.image(logo_path)



# --- CONTAINER 1 --------------------------------------------------------------------------------------------------------
with st.container():

    ### Selector buttons ###
    site_select = st.selectbox('Select site', site_name, key="plot1")    
    df_site = df_allsites[site_select]

    # Determine defaults: prefer these three if present
    preferred = ['FC_GF','FC', 'FC_model']
    available = [c for c in preferred if c in df_site.columns]

    # If none (or only some) are available, fill remaining with first numeric cols (without duplicates)
    numeric_cols = [c for c in df_site.columns if pd.api.types.is_numeric_dtype(df_site[c])]
    fallback = [c for c in numeric_cols if c not in available]
    default_vars = available + fallback[: max(0, 3 - len(available))]

    variables = st.multiselect(
        "Select variables",
        options=df_site.columns.tolist(),
        default=default_vars
    )

    plot_variable_plotly(df_site, variables)


# --- CONTAINER 2 --------------------------------------------------------------------------------------------------------
with st.container():
    st.subheader("")
    st.subheader("")

    ### Selector buttons ###
    # Buttons style
    st.markdown("""
    <style>
    /* Multiselect chips (tags) */
    .stMultiSelect [data-baseweb="tag"] {
    background-color: #DCE1E9 !important;   /* light grey fill */
    color: #000000 !important;              /* black text */
    border-radius: 12px !important;
    }

    /* Optional hover state */
    .stMultiSelect [data-baseweb="tag"]:hover {
    background-color: #F3F3F3 !important;   /* slightly lighter grey */
    border-color: #888B8D !important;       /* UC Gray */
    }
    </style>
    """, unsafe_allow_html=True)
    
    site_select2 = st.selectbox('Select site', site_name, key="plot2")    
    df_site2 = df_allsites[site_select2]

    # Determine defaults: prefer these three if present
    preferred2 = ['FCH4_GF', 'FCH4', 'FCH4_model']
    available2 = [c for c in preferred2 if c in df_site2.columns] 

    # If none (or only some) are available, fill remaining with first numeric cols (without duplicates)
    numeric_cols2 = [c for c in df_site2.columns if pd.api.types.is_numeric_dtype(df_site2[c])]
    fallback2 = [c for c in numeric_cols2 if c not in available2]
    default_vars2 = available2 + fallback2[: max(0, 3 - len(available2))]

    variables2 = st.multiselect(
        "Select variables",
        options=df_site2.columns.tolist(),
        default=default_vars2
    )

    plot_variable_plotly(df_site2, variables2)

