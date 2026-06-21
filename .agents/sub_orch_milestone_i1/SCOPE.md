# Scope: Milestone I1 - ML Pipeline Upgrade

## Architecture
- **Data Source**: Astram dataset raw event data located at `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`.
- **Preprocessed Data**: Handled by `backend/data_pipeline.py`, yielding `cleaned_events.csv` with KMeans clustering model saved as `kmeans_model.pkl`.
- **Training and Evaluation**: Upgraded in `backend/model_training.py`. Group events into hour slots and engineer group-level features:
  1. `concurrent_event_count`: Number of events in the slot.
  2. `average_distance_between_events`: Geodesic average distance between coordinate pairs in the slot (using haversine formula).
  3. `cluster_density`: Maximum number of events in a single zone cluster in the slot.
- **Model Output**: XGBoost classifier predicting compound `requires_road_closure` probability saved to `risk_model.pkl`.
- **Inference**: Loaded by `backend/main.py`.

## Sub-Milestones / Tasks
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Data Pipeline Verification | Verify raw data fields, cleaning, and KMeans saving | None | DONE |
| 2 | Compounded Feature Engineering | Group events by hour slots and compute group-level features | M1 | IN_PROGRESS |
| 3 | 5-Fold Cross Validation | Implement stratified k-fold split and scoring on group-level dataset | M2 | PLANNED |
| 4 | Hyperparameter Tuning Fallback | Programmatically detect underfitting/overfitting and tune hyperparameters | M3 | PLANNED |
| 5 | Learning Curve Generation | Plot and save training/validation scores over dataset sizes | M4 | PLANNED |
| 6 | Consistency Verification | Verify that placing barricades reduces targeted road congestion | M5 | PLANNED |

## Interface Contracts
### `model_training.py` ↔ `risk_model.pkl`
- The trained classifier must export to `risk_model.pkl`.
- Feature ordering for prediction: `['concurrent_event_count', 'average_distance_between_events', 'cluster_density', 'hour', 'day_of_week', 'is_peak']`.
- Output must be an XGBClassifier model predicting compound probability of `requires_road_closure`.

