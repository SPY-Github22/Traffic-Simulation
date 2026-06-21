# Gridlock Advanced ML Simulation Upgrade Plan

## Overview
This plan governs the development of interactive visual placement features, an advanced classical ML predictive backend, and robust training/evaluation pipelines for Gridlock AI.

## Execution Tracks

### Track 1: E2E Testing Track (Parallel)
- **Agent**: E2E Testing Orchestrator (`teamwork_preview_orchestrator` / `self`)
- **Objective**: Design, build, and publish a comprehensive, opaque-box E2E test suite covering Tiers 1-4.
- **Output**: `TEST_INFRA.md` and `TEST_READY.md`.

### Track 2: Implementation Track (Sequential Milestones)
- **Agent**: Implementation Sub-orchestrators (spawned per milestone)
- **Milestones**:
  1. **Milestone I1: ML Pipeline Upgrade**
     - Task: Build robust training and evaluation pipeline on the Astram dataset (`event_data.csv`). Implement 5-Fold CV, overfitting detection, hyperparameter tuning grid search fallback, and learning curves.
  2. **Milestone I2: "What-If" Simulation Backend**
     - Task: Upgrade the FastAPI backend. Implement `/simulate_scenario` endpoint, routing engine using `networkx` on `routing_graph.pkl` mapping zones to Bangalore road geometries, and deterministic congestion reduction checks for barricades.
  3. **Milestone I3: Frontend Interactive Map & Scenario HUD**
     - Task: Build `deck.gl` drag/drop interactive map layer, scenario HUD with Three-State simulation mode, and a highly polished dark-theme UI.
  4. **Milestone I4: Integration & Adversarial Hardening (Final Milestone)**
     - Task: Verify implementation against 100% of E2E tests from Track 1 (Tiers 1-4). Perform Tier 5 adversarial white-box coverage hardening. Run Forensic Audit checks.

## Verification & Integrity
- All milestones are gated by build/test verification, reviewer confirmation, and Forensic Audit (`teamwork_preview_auditor`).
- Zero-tolerance for hardcoded test results, facade implementations, or bypassed verification.
