import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Flight Crash Analysis", layout="wide")
st.title("✈️ Flight Crash Analysis Dashboard")

# ----------------- Load Data -----------------
try:
    df = pd.read_csv("data/flight_crash_data.csv")  # adjust path if needed
except FileNotFoundError:
    st.error("CSV file not found. Please check the file path.")
    st.stop()

# ----------------- Clean Columns -----------------
df.columns = df.columns.str.strip().str.lower()

# ----------------- Ensure Expected Columns -----------------
expected_cols = ["date", "type", "reg", "operator", "fat", "location", "dmg_level"]
missing_cols = [col for col in expected_cols if col not in df.columns]

if missing_cols:
    st.error(f"Missing expected columns: {', '.join(missing_cols)}")
    st.stop()

# ----------------- Parse Date Column -----------------
df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

# ----------------- Sidebar Filters -----------------
st.sidebar.header("🔍 Filters")

# Operator filter
operators = ["All"] + sorted(df["operator"].dropna().unique().tolist())
selected_operator = st.sidebar.selectbox("Operator", operators)
if selected_operator != "All":
    df = df[df["operator"] == selected_operator]

# Damage Level filter
dmg_levels = ["All"] + sorted(df["dmg_level"].dropna().unique().tolist())
selected_dmg = st.sidebar.selectbox("Damage Level", dmg_levels)
if selected_dmg != "All":
    df = df[df["dmg_level"] == selected_dmg]

# Year filter
df["year"] = df["date"].dt.year
years = ["All"] + sorted(df["year"].dropna().unique().astype(int).tolist())
selected_year = st.sidebar.selectbox("Year", years)
if selected_year != "All":
    df = df[df["year"] == int(selected_year)]

# ----------------- Summary Metrics -----------------
st.subheader("📊 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Crashes", len(df))
col2.metric("Total Fatalities", int(df["fat"].sum()))
col3.metric("Unique Operators", df["operator"].nunique())
col4.metric("Unique Aircraft Types", df["type"].nunique())

# ----------------- Interactive Charts -----------------
st.subheader("📈 Crash Analysis")

# 1. Crashes by Aircraft Type
fig_type = px.histogram(df, x="type", title="Crashes by Aircraft Type", color="type")
st.plotly_chart(fig_type, use_container_width=True)

# 2. Crashes by Damage Level
fig_dmg = px.histogram(df, x="dmg_level", title="Crashes by Damage Level", color="dmg_level")
st.plotly_chart(fig_dmg, use_container_width=True)

# 3. Fatalities over Time
fig_fat = px.line(df.groupby("date")["fat"].sum().reset_index(),
                  x="date", y="fat", title="Fatalities Over Time")
st.plotly_chart(fig_fat, use_container_width=True)

# 4. Crashes by Location (Top 10)
top_locations = df["location"].value_counts().nlargest(10).reset_index()
top_locations.columns = ["location", "count"]
fig_loc = px.bar(top_locations, x="location", y="count", title="Top 10 Crash Locations", color="location")
st.plotly_chart(fig_loc, use_container_width=True)

# ----------------- Raw Data Display -----------------
st.subheader("📋 Raw Data")
st.dataframe(df)

# ----------------- Footer -----------------
st.markdown("---")
st.markdown("© 2025 Flight Crash Analysis Dashboard")
