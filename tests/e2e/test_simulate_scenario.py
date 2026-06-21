from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_simulate_scenario_endpoint_active():
    """Verify that a valid baseline request returns status code 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_simulate_scenario_structure_keys():
    """Verify that the response contains all required contract keys."""
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

def test_simulate_scenario_affected_roads_format():
    """Verify that the affected_roads list elements have the correct keys and types."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 0.8}
        ],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["affected_roads"], list)
    for road in data["affected_roads"]:
        assert "road_id" in road
        assert isinstance(road["road_id"], str)
        assert "coordinates" in road
        assert isinstance(road["coordinates"], list)
        for coord in road["coordinates"]:
            assert isinstance(coord, list)
            assert len(coord) == 2
            assert isinstance(coord[0], float) # longitude
            assert isinstance(coord[1], float) # latitude
        assert "congestion_score" in road
        assert isinstance(road["congestion_score"], float)

def test_simulate_scenario_recommended_actions_format():
    """Verify that recommended_actions list elements have the correct keys and types."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Accident",
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["recommended_actions"], list)
    for action in data["recommended_actions"]:
        assert "action_type" in action
        assert isinstance(action["action_type"], str)
        assert "latitude" in action
        assert isinstance(action["latitude"], float)
        assert "longitude" in action
        assert isinstance(action["longitude"], float)
        assert "description" in action
        assert isinstance(action["description"], str)

def test_simulate_scenario_headers_and_type():
    """Verify that the response returns correct application/json headers."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_simulate_scenario_empty_body_returns_422():
    """Verify that sending an empty JSON body {} returns 422 validation error."""
    response = client.post("/simulate_scenario", json={})
    assert response.status_code == 422

def test_simulate_scenario_none_body_returns_422():
    """Verify that sending a None request body returns 422 validation error."""
    response = client.post("/simulate_scenario", json=None)
    assert response.status_code == 422

def test_simulate_scenario_method_not_allowed():
    """Verify that attempting to GET or PUT on /simulate_scenario returns 405 Method Not Allowed."""
    response = client.get("/simulate_scenario")
    assert response.status_code == 405

def test_simulate_scenario_risk_score_capped_at_10():
    """Verify that the risk_score is capped at 10.0 even under extreme congestion inputs."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 1.0},
            {"latitude": 12.9720, "longitude": 77.5950, "density": 1.0},
            {"latitude": 12.9730, "longitude": 77.5960, "density": 1.0}
        ],
        "events": [
            {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"},
            {"latitude": 12.9720, "longitude": 77.5950, "event_cause": "Protest / Rally", "time_of_day": "Evening Peak"},
            {"latitude": 12.9730, "longitude": 77.5960, "event_cause": "Waterlogging", "time_of_day": "Morning Peak"}
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] <= 10.0

def test_simulate_scenario_risk_score_min_1():
    """Verify that the risk_score is at least 1.0, representing the minimum scale score."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_score"] >= 1.0
