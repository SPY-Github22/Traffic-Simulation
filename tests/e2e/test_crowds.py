from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_crowd_single_placement():
    """Verify that placing a single crowd source with valid density returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 0.5}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_crowd_multiple_placements():
    """Verify that placing multiple crowd sources with varying densities returns 200."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 0.2},
            {"latitude": 12.9730, "longitude": 77.5960, "density": 0.7},
            {"latitude": 12.9750, "longitude": 77.5980, "density": 0.9}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_crowd_empty_list():
    """Verify that sending an empty crowds list returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_crowd_density_extreme_bounds_valid():
    """Verify that crowd density exactly at 0.0 and 1.0 boundary limits returns 200."""
    payload1 = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.0}],
        "events": []
    }
    response1 = client.post("/simulate_scenario", json=payload1)
    assert response1.status_code == 200

    payload2 = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 1.0}],
        "events": []
    }
    response2 = client.post("/simulate_scenario", json=payload2)
    assert response2.status_code == 200

def test_crowds_valid_response_types():
    """Verify response payload structure and value constraints when crowds are specified."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.6}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["risk_score"], float)
    assert 1.0 <= data["risk_score"] <= 10.0
    assert isinstance(data["requires_road_closure"], float)
    assert 0.0 <= data["requires_road_closure"] <= 1.0


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_crowd_density_underflow_returns_422():
    """Verify that a crowd density less than 0.0 (e.g., -0.1) returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": -0.1}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_crowd_density_overflow_returns_422():
    """Verify that a crowd density greater than 1.0 (e.g., 1.01 or 1.5) returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 1.01}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_crowd_latitude_out_of_bounds_returns_422():
    """Verify that a crowd source placed outside Bengaluru latitude limits returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.5, "longitude": 77.5946, "density": 0.5}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_crowd_missing_density_returns_422():
    """Verify that a crowd object missing the density field returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_crowd_invalid_density_type_returns_422():
    """Verify that passing a string value for density returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": "high"}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422
