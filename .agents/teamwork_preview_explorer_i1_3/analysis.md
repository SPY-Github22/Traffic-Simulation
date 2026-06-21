# Analysis Report — ML Pipeline Upgrade & Verification

## 1. Raw Dataset and Preprocessing Pipeline Analysis

### Raw Dataset (`event_data.csv`)
- **Location**: `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`
- **Total Records**: 8,206 rows (8,207 lines including header)
- **File Size**: ~4,020,472 bytes (~3.83 MB)
- **Columns**: 46 columns total. Important ones include:
  - `id`: unique identifier (e.g., `FKID000000`)
  - `event_type`: categorical, primarily `unplanned` or `planned`
  - `latitude`, `longitude`: coordinate pairs (geospatial indicators for incident site)
  - `event_cause`: categorical cause (e.g., `vehicle_breakdown`, `tree_fall`, `accident`, `public_event`, `water_logging`, `pot_holes`, `construction`)
  - `requires_road_closure`: boolean target column (`True` / `False`) indicating whether the incident requires closure of the road.
  - `start_datetime`, `end_datetime`: temporal timestamps
  - `priority`: categorical priority (`High`, `Medium`, `Low`)
- **Class Balance**: 
  - An initial scan of the raw dataset indicates a significant class imbalance: `requires_road_closure` is `False` in ~85-90% of cases, and `True` in ~10-15% of cases. 
  - This imbalance makes accuracy a deceptive metric; F1-score and Precision/Recall are critical for evaluation.

### Preprocessing Pipeline (`data_pipeline.py`)
The pipeline processes raw data into `cleaned_events.csv` (saved in `D:\gridlock-ai\backend\cleaned_events.csv` with 8,039 rows):
1. **Geospatial Cleaning**: Drops rows missing coordinates and filters for the Bengaluru bounding box: `(latitude > 12.7) & (latitude < 13.2) & (longitude > 77.4) & (longitude < 77.8)`. 167 rows (about 2.03% of data) are filtered out, demonstrating high geospatial data quality.
2. **Temporal Feature Extraction**: Converts `start_datetime` to datetime objects and extracts:
   - `hour` (0-23)
   - `day_of_week` (0-6, where 0 is Monday)
   - `is_peak` (1 if hour is 8-11 or 17-20, else 0)
3. **Imputation & Type Casting**:
   - Missing `event_cause` imputed as `'Unknown'`.
   - Missing `priority` imputed as `'Medium'`.
   - Converts `requires_road_closure` to integer (`1` or `0`).
4. **Functional Zone Clustering**: Applies `KMeans` with `n_clusters=15` on `[latitude, longitude]` coordinates to map events to 15 functional traffic zones/clusters in Bengaluru.

---

## 2. ML Pipeline Upgrade Strategy (`model_training.py`)

The current training script uses a simple 80/20 train/test split and trains a single XGBoost Classifier without hyperparameter tuning or visualization. We propose the following upgrades:

### A. 5-Fold Stratified Cross-Validation
- **Rationale**: Since the dataset exhibits class imbalance (approx. 12% positive class), we must use `StratifiedKFold` to ensure each fold has an identical class distribution.
- **Implementation**:
  ```python
  from sklearn.model_selection import StratifiedKFold
  import numpy as np

  skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
  fold_metrics = {'accuracy': [], 'precision': [], 'recall': [], 'f1': []}
  
  for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
      X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
      y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]
      
      model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
      model.fit(X_train_fold, y_train_fold)
      
      preds = model.predict(X_val_fold)
      # Calculate metrics for fold...
  ```
- **Final Model Saving**: After cross-validation, the final model should be trained on the *entire* dataset with the best hyperparameters and saved to `risk_model.pkl`.

### B. Automated Hyperparameter Tuning Fallback
- **Trigger Criteria**:
  - **Overfitting**: `mean_train_f1 - mean_val_f1 > 0.12` (over 12% absolute difference in F1-score).
  - **Underfitting**: `mean_val_f1 < 0.60` (validation F1-score below baseline performance).
