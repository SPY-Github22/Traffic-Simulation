## 2026-06-20T18:19:47Z

Draft and write the D:\gridlock-ai\TEST_INFRA.md file for the Gridlock Advanced ML Simulation Upgrade project.

Make sure to include the following sections exactly:

# E2E Test Infra: Gridlock Advanced ML Simulation Upgrade

## Test Philosophy
- Opaque-box, requirement-driven. No dependency on implementation design.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.

## Feature Inventory
| # | Feature | Source (requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Scenario Mode Selection | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 2 | Barricade Placement | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 3 | Crowd Placement & Density | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| 4 | Historical/Simulated Events | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 5 | Congestion Prediction Endpoint (`/simulate_scenario`) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 6 | Bengaluru Geometry & Routing | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| 7 | Barricade Consistency (Congestion Reduction Rule) | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ |

## Test Architecture
- Test runner: `pytest` from the project root directory.
- Test case format: Automated Python test files located in `tests/e2e/`.
- Directory layout:
  - `tests/e2e/test_scenario_mode.py`
  - `tests/e2e/test_barricades.py`
  - `tests/e2e/test_crowds.py`
  - `tests/e2e/test_events.py`
  - `tests/e2e/test_simulate_scenario.py`
  - `tests/e2e/test_routing.py`
  - `tests/e2e/test_consistency.py`
  - `tests/e2e/test_combinations.py` (Tier 3)
  - `tests/e2e/test_real_world.py` (Tier 4)

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Baseline Congestion Mapping | F5, F6 | Low |
| 2 | Rush Hour Event with Crowd Congestion | F3, F4, F5 | Medium |
| 3 | Road Blockage and Alternative Route Guidance | F2, F5, F6 | Medium |
| 4 | Crowd and Event Dynamic Response | F3, F4, F5, F6 | High |
| 5 | Optimized Strategy Barricade Verification | F1, F2, F3, F4, F7 | High |

## Coverage Thresholds
- Tier 1: 35 test cases (5 per feature)
- Tier 2: 35 test cases (5 per feature)
- Tier 3: 7 test cases (covering major feature pairs)
- Tier 4: 5 realistic application scenarios
- **Total**: 82 test cases

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When done, write progress.md in your working directory and send a completion message with the path of the written file.

## 2026-06-20T18:23:10Z

Implement the E2E test suite in the `tests/e2e` directory based on the spec in `D:\gridlock-ai\TEST_INFRA.md`.

You need to:
1. Create the `tests/` and `tests/e2e/` directories.
2. Create `tests/conftest.py` that adds the `backend` directory to `sys.path` so that tests can import `from main import app` cleanly.
3. Write the 9 test files inside `tests/e2e/` matching the directory layout:
   - `test_scenario_mode.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_barricades.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_crowds.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_events.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_simulate_scenario.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_routing.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_consistency.py` (Tier 1: 5 tests, Tier 2: 5 tests)
   - `test_combinations.py` (Tier 3: 7 tests)
   - `test_real_world.py` (Tier 4: 5 scenarios)

All tests must use `pytest` and `fastapi.testclient.TestClient(app)` to send requests to the `/simulate_scenario` endpoint, validating status codes, JSON structures, bounds, values, and consistency rules as specified.
Wait, since `/simulate_scenario` is not implemented in the backend yet, the tests should currently fail (e.g. return 404 or 422 if bounds check catches it). This is expected. Do not modify the backend code — only write the tests in the `tests/` folder.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When completed, verify that the files are created and try running pytest from the project root using a build/test run command. Document the output and send a completion message back.

