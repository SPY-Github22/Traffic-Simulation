# Gridlock AI - ML Pipeline Analysis Report

This report presents findings from the investigation of the machine learning pipeline under `D:\gridlock-ai` and the raw event dataset at `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`. It outlines a strategy for upgrading the training and validation workflows and proposes a logical consistency verification script.

---

## 1. Raw Dataset and Preprocessing Pipeline Analysis

### 1.1 Dataset Examination
- **Dataset Path**: `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`
- **Total Records**: 8,206 rows (8,207 lines including header).
- **Columns**: The dataset contains 46 columns containing temporal, spatial, categorical, and status details. Key columns include:
  - `id`: Unique event identifier.
  - `latitude`, `longitude`: Spatial coordinates of the event.
  - `event_cause`: Cause of the traffic event (e.g., `Accident`, `Waterlogging`, `Vehicle Breakdown`, `Protest / Rally`).
  - `event_type`: Categorization of event (e.g., `unplanned`, `planned`).
  - `start_datetime`: Timestamp when the event was reported.
  - `priority`: Event priority (`High`, `Medium`, `Low`).
  - `requires_road_closure`: Target variable indicating if the event required road closure (boolean: `True`/`False`).
- **Class Balance**: 
  - The dataset has a high class imbalance for the target variable `requires_road_closure`.
  - In samples inspected, approximately **4% to 10%** of events are marked as requiring road closure (`requires_road_closure = True`/`1`), while **90% to 96%** do not (`requires_road_closure = False`/`0`).
  - Because of this class imbalance, accuracy alone is a misleading metric. Optimization and evaluation must rely heavily on the **F1-Score**, **Precision**, and **Recall**.

### 1.2 Data Preprocessing (`data_pipeline.py`)
The data pipeline (`backend/data_pipeline.py`) performs the following steps to clean and transform the raw data into `cleaned_events.csv` (which contains 8,039 rows):
1. **Geospatial Filtering**: Drops rows with missing coordinates and filters records to keep only those within a rough bounding box for Bengaluru:
   - $12.7 < \text{latitude} < 13.2$
   - $77.4 < \text{longitude} < 77.8$
   This drops about 2% of the rows.
2. **Temporal Feature Extraction**: Parses `start_datetime` (dropping nulls) and extracts:
   - `hour` (0 to 23)
   - `day_of_week` (0 to 6, where 0 is Monday)
   - `is_peak`: A binary indicator set to `1` if the event occurred during peak hours (`8:00 AM - 11:59 AM` or `5:00 PM - 8:59 PM`), else `0`.
3. **Null Imputation**:
   - `event_cause` is filled with `'Unknown'` if missing.
   - `priority` is filled with `'Medium'` if missing.
4. **Target Conversion**: Map boolean `requires_road_closure` values to integers (`0` or `1`).
5. **Spatial Clustering**: Performs K-Means clustering with $k=15$ on coordinate pairs (`latitude`, `longitude`) to group events into 15 distinct functional zones (`zone_cluster` labeled `0` to `14`).

---

## 2. Strategy to Upgrade `model_training.py`

The current implementation in `model_training.py` uses a simple train-test split (80-20) and trains an XGBoost classifier. We propose upgrading this script to support 5-Fold Cross-Validation, automated hyperparameter tuning fallback, and learning curve generation.

### 2.1 5-Fold Cross-Validation
To obtain a robust, unbiased estimate of model performance, we will replace the single split with `StratifiedKFold` from `scikit-learn` to maintain class balance across folds.
- **Methodology**:
  ```python
  from sklearn.model_selection import StratifiedKFold
  skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
  ```
- **Evaluation**: For each fold, we fit the classifier on the 4 training splits and evaluate on the validation split, capturing:
  - Accuracy, Precision, Recall, and F1-Score.
- **Reporting**: Report the mean and standard deviation of each metric across all 5 folds to ensure stability.

### 2.2 Automated Hyperparameter Tuning Fallback
We will programmatically monitor model performance to detect overfitting or underfitting. If either is detected, the script will fallback to an automated grid search to find optimal hyperparameters.

