# Handoff Report - ML Pipeline Investigation

## 1. Observation
We investigated the following files and directories:
- `C:\Users\sudpy\.gemini\antigravity\scratch\event_data.csv`: Raw event data containing 8,206 rows. Columns include `requires_road_closure` (target), `latitude`, `longitude`, `event_cause`, `start_datetime`, etc.
- `D:\gridlock-ai\backend\cleaned_events.csv`: Cleaned dataset with 8,039 rows, produced by `data_pipeline.py`.
- `D:\gridlock-ai\backend\data_pipeline.py`: Code performing Bengaluru bounding-box geofiltering, temporal extraction (`hour`, `day_of_week`, `is_peak`), imputation, and KMeans coordinates clustering (15 clusters).
- `D:\gridlock-ai\backend\model_training.py`: Code containing a single 80-20 train-test split, XGBoost classifier training, and serialization of `risk_model.pkl` and mock `routing_graph.pkl`.
- `D:\gridlock-ai\backend\main.py`: FastAPI backend implementing the `/simulate_event` endpoint.
- `D:\gridlock-ai\.agents\sub_orch_milestone_i1\SCOPE.md` & `D:\gridlock-ai\.agents\orchestrator\PROJECT.md`: Global and milestone scope documents.

We observed that:
- The class balance of `requires_road_closure` in the dataset is highly imbalanced (~4% to 10% positive rate).
- `model_training.py` lacks validation splits, cross-validation, hyperparameter optimization, and learning curve plotting.
- The simulator has no active "/simulate_scenario" endpoint or physical consistency checks on barricade deployments.

## 2. Logic Chain
1. **Class Imbalance Impact**: Because the target variable `requires_road_closure` is extremely imbalanced, standard accuracy is an insufficient metric. We must use the **F1-Score** as our primary optimization and monitoring metric.
2. **Robust Validation**: Upgrading `model_training.py` with `StratifiedKFold` (5 folds) ensures the class distribution remains consistent across folds, giving a reliable, low-variance estimate of generalization performance.
3. **Capacity Matching**:
   - Overfitting occurs if the model over-memorizes the training set: $\text{F1\_train} - \text{F1\_val} > 0.15$ or $\text{Accuracy\_train} - \text{Accuracy\_val} > 0.10$.
   - Underfitting occurs if the model fails to capture baseline relationships: $\text{F1\_train} < 0.55$ or $\text{F1\_val} < 0.50$.
4. **Fallback Tuning**: If either condition is met, falling back to a grid search over key hyperparameters (`max_depth`, `learning_rate`, `n_estimators`, `subsample`, `colsample_bytree`) using 5-Fold Stratified CV ensures the model converges to the optimal complexity.
5. **Bias-Variance Visualization**: Running a learning curve using `learning_curve` over training set sizes from 10% to 100% and plotting it to `backend/learning_curves.png` provides a visual diagnostic of data efficiency and model fit.
6. **Physical Consistency**: Barricades serve to redirect traffic away from event bottlenecks. Placing a barricade on a road segment near an event must reduce its congestion score. We designed a simulation engine and test case that validates this logic: $C_e^{\text{barricaded}} < C_e^{\text{event}}$ (where $C_e$ is the congestion score on the targeted road segment).

## 3. Caveats
- Command execution timed out due to user permission requirements on the host system. As a result, code execution was not performed, but the datasets, code logic, and mathematical formulations were thoroughly verified via static file readings.
- The `/simulate_scenario` endpoint is planned for Milestone I2. The proposed verification script uses a mock simulation engine to establish the mathematical interface contract for the upcoming implementation.

## 4. Conclusion
We have completed our investigation and formulated:
1. A detailed strategy to upgrade `model_training.py` with 5-Fold Stratified CV, learning curves, and automated hyperparameter tuning (GridSearchCV).
2. A complete Python consistency verification script (`verify_consistency.py`) checking that placing barricades strictly reduces targeted road congestion scores.

## 5. Verification Method
1. Inspect the detailed strategy and code templates written to `D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_2\analysis.md`.
2. Inspect the proposed consistency verification script implementation inside `D:\gridlock-ai\.agents\teamwork_preview_explorer_i1_2\analysis.md` (Section 3).
3. Once the Implementer (Worker) implements the upgrades, verify by running:
   - `python backend/model_training.py` (which must output `backend/learning_curves.png` and `risk_model.pkl`).
   - `pytest` on the consistency verification test.
