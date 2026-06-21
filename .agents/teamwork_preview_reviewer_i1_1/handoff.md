# Handoff Report — Milestone I1 ML Pipeline Upgrade Review

## 1. Observation
- File paths reviewed:
  - `backend/requirements.txt` (lines 1-11)
  - `backend/data_pipeline.py` (lines 1-63)
  - `backend/model_training.py` (lines 1-274)
  - `backend/main.py` (lines 1-161)
  - `backend/test_main.py` (lines 1-36)
  - `backend/verify_consistency.py` (lines 1-123)
- Direct observation from `D:\gridlock-ai\backend\verify_consistency.py`:
  - Line 82: `events = {("J1", "J2"): 10.0}`
  - Line 83: `scores_event = sim.calculate_congestion_scores(events=events)`
  - Line 89: `assert scores_event[("J1", "J2")] > scores_base[("J1", "J2")], "Event should increase congestion"`
  - Line 107: `events_2 = {("J2", "J3"): 10.0}`
  - Line 117: `assert scores_mitigated_detour[("J2", "J3")] < scores_event_2[("J2", "J3")], "Detour barricade should reduce congestion on targeted road J2-J3"`
- Direct observation from `D:\gridlock-ai\backend\main.py`:
  - Lines 105-109:
    ```python
    if kmeans_model:
        cluster = int(kmeans_model.predict([[event.latitude, event.longitude]])[0])
    else:
        cluster = (int(event.latitude * 1000) ^ int(event.longitude * 1000)) % 10
    ```
- Direct observation from directory search:
  - `find_by_name` for `kmeans_model.pkl` in `D:\gridlock-ai` returned 0 results.
  - `list_dir` for `D:\gridlock-ai\backend` verified that `kmeans_model.pkl` is absent, while `risk_model.pkl` and `routing_graph.pkl` are present.

## 2. Logic Chain
- Step 1: In `verify_consistency.py` (Observation 1), an event of severity 10.0 is applied to `J1 -> J2`. Since this road's weight increases from 2.0 to 12.0, the total path weight of `J1 -> J2 -> J3` becomes 14.0, which exceeds the weight of the alternative path `J1 -> J4 -> J3` (weight 8.0).
- Step 2: The shortest path algorithm `nx.shortest_path(..., weight="weight")` immediately detours all 100 simulated vehicles via the alternative path, reducing the traffic volume on the targeted road `J1 -> J2` to 0.
- Step 3: A traffic volume of 0 on `J1 -> J2` causes the congestion formula `1.0 + min(9.0, (vol / cap) * base_w)` to resolve to `1.0`.
- Step 4: The assertion `scores_event[("J1", "J2")] > scores_base[("J1", "J2")]` compares the new score (1.0) with the base score (3.0), which evaluates to `1.0 > 3.0` (False). Thus, running `verify_consistency.py` will fail with an `AssertionError` at line 89.
- Step 5: In `main.py` (Observation 2), the absence of `kmeans_model.pkl` (Observation 3) activates the XOR hash fallback. Since the XOR hash generates labels 0-9 and K-Means generates labels 0-14, the calculated `cluster_density` feature experiences a distribution shift at inference compared to training.
- Step 6: Therefore, the model's accuracy will degrade under fallback conditions, and the verification script is broken.

## 3. Caveats
- Command execution timed out due to the sandbox's requirement for interactive user approval of CLI runs. Validation of code execution was performed purely via static analysis and logical step tracing.
- We assumed that `risk_model.pkl` was trained in a prior stage using features derived from KMeans clusters (0-14), as specified in `model_training.py` and `data_pipeline.py`.

## 4. Conclusion
- The changes made in Milestone I1 correct the coordinate validation, batch schema inputs, and model cross-validation setup, but fail on verification correctness. The validation script `verify_consistency.py` is broken and fails on run, and `kmeans_model.pkl` is missing, causing a feature shift at inference. A verdict of **REQUEST_CHANGES** is issued.

## 5. Verification Method
1. Run the verification script:
   `python backend/verify_consistency.py`
   *Expected Failure*: Script throws an `AssertionError` on line 89.
   *Verification of Fix*: Lower the event severity in lines 82 and 107 to `1.0` or `2.0`, and re-run the script. It should run to completion and print:
   `All logical consistency checks passed successfully!`
2. Verify model training output:
   `python backend/model_training.py`
   *Expected output*: File `backend/kmeans_model.pkl` should be created, and the fallback path in `main.py` should no longer trigger.