- **Tuning Method**: Trigger `GridSearchCV` programmatically when either condition is met.
- **Parameter Grid**:
  ```python
  param_grid = {
      'max_depth': [3, 5, 7],
      'learning_rate': [0.01, 0.1, 0.3],
      'n_estimators': [50, 100, 200],
      'min_child_weight': [1, 3, 5],
      'subsample': [0.8, 1.0]
  }
  ```
- **Fallback Execution**:
  ```python
  if is_overfitting or is_underfitting:
      print("[WARNING] Overfitting/Underfitting detected. Triggering automated tuning...")
      grid_search = GridSearchCV(
          estimator=xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42),
          param_grid=param_grid,
          cv=5,
          scoring='f1',
          n_jobs=-1
      )
      grid_search.fit(X, y)
      best_model = grid_search.best_estimator_
      # Save best_model to risk_model.pkl
  ```

### C. Learning Curve Generation
- **Requirement**: Save a plot representing the model's F1-score performance against the volume of training data to `backend/learning_curves.png`.
- **Implementation**:
  ```python
  from sklearn.model_selection import learning_curve
  import matplotlib.pyplot as plt

  train_sizes, train_scores, val_scores = learning_curve(
      model, X, y, cv=5, scoring='f1', train_sizes=np.linspace(0.1, 1.0, 10), n_jobs=-1
  )
  
  train_mean = np.mean(train_scores, axis=1)
  train_std = np.std(train_scores, axis=1)
  val_mean = np.mean(val_scores, axis=1)
  val_std = np.std(val_scores, axis=1)
  
  plt.figure(figsize=(10, 6))
  plt.plot(train_sizes, train_mean, label='Training F1-score', color='blue', marker='o')
  plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color='blue')
  plt.plot(train_sizes, val_mean, label='Validation F1-score', color='green', marker='s')
  plt.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color='green')
  
  plt.title('Learning Curves (XGBoost Classifier)')
  plt.xlabel('Training Set Size')
  plt.ylabel('F1-Score')
  plt.legend(loc='best')
  plt.grid(True)
  plt.savefig('backend/learning_curves.png', dpi=300, bbox_inches='tight')
  plt.close()
  ```
- **Note**: `matplotlib` is not in `backend/requirements.txt` and must be added.

---

## 3. Logical Consistency Verification

### Current Backend State
- `backend/main.py` contains `/simulate_event` which calculates a generic `risk_score` and `requires_road_closure` using the ML model.
- If the risk of road closure is above 0.5, it appends a "Barricade" recommendation.
- However, the backend does *not* currently simulate the dynamic effects of barricades on traffic flow, nor does it calculate edge-by-edge congestion scores. The graph `routing_graph.pkl` is loaded but never used for path-finding.
- The `/simulate_scenario` endpoint is planned for Milestone I2.

### Design of the Logical Consistency Script
To verify the logical consistency of traffic routing and barricade simulation, the script must verify the following axiom:
> **Placing barricades on or upstream of a congested road strictly reduces targeted road congestion scores.**

1. **Simulator Modeling**:
   - Represents the road network as a NetworkX directed graph.
   - Computes travel time/congestion as `base_weight * (traffic_volume / capacity)`.
   - Simulates routing using shortest-path calculations between key junctions.
   - Events (e.g. Accidents) increase the travel cost (weight) of affected roads, causing them to show high congestion.
   - Barricades close specific roads by removing them from the routing graph.
2. **Consistency Assertions**:
   - **Direct Closure**: Placing a barricade directly on the congested road closes it, forcing all traffic to detour. The active congestion on the closed road must fall to 0.0 (or a baseline minimum).
   - **Detour Routing**: Placing a barricade upstream detours traffic before it enters the congested road. The traffic volume and congestion score on the targeted congested road must drop.
3. **Verification Script Location**: `D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_3\verify_consistency.py`
