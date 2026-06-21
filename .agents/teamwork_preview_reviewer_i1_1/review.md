# Review Report — Milestone I1 ML Pipeline Upgrade

## Review Summary

**Verdict**: REQUEST_CHANGES

This review evaluates the code changes made in Milestone I1 for the Gridlock ML Simulation Upgrade. While the feature engineering, model training setup, cross-validation, and hyperparameter tuning fallback logic are correctly implemented, there are critical issues with the verification script (`verify_consistency.py`) and an operational gap regarding the absence of the trained K-Means model (`kmeans_model.pkl`) which triggers a feature-mismatch fallback in production inference.

---

## Findings

### Critical Finding 1: Broken Consistency Verification Script (`verify_consistency.py`)
- **What**: The script `verify_consistency.py` is logically broken and fails its own assertions when executed.
- **Where**: `backend/verify_consistency.py`, lines 70–120.
- **Why**: 
  1. In **Scenario 2**, the script introduces an event of severity `10.0` on road `J1 -> J2`. Since this road's weight increases to `12.0`, the shortest path routing algorithm immediately routes all traffic via the detour path `J1 -> J4 -> J3` (total weight `8.0`). As a result, the traffic volume on the targeted road `J1 -> J2` drops to `0`. Under the congestion formula, this drops its congestion score to `1.0`. The script then asserts:
     ```python
     assert scores_event[("J1", "J2")] > scores_base[("J1", "J2")]  # (1.0 > 3.0) -> False
     ```
     This assertion fails immediately, throwing an `AssertionError`.
  2. In **Scenario 4**, the detour barricade is placed upstream. Because of the same routing switch, both `scores_event_2[("J2", "J3")]` and `scores_mitigated_detour[("J2", "J3")]` have `0` volume and resolve to a score of `1.0`. The assertion:
     ```python
     assert scores_mitigated_detour[("J2", "J3")] < scores_event_2[("J2", "J3")]  # (1.0 < 1.0) -> False
     ```
     would also fail.
- **Suggestion**: The simulation needs to account for traffic routing behavior under congestion. The severity of the event should be small enough (e.g., `1.0` or `2.0`) so that the congested path remains the shortest path prior to mitigation, or the routing logic should model traffic assignment/equilibria instead of all-or-nothing shortest path.

### Major Finding 2: Missing `kmeans_model.pkl` & Feature Shift Fallback in `main.py`
- **What**: The trained K-Means model file `kmeans_model.pkl` does not exist in the repository or the backend directory.
- **Where**: `backend/main.py`, lines 27–30 & 105–109.
- **Why**: Since `kmeans_model.pkl` is missing, the backend API (`main.py`) falls back to predicting zone clusters using the coordinate XOR hash:
  ```python
  cluster = (int(event.latitude * 1000) ^ int(event.longitude * 1000)) % 10
  ```
  However, the model `risk_model.pkl` was trained on features generated using 15-cluster K-Means labels (0–14). The XOR hash maps coordinates to 10 clusters (0–9). This mismatch in cluster mapping results in a severe feature distribution shift for the `cluster_density` feature at inference time, rendering predictions inaccurate.
- **Suggestion**: Ensure that `model_training.py` runs to completion during the build phase to generate and save `kmeans_model.pkl` alongside `risk_model.pkl`.

### Minor Finding 3: Missing `joblib` Dependency in `requirements.txt`
- **What**: `joblib` is imported directly in `main.py` but is not listed in `requirements.txt`.
- **Where**: `backend/requirements.txt` and `backend/main.py`, line 9.
- **Why**: While `joblib` is transitively installed via `scikit-learn`, importing it directly without specifying it as a direct dependency in `requirements.txt` is poor dependency management and risks breakage if a future version of `scikit-learn` removes or replaces it.
- **Suggestion**: Add `joblib` explicitly to `backend/requirements.txt`.

### Minor Finding 4: Silent Fallbacks on Model Loading Failures
- **What**: If `risk_model.pkl` or `routing_graph.pkl` fails to load, `main.py` falls back silently to default values (0.5 road closure probability, 5.0 risk score).
- **Where**: `backend/main.py`, lines 21–30.
- **Why**: There is no logging or exception raising when these critical model files are missing, which makes configuration errors hard to detect.
- **Suggestion**: Add logging statements (e.g., using python's standard `logging` library) to log warnings when fallback logic or missing model files are detected.

---

## Verified Claims

- **Claim 1**: Batch schema coordinate validation (HTTP 422 error on out-of-bounds) in `main.py`.
  - *Method*: Static analysis of `main.py` (lines 91-94) and `test_main.py` (lines 25-34).
  - *Status*: **PASS**. The coordinate range checks are correctly implemented, raising an HTTP 422 error if any event is out of bounds, and the corresponding unit test verifies this behavior.
- **Claim 2**: Compounded batch feature engineering in training.
  - *Method*: Static analysis of `model_training.py` (lines 41-77).
  - *Status*: **PASS**. Grouping is performed by rounding to the nearest hour slot, and compound features (`concurrent_event_count`, `average_distance_between_events` via Haversine formula, and `cluster_density`) are correctly calculated.
- **Claim 3**: 5-Fold Stratified CV and GridSearchCV fallback.
  - *Method*: Static analysis of `model_training.py` (lines 86-189).
  - *Status*: **PASS**. Stratified K-Fold is correctly set up, scores are tracked, and `GridSearchCV` triggers on underfitting/overfitting thresholds.
- **Claim 4**: Learning curve plotting.
  - *Method*: Static analysis of `model_training.py` (lines 196-234).
  - *Status*: **PASS**. Plotting is performed in a headless environment and saved to `backend/learning_curves.png`.

---

## Coverage Gaps

- **Transitive Dependency Verification** — Risk Level: **Low** — Recommendation: Add `joblib` explicitly to requirements.
- **Inference-Time Model Performance** — Risk Level: **High** — Recommendation: Fix the missing `kmeans_model.pkl` artifact.

---

## Unverified Items

- **Actual Model Training Run** — Reason: Command execution timed out due to lack of interactive user permission approvals in the current sandbox environment.
- **Mock Routing Graph Integration in API** — Reason: Relies on runtime model loading which could not be executed.

---

## Adversarial / Challenge Review

### 1. Assumption Stress-Testing
- **Assumption challenged**: Shortest path routing behaves monotonically with event severity in `verify_consistency.py`.
- **Attack scenario**: High event severity (`10.0`) forces all traffic to detour immediately, dropping targeted congestion to `1.0` (uncongested base score + 0 volume).
- **Blast radius**: The verification script fails to compile or run, breaking continuous integration.
- **Mitigation**: Adjust the event severity down to `1.0` or `2.0` so that the shortest path does not switch until a barricade is explicitly placed.

### 2. Edge Case Mining
- **Edge case**: Single event batches sent to `/simulate_event`.
- **Behavior**: If `len(request.events) == 1`, `average_distance_between_events` returns `0.0`. `cluster_density` is `1`. This is handled correctly by the code.
- **Edge case**: Empty event list in batch.
- **Behavior**: Handled correctly in `main.py` (lines 88-89): raises HTTP 400.
