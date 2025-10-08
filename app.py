import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Flight Crash Analysis", layout="wide")
st.title("✈️ Flight Crash Analysis Dashboard")

# ----------------- Load Data -----------------
csv_path = "data/flight_crash_data.csv"

try:
    df = pd.read_csv(csv_path, sep="\t", engine="python")
except FileNotFoundError:
    st.error("CSV file not found. Please check the file path.")
    st.stop()
except pd.errors.ParserError as e:
    st.error(f"Error parsing CSV: {e}")
    st.stop()

# ----------------- Normalize Columns -----------------
df = df.rename(columns={"fatalities": "fat", "damage_level": "dmg_level"})
df.columns = df.columns.str.strip().str.lower()

# ----------------- Clean Data -----------------
# Strip whitespace and normalize text columns
for col in ["type", "operator", "dmg_level", "location"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.title()

# Ensure numeric columns
df["fat"] = pd.to_numeric(df["fat"], errors="coerce").fillna(0)

# Parse date
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    if df["date"].isna().any():
        st.warning("Some dates could not be parsed and are set as NaT.")

# ----------------- Sidebar Filters -----------------
st.sidebar.header("🔍 Filters")

# Operator filter
if "operator" in df.columns:
    operators = ["All"] + sorted(df["operator"].dropna().unique())
    selected_operator = st.sidebar.selectbox("Operator", operators)
    if selected_operator != "All":
        df = df[df["operator"] == selected_operator]

# Damage Level filter
if "dmg_level" in df.columns:
    dmg_levels = ["All"] + sorted(df["dmg_level"].dropna().unique())
    selected_dmg = st.sidebar.selectbox("Damage Level", dmg_levels)
    if selected_dmg != "All":
        df = df[df["dmg_level"] == selected_dmg]

# Year filter
if "date" in df.columns:
    df["year"] = df["date"].dt.year
    years = ["All"] + sorted(df["year"].dropna().unique().astype(int))
    selected_year = st.sidebar.selectbox("Year", years)
    if selected_year != "All":
        df = df[df["year"] == int(selected_year)]

# Warn if no data after filters
if df.empty:
    st.warning("No data available for the selected filters.")

# ----------------- Summary Metrics -----------------
st.subheader("📊 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Crashes", len(df))
col2.metric("Total Fatalities", int(df["fat"].sum()) if "fat" in df.columns else 0)
col3.metric("Unique Operators", df["operator"].nunique() if "operator" in df.columns else 0)
col4.metric("Unique Aircraft Types", df["type"].nunique() if "type" in df.columns else 0)

# ----------------- Interactive Charts -----------------
st.subheader("📈 Crash Analysis")

# 1. Crashes by Aircraft Type
if "type" in df.columns and not df.empty:
    fig_type = px.histogram(df, x="type", title="Crashes by Aircraft Type", color="type")
    st.plotly_chart(fig_type, use_container_width=True)

# 2. Crashes by Damage Level
if "dmg_level" in df.columns and not df.empty:
    fig_dmg = px.histogram(df, x="dmg_level", title="Crashes by Damage Level", color="dmg_level")
    st.plotly_chart(fig_dmg, use_container_width=True)

# 3. Fatalities over Time
if "date" in df.columns and "fat" in df.columns and not df.empty:
    df_time = df.groupby("date")["fat"].sum().reset_index()
    fig_fat = px.line(df_time, x="date", y="fat", title="Fatalities Over Time")
    st.plotly_chart(fig_fat, use_container_width=True)

# 4. Top 10 Crash Locations
if "location" in df.columns and not df.empty:
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
