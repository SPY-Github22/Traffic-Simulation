from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_scenario_mode_baseline_success():
    """Verify that 'Baseline' scenario mode returns 200 and a valid structure."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "requires_road_closure" in data
    assert "affected_roads" in data
    assert "recommended_actions" in data

def test_scenario_mode_future_impact_success():
    """Verify that 'Future Impact' scenario mode returns 200 and a valid structure."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert isinstance(data["risk_score"], float)

def test_scenario_mode_optimized_strategy_success():
    """Verify that 'Optimized Strategy' scenario mode returns 200 and a valid structure."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert isinstance(data["risk_score"], float)

def test_scenario_mode_missing_returns_422():
    """Verify that missing the scenario_mode field returns a 422 validation error."""
    payload = {
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_scenario_mode_valid_structure_types():
    """Verify that all response fields have correct data types under normal Baseline mode."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["risk_score"], float)
    assert 1.0 <= data["risk_score"] <= 10.0
    assert isinstance(data["requires_road_closure"], float)
    assert 0.0 <= data["requires_road_closure"] <= 1.0
    assert isinstance(data["affected_roads"], list)
    assert isinstance(data["recommended_actions"], list)


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_scenario_mode_invalid_value_returns_422():
    """Verify that an invalid scenario mode name returns a 422 validation error."""
    payload = {
        "scenario_mode": "InvalidModeName",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_scenario_mode_empty_string_returns_422():
    """Verify that an empty string for scenario mode returns a 422 validation error."""
    payload = {
        "scenario_mode": "",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_scenario_mode_case_sensitivity_returns_422():
    """Verify that lowercase/uppercase variations of scenario modes return 422 (strict validation)."""
    payload = {
        "scenario_mode": "baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_scenario_mode_incorrect_type_returns_422():
    """Verify that passing an integer instead of a string returns a 422 validation error."""
    payload = {
        "scenario_mode": 123,
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_scenario_mode_none_returns_422():
    """Verify that passing None (null) for scenario mode returns a 422 validation error."""
    payload = {
        "scenario_mode": None,
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422
