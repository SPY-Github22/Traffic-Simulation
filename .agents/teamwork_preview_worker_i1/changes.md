# Changes Summary - Milestone I1

## requirements.txt
- Added `matplotlib` library for generating learning curve plots.

## backend/data_pipeline.py
- Updated the pipeline to save the trained K-Means model to `kmeans_model.pkl` in the output directory.
- Updated pathing to be robust and dynamically determined relative to the file location.

## backend/model_training.py
- Updated data loading to import and run `clean_data` from `data_pipeline.py` to ensure the raw dataset (`event_data.csv`) is cleaned.
- Implemented compound event feature engineering:
  - Rounded `start_datetime` to the nearest hour slot to group concurrent events.
  - Engineered group-level features: `concurrent_event_count`, `average_distance_between_events` (using Haversine geodesic distance), `cluster_density` (maximum events in a single zone cluster), and temporal features (`hour`, `day_of_week`, `is_peak` for the slot).
  - Defined the group-level target variable `requires_road_closure` (1 if at least one event in the group has `requires_road_closure == 1`, else 0).
- Implemented 5-Fold Stratified Cross-Validation on the engineered group features to evaluate model performance (tracking Accuracy, Precision, Recall, and F1-score).
- Added programmatic underfitting and overfitting checks:
  - Underfitting trigger: mean validation F1-score < 0.60
  - Overfitting trigger: mean training F1-score - mean validation F1-score > 0.12
- Configured automated hyperparameter tuning fallback via `GridSearchCV` with Stratified 5-Fold CV over the parameter grid:
  - `max_depth`: `[3, 5, 7]`
  - `learning_rate`: `[0.01, 0.1, 0.3]`
  - `n_estimators`: `[50, 100, 200]`
  - `min_child_weight`: `[1, 3, 5]`
  - `subsample`: `[0.8, 1.0]`
- Plotted learning curves using F1-score on train/val sets over sizes from 10% to 100% and saved to `backend/learning_curves.png`.
- Saved the final trained model to `backend/risk_model.pkl` and mock routing graph to `backend/routing_graph.pkl`.

## backend/main.py
- Updated model loading (`risk_model.pkl`, `routing_graph.pkl`, `kmeans_model.pkl`) to resolve absolute paths relative to the `main.py` directory.
- Updated the `/simulate_event` endpoint to validate input event coordinates and immediately raise an HTTP 422 error if any coordinate is out of bounds.
- Refactored the endpoint to construct group-level features (`concurrent_event_count`, `average_distance_between_events`, `cluster_density`, `hour`, `day_of_week`, `is_peak`) dynamically from the batch of input events, predict compound road closure probability natively using the updated XGBoost model, set the compound risk score, and return recommended actions if the closure probability exceeds 0.5.

## backend/test_main.py
- Updated test payload inputs to wrap individual event requests in `{"events": [payload]}` to conform to the `SimulationBatchRequest` batch schema.

## backend/verify_consistency.py
- Created a logical consistency verification script utilizing a NetworkX directed graph simulation to verify traffic volume routing, congestion score boundary constraints `[1.0, 10.0]`, direct barricade mitigation effectiveness, and detour mitigation upstream behavior.
