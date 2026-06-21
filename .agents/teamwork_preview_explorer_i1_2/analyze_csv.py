import pandas as pd
import numpy as np

# Load dataset
input_path = r'C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv'
df = pd.read_csv(input_path)

# Columns and types
print("--- Columns and Types ---")
print(df.dtypes)
print()

# Total Rows
print(f"Total Rows: {len(df)}")

# Class balance for requires_road_closure
print("\n--- Class Balance of requires_road_closure ---")
if 'requires_road_closure' in df.columns:
    print(df['requires_road_closure'].value_counts(dropna=False))
    print(df['requires_road_closure'].value_counts(normalize=True, dropna=False))
else:
    print("requires_road_closure NOT in columns!")

# Check missing values for critical fields
print("\n--- Missing Values ---")
for col in ['latitude', 'longitude', 'start_datetime', 'event_cause', 'priority', 'requires_road_closure']:
    if col in df.columns:
        missing = df[col].isnull().sum()
        print(f"{col}: {missing} missing ({missing/len(df)*100:.2f}%)")

# Event Cause values
print("\n--- Event Cause Value Counts ---")
if 'event_cause' in df.columns:
    print(df['event_cause'].value_counts(dropna=False).head(10))

# Coordinates bounding box filtering check (matching data_pipeline.py)
print("\n--- Bounding Box Filter Simulation ---")
lat_min, lat_max = 12.7, 13.2
lon_min, lon_max = 77.4, 77.8
geo_clean = df.dropna(subset=['latitude', 'longitude'])
in_bounds = geo_clean[
    (geo_clean['latitude'] > lat_min) & (geo_clean['latitude'] < lat_max) &
    (geo_clean['longitude'] > lon_min) & (geo_clean['longitude'] < lon_max)
]
print(f"Total with coords: {len(geo_clean)}")
print(f"In bounds ({lat_min}-{lat_max} Lat, {lon_min}-{lon_max} Lon): {len(in_bounds)} ({len(in_bounds)/len(df)*100:.2f}%)")

# Check requires_road_closure distribution after preprocessing steps
in_bounds = in_bounds.copy()
in_bounds['start_datetime'] = pd.to_datetime(in_bounds['start_datetime'], errors='coerce')
cleaned = in_bounds.dropna(subset=['start_datetime'])
print(f"After datetime parsing & dropna: {len(cleaned)}")
print("Class balance after filtering:")
print(cleaned['requires_road_closure'].value_counts(dropna=False))
print(cleaned['requires_road_closure'].value_counts(normalize=True, dropna=False))
