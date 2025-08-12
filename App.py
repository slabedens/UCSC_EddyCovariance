import streamlit as st

st.logo("paytan_lab_logo.png")  

pg = st.navigation([
    st.Page("pages/overview.py", title="Overview"),
    st.Page("pages/plot.py",     title="Plot")
])
pg.run()
