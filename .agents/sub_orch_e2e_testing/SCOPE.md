# Scope: E2E Testing Track

## Architecture
- **E2E Testing Suite**: Run via `pytest tests/e2e/` from project root. Tests target the FastAPI backend (`/simulate_scenario`) and verify inputs/outputs/routing/prediction logic according to the specs.
- **Verification Strategy**: The tests are opaque-box, requirement-driven, validating that inputs are correctly bound-checked, outputs adhere to constraints, and the ML logic obeys the physical consistency rules (e.g. barricades reduce congestion).

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID |
|---|------|-------|-------------|--------|-----------------|
| M1 | Draft TEST_INFRA.md | Draft and publish TEST_INFRA.md | None | DONE | 459a9fc0-3ea8-4559-a3f3-d6f969907259 |
| M2 | Test Framework Setup & Helper | Create tests/e2e directory and shared test helpers (mock/client) | M1 | DONE | 8c26d6d2-c55c-4ba7-a63e-ae2891edbd11 |
| M3 | Tier 1-2 Tests | Write Tier 1 (Feature Coverage) and Tier 2 (Boundary) tests | M2 | IN_PROGRESS | bd4e4131-a993-479a-9124-1a12711c132d |
| M4 | Tier 3-4 Tests | Write Tier 3 (Cross-Feature) and Tier 4 (Real-World) tests | M3 | IN_PROGRESS | bd4e4131-a993-479a-9124-1a12711c132d |
| M5 | Test Run & Hardening | Verify all tests are running and fail with expected API status (404/405/etc.) | M4 | PLANNED | TBD |
| M6 | Publish TEST_READY.md | Publish TEST_READY.md at project root and finalize handoff | M5 | PLANNED | TBD |

## Interface Contracts
- See global PROJECT.md for backend request/response formats.
