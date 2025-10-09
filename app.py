# app.py - Flight Crash Dashboard (Tabbed, full visuals)
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from textwrap import dedent

st.set_page_config(page_title="Flight Crash Dashboard", layout="wide")
st.title("✈️ Flight Crash Dashboard — Interactive Replica")

DATA_PATH = "data/flight_crash_data.csv"
GEOCODE_CACHE = "data/geocoded_locations.csv"

# ---------------------------
# Helper functions
# ---------------------------
def load_data(path=DATA_PATH):
    if not os.path.exists(path):
        st.error(f"Dataset not found at {path}. Please add the CSV there.")
        st.stop()
    df = pd.read_csv(path)
    # normalize columns
    df.columns = df.columns.str.strip().str.lower()
    # standardize names
    if "type" in df.columns:
        df = df.rename(columns={"type": "aircraft_type"})
    # parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    df["year"] = df["date"].dt.year
    # normalize text and numeric
    if "damage_level" in df.columns:
        df["damage_level"] = df["damage_level"].astype(str).str.capitalize().fillna("Unknown")
    else:
        df["damage_level"] = "Unknown"
    df["operator"] = df.get("operator", pd.Series("Unknown")).fillna("Unknown")
    df["fatalities"] = pd.to_numeric(df.get("fatalities", 0), errors="coerce").fillna(0)
    return df

def ensure_geocoded(df):
    """Return df with latitude/longitude if available or from cache."""
    if "latitude" in df.columns and "longitude" in df.columns:
        return df
    # try reading geocode cache
    if os.path.exists(GEOCODE_CACHE):
        geo = pd.read_csv(GEOCODE_CACHE)
        geo.columns = geo.columns.str.strip().str.lower()
        # merge on location
        if "location" in df.columns and "location" in geo.columns:
            df = df.merge(geo, on="location", how="left")
    return df

def geocode_locations(locations, provider="nominatim", user_agent="flight-crash-dashboard"):
    """Attempt to geocode using geopy Nominatim (returns list of dicts)."""
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter
    except Exception as e:
        st.error("geopy not installed. Add geopy to requirements to enable geocoding.")
        return {}

    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    results = {}
    for loc in locations:
        try:
            if pd.isna(loc) or loc == "":
                results[loc] = {"latitude": None, "longitude": None}
                continue
            # call geocode
            g = geocode(loc)
            if g:
                results[loc] = {"latitude": g.latitude, "longitude": g.longitude}
            else:
                results[loc] = {"latitude": None, "longitude": None}
        except Exception:
            results[loc] = {"latitude": None, "longitude": None}
    return results

# ---------------------------
# Load & prepare data
# ---------------------------
df = load_data()
df = ensure_geocoded(df)

# default sidebar filters
with st.sidebar:
    st.header("Filters")
    years = st.multiselect("Year(s)", sorted(df["year"].dropna().unique()), default=sorted(df["year"].dropna().unique()))
    damage_sel = st.multiselect("Damage Level(s)", sorted(df["damage_level"].unique()), default=sorted(df["damage_level"].unique()))
    operator_sel = st.multiselect("Operator(s) (top 50 shown)", sorted(df["operator"].unique())[:50])

# apply filters
filtered = df.copy()
if years:
    filtered = filtered[filtered["year"].isin(years)]
if damage_sel:
    filtered = filtered[filtered["damage_level"].isin(damage_sel)]
if operator_sel:
    filtered = filtered[filtered["operator"].isin(operator_sel)]

# ---------------------------
# Tabs: Overview / Analysis / Insights / Map / Data
# ---------------------------
tabs = st.tabs(["Overview", "Fatality & Damage Analysis", "Aircraft & Operator Insights", "Map & Locations", "Data Explorer"])

