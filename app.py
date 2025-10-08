import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -------------------------------------------------
# APP CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Flight Crash Dashboard", layout="wide")
st.title("✈️ Flight Crash Dashboard (Recreated from Power BI)")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
DATA_PATH = "data/flight_crash_data.csv"

if not os.path.exists(DATA_PATH):
    st.error("❌ No dataset found at data/flight_crash_data.csv. Please add your cleaned_flight_data.csv or .xls converted file.")
    st.stop()

# Read your dataset
df = pd.read_csv(DATA_PATH)

# Rename columns to uniform names for consistency
df.rename(columns={
    "acc.date": "date",
    "type": "aircraft_type",
    "fat": "fatalities",
    "dmg_level": "damage_level"
}, inplace=True)

# Parse date & derive year
df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
df["year"] = df["date"].dt.year

# Clean up missing values
df["damage_level"] = df["damage_level"].fillna("Unknown")
df["operator"] = df["operator"].fillna("Unknown")
df["fatalities"] = df["fatalities"].fillna(0)

# -------------------------------------------------
# KPI METRICS
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accidents", f"{df.shape[0]:,}")
col2.metric("Total Fatalities", f"{int(df['fatalities'].sum()):,}")
col3.metric("Total Operators", f"{df['operator'].nunique():,}")
col4.metric("Max Fatalities in Single Accident", f"{int(df['fatalities'].max())}")

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
with st.sidebar:
    st.header("🧭 Filters")
    years = st.multiselect("Select Year(s)", sorted(df["year"].dropna().unique()), default=sorted(df["year"].dropna().unique()))
    damage_levels = st.multiselect("Select Damage Level(s)", sorted(df["damage_level"].unique()), default=sorted(df["damage_level"].unique()))
    operators = st.multiselect("Filter by Operator", sorted(df["operator"].unique())[:20])

# Apply filters
filtered_df = df[df["year"].isin(years) & df["damage_level"].isin(damage_levels)]
if operators:
    filtered_df = filtered_df[filtered_df["operator"].isin(operators)]

# -------------------------------------------------
# CHARTS
# -------------------------------------------------

# --- 1. Accidents Over Time ---
st.subheader("📅 Accidents Over Time")
acc_over_time = filtered_df.groupby("year").size().reset_index(name="accident_count")
fig1 = px.bar(acc_over_time, x="year", y="accident_count",
              title="Yearly Number of Accidents",
              labels={"year": "Year", "accident_count": "Number of Accidents"})
fig1.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig1, use_container_width=True)

# --- 2. Damage Level Distribution ---
st.subheader("💥 Damage Level Distribution")
damage_dist = filtered_df["damage_level"].value_counts().reset_index()
damage_dist.columns = ["damage_level", "count"]
fig2 = px.pie(damage_dist, names="damage_level", values="count",
              title="Distribution of Damage Levels",
              color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig2, use_container_width=True)

# --- 3. Top 10 Operators by Accident Count ---
st.subheader("🏢 Top 10 Operators by Number of Accidents")
top_ops = filtered_df["operator"].value_counts().nlargest(10).reset_index()
top_ops.columns = ["operator", "accidents"]
fig3 = px.bar(top_ops, x="operator", y="accidents",
              title="Top 10 Operators",
              color="accidents",
              color_continuous_scale="Blues")
st.plotly_chart(fig3, use_container_width=True)

# --- 4. Aircraft Types Most Involved in Accidents ---
st.subheader("🛩️ Aircraft Types Involved in Accidents")
top_aircraft = filtered_df["aircraft_type"].value_counts().nlargest(10).reset_index()
top_aircraft.columns = ["aircraft_type", "accidents"]
fig4 = px.bar(top_aircraft, x="aircraft_type", y="accidents",
              title="Top 10 Aircraft Types Involved in Accidents",
              color="accidents",
              color_continuous_scale="Purples")
st.plotly_chart(fig4, use_container_width=True)

# --- 5. Fatalities Distribution ---
st.subheader("☠️ Fatalities by Damage Level")
fatal_by_dmg = filtered_df.groupby("damage_level")["fatalities"].sum().reset_index()
fig5 = px.bar(fatal_by_dmg, x="damage_level", y="fatalities",
              title="Total Fatalities per Damage Level",
              color="fatalities",
              color_continuous_scale="Reds")
st.plotly_chart(fig5, use_container_width=True)

# --- 6. Accident Locations Table ---
st.subheader("🌍 Accident Locations")
st.dataframe(filtered_df[["date", "operator", "aircraft_type", "location", "damage_level", "fatalities"]].sort_values("date", ascending=False), use_container_width=True)

# Footer
st.markdown("---")
st.caption("Created by [You] — Powered by Streamlit & Plotly")
