
Flight Crash Dashboard - scaffold
--------------------------------
Files created at: /mnt/data/flight_dashboard_app

1) extract_data.py - helper to pull CSV/JSON from uploaded archives in /mnt/data into ./data/
   Run inside the app folder: python extract_data.py

2) app.py - Streamlit app. Expects data/flight_crash_data.csv to exist with columns:
   date, year, operator, aircraft_type, fatalities, damage_level, latitude, longitude, location

3) requirements.txt - python dependencies

Tips:
- If extract_data.py doesn't find CSVs, you'll need to export the dataset from Power BI as CSV or provide a CSV extracted from the semantic model.
- A minimal CSV will let the app render and you can iterate on visuals to match Power BI more closely.
