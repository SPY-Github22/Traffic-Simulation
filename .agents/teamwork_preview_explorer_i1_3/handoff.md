# Handoff Report — ML Pipeline Explorer 3

## 1. Observation
- **Raw Dataset**:
  - Path: `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`
  - Total Lines: `8207` (including header).
  - Target Column: `requires_road_closure` is boolean (`True` or `False`). Looking at lines 1-50, ~12% are `True`.
- **Preprocessed Dataset**:
  - Path: `D:\gridlock-ai\backend\cleaned_events.csv`
  - Total Lines: `8040` (including header).
  - Features added: `hour`, `day_of_week`, `is_peak`, `zone_cluster`.
  - Target variable converted to integer (`1` or `0`).
- **Data Pipeline**:
  - Path: `D:\gridlock-ai\backend\data_pipeline.py`
  - Output path in script (line 48): `output_file = r'C:\Users\sudpy\.gemini\antigravity\scratch\gridlock-ai\backend\cleaned_events.csv'`.
  - Functional zones (line 39): `kmeans = KMeans(n_clusters=15, random_state=42, n_init=10)`.
  - Peak hours definition (line 23): `df['is_peak'] = df['hour'].apply(lambda x: 1 if (8 <= x <= 11) or (17 <= x <= 20) else 0)`.
- **Model Training**:
  - Path: `D:\gridlock-ai\backend\model_training.py`
  - Features trained (lines 16-17): `X = df[['hour', 'day_of_week', 'is_peak', 'zone_cluster', 'event_type_encoded']]`.
  - Evaluation (line 19): `X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)`.
  - Model type (line 22): `xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)`.
- **Backend Simulation**:
  - Path: `D:\gridlock-ai\backend\main.py`
  - Endpoint (line 55): `@app.post("/simulate_event", response_model=EventSimulationResponse)`.
  - Routing Graph (line 17): loaded as `routing_graph.pkl` but not used for pathfinding or congestion calculations.
- **Dependencies**:
  - Path: `D:\gridlock-ai\backend\requirements.txt`
  - Observation: `matplotlib` is missing.

## 2. Logic Chain
- **Raw Data & Preprocessing**:
  - Raw dataset has 8,206 data rows. Filtering drops 167 rows (2.03%) due to coordinates bounds or missing start datetime. The remaining 8,039 rows are saved in `cleaned_events.csv`.
- **Model Upgrades**:
  - Standard train/test splits are prone to high variance on imbalanced datasets. Stratified 5-Fold Cross-Validation should be implemented to ensure class distributions are preserved.
  - Overfitting/Underfitting can be programmatically detected using train-to-validation F1-score comparisons. Underfitting is defined as `val_f1 < 0.60` and overfitting as `mean_train_f1 - mean_val_f1 > 0.12`. Detection triggers tuning fallback via `GridSearchCV` over parameters (`max_depth`, `learning_rate`, `n_estimators`, `min_child_weight`, `subsample`).
  - Learning curves are generated using `sklearn.model_selection.learning_curve` and saved to `backend/learning_curves.png`. This requires adding `matplotlib` to `requirements.txt`.
- **Barricade Simulation & Verification**:
  - Currently, `main.py` has no `/simulate_scenario` endpoint and does not calculate edge-by-edge congestion scores or run routing. Barricades are only recommendatory.
  - To test future `/simulate_scenario` logic (Milestone I2), we designed a verification script `verify_consistency.py` inside our folder. It models traffic routing over a directed NetworkX graph, computes edge congestion based on volume-to-capacity ratios, and uses assertions to verify that:
    1. Placing a barricade directly on a road closes it, dropping its active congestion score to 0.0.
    2. Placing a barricade upstream detours traffic, reducing the congestion score of the targeted road segment.

## 3. Caveats
- Command executions (`run_command`) timed out because the user was not active. All analysis is derived from read-only inspection of the files and codebases.
- The actual implementation of the simulation model for `/simulate_scenario` must match the assertions defined in the proposed verification script.

## 4. Conclusion
The machine learning pipeline is ready for upgrades. Cross-validation, automated tuning fallback, and learning curves can be safely added to `model_training.py` (with the addition of `matplotlib` to requirements).
A logical consistency test script has been designed and saved to `D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_3\verify_consistency.py` to verify routing detours and congestion reduction in Milestone I2.

## 5. Verification Method
- **To test the verification script**: Run `python D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_3\verify_consistency.py`. It should print all scenarios and output `All logical consistency checks passed successfully!`.
- **Files to inspect**:
  - `D:\gridlock-ai\backend\requirements.txt` (to verify addition of `matplotlib`).
  - `D:\gridlock-ai\backend\model_training.py` (after implementation).
  - `D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_3\analysis.md`.
