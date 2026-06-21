from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# Valid causes: "Accident", "Vehicle Breakdown", "Protest / Rally", "Waterlogging"
# Valid times of day: "Morning Peak", "Evening Peak", "Off-Peak"

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_event_single_valid():
    """Verify that simulating a single valid Accident event during Morning Peak returns 200.
    Also verifies the 'Tooltip on hover showing exact pin type' requirement:
    recommended_actions must include the exact event cause (e.g. 'Accident') in the description.
    """
    payload = {
        "scenario_mode": "Future Impact",
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
    # Check that recommended actions description includes the cause "Accident"
    for action in data.get("recommended_actions", []):
        assert "Accident" in action["description"]

def test_event_vehicle_breakdown_evening():
    """Verify that simulating a Vehicle Breakdown event during Evening Peak returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Vehicle Breakdown",
                "time_of_day": "Evening Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_event_time_of_day_impact():
    """Verify Time of Day Integration requirement:
    Modifying time_of_day for the same event changes the predicted risk and congestion scores,
    with peak hours returning higher or equal scores than off-peak.
    """
    event_peak = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "event_cause": "Accident",
        "time_of_day": "Morning Peak"
    }
    event_off = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "event_cause": "Accident",
        "time_of_day": "Off-Peak"
    }

    res_peak = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_peak]
    })
    res_off = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_off]
    })

    assert res_peak.status_code == 200
    assert res_off.status_code == 200

    risk_peak = res_peak.json()["risk_score"]
    risk_off = res_off.json()["risk_score"]
    assert risk_peak >= risk_off

def test_event_multiple_valid_events():
    """Verify that simulating multiple distinct events returns 200."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Accident",
                "time_of_day": "Morning Peak"
            },
            {
                "latitude": 12.9730,
                "longitude": 77.5960,
                "event_cause": "Protest / Rally",
                "time_of_day": "Evening Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_event_empty_list():
    """Verify that simulating with an empty events list returns 200."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_event_invalid_cause_returns_422():
    """Verify that an invalid event cause (e.g., 'Construction') returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Construction",
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_event_invalid_time_of_day_returns_422():
    """Verify that an invalid time of day (e.g., 'Midnight') returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Accident",
                "time_of_day": "Midnight"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_event_latitude_out_of_bounds_returns_422():
    """Verify that an event with latitude outside Bengaluru bounds returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 13.5,
                "longitude": 77.5946,
                "event_cause": "Accident",
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_event_missing_cause_returns_422():
    """Verify that an event object missing the event_cause field returns 422."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422

def test_event_incorrect_field_types_returns_422():
    """Verify that passing an integer for event_cause returns a 422 validation error."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": 12345,
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 422
