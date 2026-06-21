import pandas as pd
import numpy as np

def analyze():
    input_path = r'C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv'
    df = pd.read_csv(input_path)
    
    output_lines = []
    output_lines.append("=== RAW DATASET ANALYSIS ===")
    output_lines.append(f"Total rows in raw dataset: {len(df)}")
    output_lines.append(f"Columns: {list(df.columns)}")
    
    # Missing values
    missing = df.isnull().sum()
    output_lines.append("\n=== MISSING VALUES (Top 15) ===")
    for col, count in missing.sort_values(ascending=False).head(15).items():
        output_lines.append(f"{col}: {count} ({count/len(df)*100:.2f}%)")
        
    # Class balance of requires_road_closure
    if 'requires_road_closure' in df.columns:
        counts = df['requires_road_closure'].value_counts(dropna=False)
        output_lines.append("\n=== CLASS BALANCE (requires_road_closure) ===")
        for val, count in counts.items():
            output_lines.append(f"{val}: {count} ({count/len(df)*100:.2f}%)")
            
    # Event types and causes
    output_lines.append("\n=== EVENT TYPES ===")
    for val, count in df['event_type'].value_counts(dropna=False).items():
        output_lines.append(f"{val}: {count}")
        
    output_lines.append("\n=== EVENT CAUSES (Top 10) ===")
    for val, count in df['event_cause'].value_counts(dropna=False).head(10).items():
        output_lines.append(f"{val}: {count}")

    # Process data with data_pipeline logic
    df_clean = df.dropna(subset=['latitude', 'longitude'])
    df_clean = df_clean[(df_clean['latitude'] > 12.7) & (df_clean['latitude'] < 13.2) & 
                        (df_clean['longitude'] > 77.4) & (df_clean['longitude'] < 77.8)]
    df_clean['start_datetime'] = pd.to_datetime(df_clean['start_datetime'], errors='coerce')
    df_clean = df_clean.dropna(subset=['start_datetime'])
    df_clean['hour'] = df_clean['start_datetime'].dt.hour
    df_clean['day_of_week'] = df_clean['start_datetime'].dt.dayofweek
    df_clean['is_peak'] = df_clean['hour'].apply(lambda x: 1 if (8 <= x <= 11) or (17 <= x <= 20) else 0)
    df_clean['event_cause'] = df_clean['event_cause'].fillna('Unknown')
    df_clean['priority'] = df_clean['priority'].fillna('Medium')
    df_clean['requires_road_closure'] = df_clean['requires_road_closure'].astype(int)
    
    output_lines.append("\n=== CLEANED DATASET ANALYSIS ===")
    output_lines.append(f"Total rows in cleaned dataset: {len(df_clean)}")
    counts_clean = df_clean['requires_road_closure'].value_counts(dropna=False)
    output_lines.append("Class balance of requires_road_closure in cleaned dataset:")
    for val, count in counts_clean.items():
        output_lines.append(f"{val}: {count} ({count/len(df_clean)*100:.2f}%)")
        
    output_lines.append("\n=== TEMPORAL DISTRIBUTION (hour) ===")
    for hour, count in df_clean['hour'].value_counts().sort_index().items():
        output_lines.append(f"Hour {hour:02d}: {count}")
        
    output_lines.append("\n=== PEAK VS NON-PEAK ===")
    for peak, count in df_clean['is_peak'].value_counts().items():
        output_lines.append(f"Peak {peak}: {count} ({count/len(df_clean)*100:.2f}%)")

    # Write output to file
    with open(r'D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_1\dataset_stats.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print("Analysis finished and written to dataset_stats.txt")

if __name__ == '__main__':
    analyze()
