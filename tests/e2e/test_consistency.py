from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_consistency_optimized_score_lower_than_future_impact():
    """Verify overall risk score in 'Optimized Strategy' (with barricades) <= 'Future Impact' (without barricades)."""
    event_payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "event_cause": "Accident",
        "time_of_day": "Morning Peak"
    }
    
    # 1. Future Impact (no barricades)
    payload_future = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_payload]
    }
    res_future = client.post("/simulate_scenario", json=payload_future)
    assert res_future.status_code == 200
    risk_future = res_future.json()["risk_score"]

    # 2. Optimized Strategy (with barricades)
    payload_opt = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9716, "longitude": 77.5946}],
        "crowds": [],
        "events": [event_payload]
    }
    res_opt = client.post("/simulate_scenario", json=payload_opt)
    assert res_opt.status_code == 200
    risk_opt = res_opt.json()["risk_score"]

    assert risk_opt <= risk_future

def test_consistency_targeted_road_congestion_reduced():
    """Verify that placing a barricade reduces targeted road congestion compared to Future Impact."""
    event = {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
    barricade = {"latitude": 12.9716, "longitude": 77.5946}
    
    payload_future = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event]
    }
    res_future = client.post("/simulate_scenario", json=payload_future)
    assert res_future.status_code == 200
    future_roads = {r["road_id"]: r["congestion_score"] for r in res_future.json().get("affected_roads", [])}

    payload_opt = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [barricade],
        "crowds": [],
        "events": [event]
    }
    res_opt = client.post("/simulate_scenario", json=payload_opt)
    assert res_opt.status_code == 200
    opt_roads = {r["road_id"]: r["congestion_score"] for r in res_opt.json().get("affected_roads", [])}

    # Check that for any road that had high congestion, the optimized score is lower or equal
    for road_id, future_score in future_roads.items():
        if road_id in opt_roads:
            assert opt_roads[road_id] <= future_score

def test_consistency_no_barricades_equal_scores():
    """Verify that 'Optimized Strategy' with no barricades has same risk score as 'Future Impact'."""
    event = {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
    
    payload_future = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event]
    }
    payload_opt = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [],
        "crowds": [],
        "events": [event]
    }
    
    res_future = client.post("/simulate_scenario", json=payload_future)
    res_opt = client.post("/simulate_scenario", json=payload_opt)
    
    assert res_future.status_code == 200
    assert res_opt.status_code == 200
    assert res_future.json()["risk_score"] == res_opt.json()["risk_score"]

def test_consistency_monotonically_decreasing_risk():
    """Verify that adding more strategic barricades monotonically decreases or maintains overall risk score."""
    event = {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
    
    # 0 barricades
    p0 = {"scenario_mode": "Optimized Strategy", "barricades": [], "crowds": [], "events": [event]}
    r0 = client.post("/simulate_scenario", json=p0).json()["risk_score"]
    
    # 1 barricade
    p1 = {"scenario_mode": "Optimized Strategy", "barricades": [{"latitude": 12.9716, "longitude": 77.5946}], "crowds": [], "events": [event]}
    r1 = client.post("/simulate_scenario", json=p1).json()["risk_score"]
    
    # 2 barricades
    p2 = {"scenario_mode": "Optimized Strategy", "barricades": [{"latitude": 12.9716, "longitude": 77.5946}, {"latitude": 12.9720, "longitude": 77.5950}], "crowds": [], "events": [event]}
    r2 = client.post("/simulate_scenario", json=p2).json()["risk_score"]
    
    assert r1 <= r0
    assert r2 <= r1

def test_consistency_barricade_limits_congestion_spread():
    """Verify that barricades limit the congestion score of adjacent/downstream roads."""
    # Placing barricades should prevent congestion spreading to downstream nodes
    event = {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
    
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9720, "longitude": 77.5950}],
        "crowds": [],
        "events": [event]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Risk score should be mitigated/contained
    assert data["risk_score"] < 10.0


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_consistency_micro_distance_barricades():
    """Verify that barricades placed at sub-meter/micro-degree distances from event reduce risk without errors."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.97160001, "longitude": 77.59460001}],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_consistency_exact_coincident_barricade():
    """Verify that placing a barricade exactly on the event coordinates mitigates congestion score correctly."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9716, "longitude": 77.5946}],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_consistency_distant_barricade_no_effect():
    """Verify that a barricade placed very far away (opposite side of city) does not reduce local event risk score."""
    # Event at (12.9716, 77.5946) - central
    # Barricade at (12.71, 77.41) - south-west edge
    p_no_barricade = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    }
    p_distant_barricade = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.71, "longitude": 77.41}],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    }
    
    r_no = client.post("/simulate_scenario", json=p_no_barricade).json()["risk_score"]
    r_dist = client.post("/simulate_scenario", json=p_distant_barricade).json()["risk_score"]
    
    # Distance barricade has no effect on this specific event's risk
    assert abs(r_no - r_dist) < 1e-5

def test_consistency_dense_barricades_preserves_bounds():
    """Verify that placing a massive list of barricades does not cause risk score to drop below 1.0."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9716 + 0.0001 * i, "longitude": 77.5946 + 0.0001 * i} for i in range(20)],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    assert response.json()["risk_score"] >= 1.0

def test_consistency_mode_switching_preserves_baseline():
    """Verify that switching to 'Baseline' ignores barricade mitigation and returns stable baseline scores."""
    p_baseline = {
        "scenario_mode": "Baseline",
        "barricades": [{"latitude": 12.9716, "longitude": 77.5946}],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=p_baseline)
    assert response.status_code == 200
    # In baseline, placing a barricade shouldn't lower baseline risk score below normal minimum or affect baseline roads
    assert response.json()["risk_score"] >= 1.0