#### A. Overfitting & Underfitting Criteria
Due to class imbalance, we define our criteria using the **F1-Score** (since it balances precision and recall on the minority class) and **Accuracy**:
1. **Overfitting Detection**:
   - **Criterion**: The difference between training and validation performance is excessively large.
   - **Formula**:
     $$\text{F1\_train} - \text{F1\_val} > 0.15 \quad \text{OR} \quad \text{Accuracy\_train} - \text{Accuracy\_val} > 0.10$$
2. **Underfitting Detection**:
   - **Criterion**: The model performs poorly on both training and validation sets, indicating it failed to learn patterns.
   - **Formula**:
     $$\text{F1\_train} < 0.55 \quad \text{OR} \quad \text{F1\_val} < 0.50$$

#### B. Parameter Grid for Fallback Tuning
If tuning is triggered, we run `GridSearchCV` (or `RandomizedSearchCV`) over a parameter grid targeting XGBoost hyperparameters:
- **Parameter Grid**:
  ```python
  param_grid = {
      'max_depth': [3, 5, 7],
      'learning_rate': [0.01, 0.05, 0.1, 0.2],
      'n_estimators': [50, 100, 200],
      'subsample': [0.8, 1.0],
      'colsample_bytree': [0.8, 1.0]
  }
  ```
- **Scoring**: The tuning process will optimize for the `f1` metric to handle class imbalance.

### 2.3 Learning Curve Generation
Learning curves help analyze how model performance scales with dataset size and confirm if the model benefits from more training data.
- **Methodology**:
  Use `sklearn.model_selection.learning_curve` with 5-fold cross-validation and 10 train sizes spaced linearly from 10% to 100%.
- **Plotting**:
  Plot training score and validation score (F1-score) along with standard deviation bands using `matplotlib`. Save the figure to `backend/learning_curves.png`.

---

## 3. Logical Consistency Verification Script Design

The backend uses a network graph (NetworkX) and an ML risk model to simulate event impacts and recommend actions (like placing barricades). We must verify the logical consistency of this simulator: **placing a barricade must strictly reduce the targeted road's congestion score**.

### 3.1 Simulator Modeling
1. **Road Network Graph**:
   Represent the city map as a directed or undirected graph $G = (V, E)$. Each edge $e \in E$ is a road segment with coordinates, a baseline weight (travel time), and a `congestion_score` (ranging from `1.0` to `10.0`).
2. **Event Impact**:
   An event at $(lat_{evt}, lon_{evt})$ with severity $S$ and impact radius $\sigma$ increases the congestion score of road segments $e$ within its vicinity:
   $$C_e^{\text{event}} = \min(10.0, C_e^{\text{baseline}} + S \times \exp\left(-\frac{d(e, \text{event})^2}{2\sigma^2}\right))$$
3. **Barricade Simulation**:
   - When a barricade is placed on or near the affected road segment, it blocks or diverts traffic.
   - We simulate this by:
     - **Routing Engine approach**: Removing the barricaded edge from routing or increasing its weight to infinity, forcing traffic flow onto alternate paths. The congestion score of the targeted road decreases as its traffic volume is diverted.
     - **Deterministic Discount approach**: Direct modeling where a barricade applied to a targeted road segment discounts the congestion score by a reduction factor $\delta \in (0, 1)$ (e.g. 40% reduction):
       $$C_e^{\text{barricaded}} = C_e^{\text{event}} \times (1 - \delta)$$

### 3.2 Python Verification Script Design
The verification script will construct a mock scenario (or load the actual backend routing graph) and test:
1. **Event Congestion Increase**: Congestion increases near the event location compared to baseline.
2. **Barricade Congestion Reduction**: Placing a barricade reduces congestion on the targeted road segment compared to the event-only scenario.
3. **Bounds Compliance**: Congestion scores always remain within `[1.0, 10.0]`.

Below is the proposed implementation of this verification script:

```python
import numpy as np
import networkx as nx
import pytest

def calculate_distance(coord1, coord2):
    # Quick Euclidean distance for local coordinates
    return np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

class SimulationEngine:
    def __init__(self, G):
        self.G = G.copy()
        
    def simulate(self, event_coords=None, barricade_coords=None, severity=5.0, radius=0.005, reduction=0.4):
        # 1. Reset to baseline
        for u, v, d in self.G.edges(data=True):
            d['congestion_score'] = 1.0
            
        if event_coords is None:
            return self.G
            
        # 2. Apply Event Congestion
        for u, v, d in self.G.edges(data=True):
            pos_u = self.G.nodes[u]['pos']
            pos_v = self.G.nodes[v]['pos']
            edge_midpoint = ((pos_u[0] + pos_v[0])/2, (pos_u[1] + pos_v[1])/2)
            
            dist = calculate_distance(edge_midpoint, event_coords)
            if dist < radius * 3: # Limit impact zone
                impact = severity * np.exp(-(dist**2) / (2 * radius**2))
                d['congestion_score'] = min(10.0, d['congestion_score'] + impact)
                
        # 3. Apply Barricade Congestion Reduction
        if barricade_coords is not None:
            for u, v, d in self.G.edges(data=True):
                pos_u = self.G.nodes[u]['pos']
                pos_v = self.G.nodes[v]['pos']
                edge_midpoint = ((pos_u[0] + pos_v[0])/2, (pos_u[1] + pos_v[1])/2)
                
                dist_to_barricade = calculate_distance(edge_midpoint, barricade_coords)
                if dist_to_barricade < 0.001: # Direct target matching
                    # Reduce congestion strictly
                    d['congestion_score'] = max(1.0, d['congestion_score'] * (1.0 - reduction))
                    
        return self.G

def test_logical_consistency():
    # Build a simple mock road network representing 4 junctions in Bengaluru
    G = nx.Graph()
    G.add_node("Junction_A", pos=(12.9716, 77.5946))
    G.add_node("Junction_B", pos=(12.9720, 77.5950))
    G.add_node("Junction_C", pos=(12.9710, 77.5940))
    G.add_node("Junction_D", pos=(12.9730, 77.5960))
    
    G.add_edge("Junction_A", "Junction_B", road_id="road_AB")
    G.add_edge("Junction_A", "Junction_C", road_id="road_AC")
    G.add_edge("Junction_B", "Junction_D", road_id="road_BD")
    G.add_edge("Junction_C", "Junction_D", road_id="road_CD")
    
    engine = SimulationEngine(G)
    
    # Coordinates of an event right on road_AB midpoint
    event_loc = ((12.9716 + 12.9720)/2, (77.5946 + 77.5950)/2)
    
    # 1. Baseline Run
    g_baseline = engine.simulate(event_coords=None, barricade_coords=None)
    c_baseline = g_baseline["Junction_A"]["Junction_B"]['congestion_score']
    assert c_baseline == 1.0, "Baseline congestion score should be 1.0"
    
    # 2. Event Run (no barricades)
    g_event = engine.simulate(event_coords=event_loc, barricade_coords=None)
    c_event = g_event["Junction_A"]["Junction_B"]['congestion_score']
    assert c_event > 1.0, "Event must increase congestion on the targeted road"
    
    # 3. Barricade Run (barricade placed at event location)
    g_barricade = engine.simulate(event_coords=event_loc, barricade_coords=event_loc)
    c_barricade = g_barricade["Junction_A"]["Junction_B"]['congestion_score']
    
    # Logical Consistency Assertions
    assert c_barricade < c_event, "Placing barricades must strictly reduce targeted road congestion scores!"
    assert c_barricade >= 1.0, "Congestion score must not drop below 1.0"
    assert c_event <= 10.0 and c_barricade <= 10.0, "Congestion scores must not exceed 10.0"
    
    print("Logical consistency verified successfully!")

if __name__ == "__main__":
    test_logical_consistency()
```
