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
