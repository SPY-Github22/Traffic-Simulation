from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# Bounding box for Bengaluru: 12.7 < lat < 13.2, 77.4 < lon < 77.8

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_barricade_single_placement():
    """Verify that placing a single barricade in Bengaluru bounds returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_barricade_multiple_placements():
    """Verify that placing multiple barricades in Bengaluru bounds returns 200."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946},
            {"latitude": 12.9730, "longitude": 77.5960},
            {"latitude": 12.9750, "longitude": 77.5980}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_barricade_empty_list():
    """Verify that sending an empty barricades list returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_barricade_valid_edge_coordinates():
    """Verify that coordinates near the Bengaluru boundary edges (but inside) return 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": 12.71, "longitude": 77.41},
            {"latitude": 13.19, "longitude": 77.79}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_barricades_validates_required_fields():
    """Verify that the response has all required fields when barricades are placed."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946}
        ],
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


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_barricade_latitude_out_of_bounds():
    """Verify that a barricade with latitude outside Bengaluru bounds returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": 14.5, "longitude": 77.5946}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_barricade_longitude_out_of_bounds():
    """Verify that a barricade with longitude outside Bengaluru bounds returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": 12.9716, "longitude": 70.5}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_barricade_missing_longitude_field():
    """Verify that a barricade object missing the longitude field returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": 12.9716}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_barricade_invalid_coordinate_types():
    """Verify that passing non-float values for barricade coordinates returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": "12.9716", "longitude": "77.5946"}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_barricade_none_coordinate_values():
    """Verify that passing null (None) values for barricade coordinates returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [
            {"latitude": None, "longitude": 77.5946}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422
