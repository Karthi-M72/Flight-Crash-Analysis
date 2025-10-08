# flight_dashboard_app - Streamlit scaffold
import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Flight Crash Dashboard", layout="wide")

st.title("Flight Crash Dashboard (recreated)")

DATA_PATH = "data/flight_crash_data.csv"

if not os.path.exists(DATA_PATH):
    st.warning("No dataset found at data/flight_crash_data.csv. Run `python extract_data.py` in the app folder to attempt extraction from your uploaded files, or place the CSV at this path.")
    st.info("A sample minimal CSV should include columns: date, year, operator, aircraft_type, fatalities, damage_level, latitude, longitude, location")
    st.stop()

df = pd.read_csv(DATA_PATH, parse_dates=["date"], dayfirst=True, infer_datetime_format=True)

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accidents", int(df.shape[0]))
col2.metric("Total Fatalities", int(df['fatalities'].sum()))
col3.metric("Total Operators", int(df['operator'].nunique()))
col4.metric("Max Fatalities in Single Accident", int(df['fatalities'].max()))

# Filters
with st.sidebar:
    st.header("Filters")
    years = st.multiselect("Year", sorted(df['year'].unique()), default=sorted(df['year'].unique()))
    damage = st.multiselect("Damage Level", sorted(df['damage_level'].unique()), default=sorted(df['damage_level'].unique()))
    operators = st.multiselect("Operator (top 20)", sorted(df['operator'].unique())[:20], default=None)

filtered = df[df['year'].isin(years) & df['damage_level'].isin(damage)]
if operators:
    filtered = filtered[filtered['operator'].isin(operators)]

# Main charts
st.subheader("Accidents Over Time")
acc_time = filtered.groupby('year').size().reset_index(name='count')
fig1 = px.bar(acc_time, x='year', y='count', title="Accidents Over Year")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("Damage Level Distribution")
dist = filtered['damage_level'].value_counts().reset_index()
dist.columns = ['damage_level','count']
fig2 = px.pie(dist, names='damage_level', values='count', title="Damage Level Distribution")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Top Operators by Accidents")
top_ops = filtered['operator'].value_counts().nlargest(10).reset_index()
top_ops.columns = ['operator','count']
fig3 = px.bar(top_ops, x='operator', y='count', title="Top Operators (by accident count)")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Geographic Map")
if 'latitude' in filtered.columns and 'longitude' in filtered.columns:
    fig4 = px.scatter_mapbox(filtered, lat='latitude', lon='longitude', hover_name='location', size_max=10, zoom=1)
    fig4.update_layout(mapbox_style="open-street-map")
    fig4.update_layout(height=500)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("No latitude/longitude columns found for map visualization.")
