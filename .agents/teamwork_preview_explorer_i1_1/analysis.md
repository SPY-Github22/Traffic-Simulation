# Gridlock AI - ML Pipeline Analysis Report

## Executive Summary
This report presents findings from the investigation of the machine learning pipeline under `D:\gridlock-ai`, the raw event dataset at `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`, and our peer explorers' results. We have identified two critical feature-encoding mismatches between model training and online inference, as well as a broken test suite, and developed a complete plan for pipeline upgrades and logical consistency verification.

---

## 1. Raw Dataset and Preprocessing Pipeline Analysis

### 1.1 Dataset Examination
* **Raw Dataset Path**: `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`
* **Total Sample Size**: 8,206 rows (8,207 lines including header).
* **Target Column**: `requires_road_closure` (Boolean: `True` or `False`).
* **Class Balance**: 
  * Class balance is heavily skewed. In the raw dataset, approximately **12%** of events are marked as `True` (requiring closure), while **88%** are `False`.
  * Because of this imbalance, **Accuracy** is a deceptive evaluation metric (a naive model predicting `False` constantly would achieve ~88% accuracy). 
  * Instead, **F1-Score** (specifically optimized for the minority class `1`), **Precision**, and **Recall** must serve as the primary metrics for model evaluation and selection.
* **Important Columns**:
  * `id`: Unique identifier (e.g., `FKID000000`)
  * `event_type`: Categorical categorization (`unplanned` or `planned`)
  * `latitude`, `longitude`: Geospatial coordinate pairs
  * `event_cause`: Detailed incident cause (e.g., `vehicle_breakdown`, `tree_fall`, `accident`, `public_event`, `water_logging`)
  * `start_datetime`, `end_datetime`: Temporal timestamps
  * `priority`: Event severity/priority (`High`, `Medium`, `Low`)

### 1.2 Preprocessing Pipeline (`data_pipeline.py`)
The preprocessing pipeline cleans and saves the dataset to `D:\gridlock-ai\backend\cleaned_events.csv` (8,039 rows):
1. **Geospatial Filtering**: Coordinates outside Bengaluru's bounding box are dropped:
   $$12.7 < \text{latitude} < 13.2 \quad \text{and} \quad 77.4 < \text{longitude} < 77.8$$
   This filters out 167 rows (~2.03% of the dataset), representing high overall data quality.
2. **Temporal Extraction**: Parses `start_datetime` and extracts:
   * `hour` (0 to 23)
   * `day_of_week` (0 to 6, where 0 is Monday)
   * `is_peak`: Set to `1` if `hour` is in peak times (`8:00 AM - 11:59 AM` or `5:00 PM - 8:59 PM`), else `0`.
3. **Null Imputation**:
   * Missing `event_cause` is imputed as `'Unknown'`.
   * Missing `priority` is imputed as `'Medium'`.
4. **Target Mapping**: Casts boolean `requires_road_closure` values to integer `0` or `1`.
5. **Spatial Clustering**: Applies K-Means clustering with $k=15$ clusters on coordinate pairs (`latitude`, `longitude`) to group events into 15 functional zones (`zone_cluster` labeled `0` to `14`).

---

## 2. Critical Mismatch & Bug Analysis (Code Quality Issues)

During our static analysis of the codebase, we uncovered three critical discrepancies that will prevent the model from generalizing correctly in production and break the test suite.

### 2.1 Feature Mismatch 1: Event Type vs. Cause Encoding
* **In Training (`model_training.py:14`)**:
  ```python
  df['event_type_encoded'] = df['event_type'].astype('category').cat.codes
  ```
  The model is trained on `event_type` (which contains categories `planned` and `unplanned`). This encodes to `0` or `1`.
* **In Inference (`main.py:73-74`)**:
  ```python
  cause_map = {"Accident": 2, "Vehicle Breakdown": 1, "Protest / Rally": 3, "Waterlogging": 4}
  event_type_encoded = cause_map.get(event.event_cause, 2)
  ```
  During inference, the API maps `event_cause` (`Accident`, `Vehicle Breakdown`, etc.) to values `1` to `4` and passes this as `event_type_encoded` to the model.
* **Impact**: The model receives values `1`, `2`, `3`, `4` which have completely different semantics from the `0` and `1` values used in training, causing out-of-distribution predictions.
* **Resolution**: Standardize the encoding. Either train the model using `event_cause` mapped to integers using the same dictionary, or extract the true `event_type` from the event description/context in `main.py` and map it to `0` or `1` consistently.

### 2.2 Feature Mismatch 2: Spatial Zone Cluster Mappings
* **In Training (`data_pipeline.py:39-40`)**:
  ```python
  kmeans = KMeans(n_clusters=15, random_state=42, n_init=10)
  df['zone_cluster'] = kmeans.fit_predict(coords)
  ```
  The dataset clusters coordinates into 15 zones (values `0` to `14`) using K-Means.
* **In Inference (`main.py:70`)**:
  ```python
  zone_cluster = (int(event.latitude * 1000) ^ int(event.longitude * 1000)) % 10
  ```
  The API uses a coordinate hash modulo 10 (values `0` to `9`) to generate the zone cluster.
