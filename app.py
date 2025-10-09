import streamlit as st
import pandas as pd
import plotly.express as px
import os

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Flight Crash Dashboard", layout="wide")
st.title("✈️ Flight Crash Dashboard (Interactive Replica)")

DATA_PATH = "data/flight_crash_data.csv"

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
if not os.path.exists(DATA_PATH):
    st.error("❌ No dataset found at data/flight_crash_data.csv.")
    st.stop()

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.strip().str.lower()

# Ensure consistency
df.rename(columns={
    "type": "aircraft_type",
}, inplace=True)

# Parse date + year
df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
df["year"] = df["date"].dt.year

# Normalize text columns
df["damage_level"] = df["damage_level"].str.capitalize().fillna("Unknown")
df["operator"] = df["operator"].fillna("Unknown")
df["fatalities"] = pd.to_numeric(df["fatalities"], errors="coerce").fillna(0)

# -------------------------------------------------
# KPIs
# -------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Accidents", f"{len(df):,}")
col2.metric("Total Fatalities", f"{int(df['fatalities'].sum()):,}")
col3.metric("Unique Operators", f"{df['operator'].nunique():,}")
col4.metric("Max Fatalities (Single Accident)", f"{int(df['fatalities'].max())}")

# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
with st.sidebar:
    st.header("🧭 Filters")
    years = st.multiselect("Year(s)", sorted(df["year"].dropna().unique()),
                           default=sorted(df["year"].dropna().unique()))
    dmg = st.multiselect("Damage Level(s)", sorted(df["damage_level"].unique()),
                         default=sorted(df["damage_level"].unique()))
    ops = st.multiselect("Operator(s)", sorted(df["operator"].unique())[:20])

filtered = df[df["year"].isin(years) & df["damage_level"].isin(dmg)]
if ops:
    filtered = filtered[filtered["operator"].isin(ops)]

# -------------------------------------------------
# CHARTS
# -------------------------------------------------

# 1️⃣ Accidents Over Time
st.subheader("📅 Accidents Over Time")
acc_by_year = filtered.groupby("year").size().reset_index(name="accidents")
fig1 = px.bar(acc_by_year, x="year", y="accidents",
              title="Yearly Accident Count",
              labels={"year": "Year", "accidents": "Number of Accidents"},
              color="accidents", color_continuous_scale="Blues")
fig1.update_layout(xaxis=dict(dtick=1))
st.plotly_chart(fig1, use_container_width=True)

# 2️⃣ Fatalities Trend
st.subheader("☠️ Fatalities Trend Over Years")
fatal_trend = filtered.groupby("year")["fatalities"].sum().reset_index()
fig2 = px.line(fatal_trend, x="year", y="fatalities", markers=True,
               title="Total Fatalities by Year")
st.plotly_chart(fig2, use_container_width=True)

# 3️⃣ Damage Level Distribution
st.subheader("💥 Damage Level Distribution")
damage_counts = filtered["damage_level"].value_counts().reset_index()
damage_counts.columns = ["damage_level", "count"]
fig3 = px.pie(damage_counts, names="damage_level", values="count",
              title="Distribution of Damage Levels",
              color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(fig3, use_container_width=True)

# 4️⃣ Top 10 Operators
st.subheader("🏢 Top 10 Operators by Number of Accidents")
top_ops = filtered["operator"].value_counts().nlargest(10).reset_index()
top_ops.columns = ["operator", "accidents"]
fig4 = px.bar(top_ops, x="operator", y="accidents",
              color="accidents", color_continuous_scale="Blues",
              title="Top 10 Operators")
st.plotly_chart(fig4, use_container_width=True)

# 5️⃣ Top 10 Aircraft Types
st.subheader("🛩️ Aircraft Types Most Involved in Accidents")
top_aircraft = filtered["aircraft_type"].value_counts().nlargest(10).reset_index()
top_aircraft.columns = ["aircraft_type", "accidents"]
fig5 = px.bar(top_aircraft, x="aircraft_type", y="accidents",
              color="accidents", color_continuous_scale="Purples",
              title="Top 10 Aircraft Types Involved")
st.plotly_chart(fig5, use_container_width=True)

# 6️⃣ Damage Level by Year (Clustered Bar)
st.subheader("📊 Damage Level by Year")
dmg_by_year = filtered.groupby(["year", "damage_level"]).size().reset_index(name="accidents")
fig6 = px.bar(dmg_by_year, x="year", y="accidents", color="damage_level",
              barmode="group", title="Accidents by Damage Level and Year")
st.plotly_chart(fig6, use_container_width=True)

# 7️⃣ Accident Table
st.subheader("📋 Recent Accidents (Filtered)")
st.dataframe(filtered.sort_values("date", ascending=False)[
    ["date", "operator", "aircraft_type", "location", "fatalities", "damage_level"]
], use_container_width=True)

# Footer
st.markdown("---")
st.caption("Created by [Your Name] | Powered by Streamlit + Plotly")