# ---------- Overview ----------
with tabs[0]:
    st.subheader("Accident Overview")
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Accidents", f"{len(filtered):,}")
    k2.metric("Total Fatalities", f"{int(filtered['fatalities'].sum()):,}")
    k3.metric("Total Unique Operators", f"{filtered['operator'].nunique():,}")
    k4.metric("Max Fatalities in Single Accident", f"{int(filtered['fatalities'].max()) if len(filtered)>0 else 0:,}")

    st.markdown("---")
    # Accidents over time
    st.markdown("#### Accidents Over Time")
    counts = filtered.groupby("year").size().reset_index(name="accidents")
    fig_year = px.bar(counts, x="year", y="accidents", title="Accidents by Year", labels={"accidents":"Number of Accidents"})
    fig_year.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_year, use_container_width=True)

    # Damage distribution + top operators
    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown("#### Damage Level Distribution")
        dmg_counts = filtered["damage_level"].value_counts().reset_index()
        dmg_counts.columns = ["damage_level","count"]
        fig_pie = px.pie(dmg_counts, names="damage_level", values="count", title="Damage Level Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        st.markdown("#### Number of Accidents by Operator (Top 15)")
        top_ops = filtered["operator"].value_counts().nlargest(15).reset_index()
        top_ops.columns = ["operator","accidents"]
        fig_ops = px.bar(top_ops, x="accidents", y="operator", orientation="h", title="Top Operators by Accident Count")
        st.plotly_chart(fig_ops, use_container_width=True)

    st.markdown("---")
    # Average fatalities & Year-wise damage breakdown
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Average Fatalities Reported (by aircraft type)")
        avg_fat = filtered.groupby("aircraft_type", dropna=False)["fatalities"].mean().reset_index().nlargest(10, "fatalities")
        avg_fat.columns = ["aircraft_type","avg_fatalities"]
        fig_avg = px.bar(avg_fat, x="avg_fatalities", y="aircraft_type", orientation="h", title="Top 10 Aircraft Types by Avg Fatalities")
        st.plotly_chart(fig_avg, use_container_width=True)
    with c2:
        st.markdown("#### Year-wise Breakdown of Damage Levels")
        dmg_year = filtered.groupby(["year","damage_level"]).size().reset_index(name="accidents")
        fig_dy = px.bar(dmg_year, x="year", y="accidents", color="damage_level", barmode="group", title="Damage Level by Year")
        st.plotly_chart(fig_dy, use_container_width=True)

# ---------- Fatality & Damage Analysis ----------
with tabs[1]:
    st.subheader("Fatality & Damage Analysis")

    # Fatality Ranges histogram / binned counts
    st.markdown("#### Number of Accidents by Fatality Ranges")
    bins = [-1,0,1,5,10,20,50,1000]
    labels = ["0","1-5","6-10","11-20","21-50","51-100","100+"]
    filtered["fatal_range"] = pd.cut(filtered["fatalities"], bins=bins, labels=labels, include_lowest=True)
    fr_counts = filtered["fatal_range"].value_counts().reindex(labels).reset_index()
    fr_counts.columns = ["fatal_range","count"]
    fig_fr = px.bar(fr_counts, x="fatal_range", y="count", title="Accidents by Fatality Ranges")
    st.plotly_chart(fig_fr, use_container_width=True)

    st.markdown("---")
    # Top 10 highest fatality accidents table
    st.markdown("#### Top 10 Highest Fatality Accidents")
    top_fatal = filtered.sort_values("fatalities", ascending=False).head(10)[["date","operator","aircraft_type","fatalities","location"]]
    st.dataframe(top_fatal.reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    # Operator vs Damage Level summary (pivot-like)
    st.markdown("#### Operator vs Damage Level (Counts)")
    pivot = filtered.pivot_table(index="operator", columns="damage_level", values="fatalities", aggfunc="count", fill_value=0)
    # show heatmap if not too wide
    if pivot.shape[0] <= 50:
        fig_heat = px.imshow(pivot, labels=dict(x="Damage Level", y="Operator", color="Count"),
                             x=pivot.columns, y=pivot.index, aspect="auto", title="Operator vs Damage Level (counts)")
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.dataframe(pivot.sort_values(pivot.columns.tolist(), ascending=False).head(50))

# ---------- Aircraft & Operator Insights ----------
with tabs[2]:
    st.subheader("Aircraft & Operator Insights")

    # Top 10 Aircraft Types Involved
    st.markdown("#### Top 10 Aircraft Types Involved in Accidents")
    top_air = filtered["aircraft_type"].value_counts().nlargest(10).reset_index()
    top_air.columns = ["aircraft_type","accidents"]
    fig_air = px.bar(top_air, x="accidents", y="aircraft_type", orientation="h", title="Top 10 Aircraft Types")
    st.plotly_chart(fig_air, use_container_width=True)

    st.markdown("---")
    # Operators responsible for most fatalities (sum)
    st.markdown("#### Operators Responsible for Most Fatalities")
    ops_fat = filtered.groupby("operator")["fatalities"].sum().reset_index().nlargest(15,"fatalities")
    fig_ops_fat = px.bar(ops_fat, x="fatalities", y="operator", orientation="h", title="Operators by Total Fatalities")
    st.plotly_chart(fig_ops_fat, use_container_width=True)

    st.markdown("---")
    # Aircraft-wise summary: counts and average fatalities
    st.markdown("#### Aircraft-wise Summary: Count & Avg Fatalities")
    aw = filtered.groupby("aircraft_type").agg(accidents=("aircraft_type","size"), avg_fatalities=("fatalities","mean")).reset_index().sort_values("accidents", ascending=False).head(20)
    st.dataframe(aw, use_container_width=True)

# ---------- Map & Locations ----------
with tabs[3]:
    st.subheader("Geographic Locations of Accidents")

    df_geo = ensure_geocoded(filtered)

    # If no lat/lon present, show instructions and button to geocode
    if "latitude" not in df_geo.columns or "longitude" not in df_geo.columns or df_geo["latitude"].isna().all():
        st.info(dedent("""
            No latitude/longitude columns detected for locations.  
            You can geocode unique 'location' values using OpenStreetMap (Nominatim) from the app.
            **Note:** Geocoding may take time and respects rate limits. Results are cached in `data/geocoded_locations.csv`.
        """))
        if st.button("🛰️ Geocode unique locations now"):
            unique_locs = filtered["location"].dropna().unique().tolist()
            with st.spinner(f"Geocoding {len(unique_locs)} unique locations (may take a while)..."):
                results = geocode_locations(unique_locs)
            # build cache df
            cache_rows = []
            for loc, coords in results.items():
                cache_rows.append({"location": loc, "latitude": coords.get("latitude"), "longitude": coords.get("longitude")})
            cache_df = pd.DataFrame(cache_rows)
            os.makedirs("data", exist_ok=True)
            cache_df.to_csv(GEOCODE_CACHE, index=False)
            st.success(f"Geocoding finished — saved {len(cache_df)} rows to {GEOCODE_CACHE}. Reload the app to plot the map.")
    else:
        # Plot map
        df_plot = df_geo.dropna(subset=["latitude","longitude"])
        if len(df_plot) == 0:
            st.warning("Latitude/longitude exist but all rows are empty.")
        else:
            st.markdown("#### Accident Map (markers colored by damage level)")
            fig_map = px.scatter_mapbox(df_plot, lat="latitude", lon="longitude", hover_name="operator",
                                       hover_data=["date","aircraft_type","fatalities","damage_level"],
                                       color="damage_level", zoom=1, height=600)
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Top Accident Locations (by count)")
    loc_counts = filtered["location"].value_counts().nlargest(20).reset_index()
    loc_counts.columns = ["location","count"]
    st.dataframe(loc_counts, use_container_width=True)

# ---------- Data Explorer ----------
with tabs[4]:
    st.subheader("Data Explorer")
    st.markdown("Filter results and inspect raw data below.")
    st.write(f"Showing {len(filtered):,} rows (after filters).")
    st.dataframe(filtered.sort_values("date", ascending=False).reset_index(drop=True), use_container_width=True)

st.markdown("---")
st.caption("Created by You — Streamlit + Plotly")