* **Impact**: The spatial partitions are completely misaligned, and the model will make predictions using garbage inputs for the spatial feature.
* **Resolution**: The K-Means model trained in `data_pipeline.py` must be saved to a file (e.g., `kmeans_model.pkl`) using `pickle`. At inference, `main.py` should load this model and call `kmeans_model.predict([[event.latitude, event.longitude]])` to obtain the correct cluster label.

### 2.3 Broken Test Suite (`test_main.py`)
* **In Test Suite (`test_main.py:18 & 32`)**:
  Both test functions send a single flat dictionary representing a single event payload directly:
  ```python
  response = client.post("/simulate_event", json=payload)
  ```
  However, the endpoint requires a batch request (`SimulationBatchRequest`) where the payload is wrapped in an `events` list:
  ```json
  {"events": [payload]}
  ```
  This causes the API to reject the requests with a `422 Unprocessable Entity` validation error in both cases.
* **Out-of-Bounds Test logic**:
  `test_simulate_event_out_of_bounds` asserts:
  ```python
  assert response.status_code == 422
  assert "Coordinates are out of bounds" in response.json()["detail"]
  ```
  But if a correct batch payload is sent with out-of-bounds coordinates, `main.py` simply skips the event (`continue`) and returns a `200 OK` status with empty lists:
  ```python
  for event in request.events:
      if not (12.7 < event.latitude < 13.2 and 77.4 < event.longitude < 77.8):
          continue
  ```
* **Resolution**:
  1. Wrap test payloads in `{"events": [payload]}`.
  2. Modify `test_simulate_event_out_of_bounds` to assert a `200 OK` response with `risk_score = 0.0` and no recommended actions, OR modify `main.py` to return an HTTP `400/422` error when input coordinate bounds are breached.

---

## 3. Strategy to Upgrade `model_training.py`

### 3.1 5-Fold Stratified Cross-Validation
To handle the class imbalance robustly, we will implement `StratifiedKFold` which preserves the target label distribution across folds.
* **Workflow**:
  1. Split features and target: `X` and `y`.
  2. Set up `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`.
  3. Across each fold, record: Accuracy, Precision, Recall, and F1-score.
  4. Print mean and standard deviation of all metrics.
  5. Fit final model on the entire dataset and save it to `risk_model.pkl`.

### 3.2 Automated Hyperparameter Tuning Fallback
We will monitor train/validation metrics to detect overfitting or underfitting programmatically and trigger tuning.
* **Detection Criteria**:
  * **Overfitting**: 
    $$\text{mean\_train\_f1} - \text{mean\_val\_f1} > 0.12$$
    (Over 12% absolute performance gap in F1-score).
  * **Underfitting**:
    $$\text{mean\_val\_f1} < 0.60$$
    (Validation F1-score fails to reach 60%).
* **Parameter Grid for Fallback**:
  If either condition is met, trigger `GridSearchCV` using `scoring='f1'` and:
  ```python
  param_grid = {
      'max_depth': [3, 5, 7],
      'learning_rate': [0.01, 0.1, 0.3],
      'n_estimators': [50, 100, 200],
      'min_child_weight': [1, 3, 5],
      'subsample': [0.8, 1.0]
  }
  ```

### 3.3 Learning Curve Generation
* Save the training and validation F1-scores plotted against dataset sizes (from 10% to 100% in 10 steps) to `backend/learning_curves.png`.
* Standard deviation bands should be plotted using `fill_between` in matplotlib.
* **Requirements update**: Add `matplotlib` to `backend/requirements.txt`.

---

## 4. Logical Consistency Verification

### 4.1 Congestion and Barricade Simulation Logic
* **Network Structure**: Cities are represented as directed graphs $G = (V, E)$. Edges represent roads with travel weights and traffic capacities.
* **Routing**: Shortest-path routing determines traffic flow volume $V_e$ on each edge.
* **Congestion Score**: Congestion on a road is computed as:
  $$\text{Score} = 1.0 + \min\left(9.0, \frac{\text{Volume}}{\text{Capacity}} \times \text{Weight}\right)$$
* **Event Impact**: Increases the weight/travel time of targeted edges, increasing congestion score.
* **Barricade Impact**: Removes the barricaded edge from routing, forcing traffic to detour.
* **Logical Axiom**: Placing barricades on or upstream of a congested road must strictly reduce targeted road congestion scores.

### 4.2 Implementation
We have written a complete logical consistency verification script at:
`D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_1\verify_consistency.py`

This script verifies:
1. **Accident Event Impact**: Congestion score on J1 -> J2 increases from 2.0 to 10.0 when an accident occurs.
2. **Direct Barricade Placement**: Placing a barricade on J1 -> J2 closes the road, reducing its active congestion to 1.0 (empty) and detouring traffic via J1 -> J4 -> J3.
3. **Upstream Detour Placement**: Placing a barricade upstream on J1 -> J2 detours traffic, reducing congestion on downstream bottleneck road J2 -> J3.
4. **Bounds Enforcement**: Scores are bounded strictly within $[1.0, 10.0]$.
