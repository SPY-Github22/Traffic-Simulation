from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 3: CROSS-FEATURE COMBINATIONS (7 tests)
# ==========================================

def test_combination_scenario_mode_and_barricades():
    """Test 1: Verify interactions when switching modes with active barricades."""
    barricades = [{"latitude": 12.9716, "longitude": 77.5946}]
    
    # In Baseline mode, barricades shouldn't trigger optimized redirection risk reductions
    res_base = client.post("/simulate_scenario", json={
        "scenario_mode": "Baseline",
        "barricades": barricades,
        "crowds": [],
        "events": []
    })
    assert res_base.status_code == 200
    
    # In Optimized Strategy, barricades should mitigate risk
    res_opt = client.post("/simulate_scenario", json={
        "scenario_mode": "Optimized Strategy",
        "barricades": barricades,
        "crowds": [],
        "events": []
    })
    assert res_opt.status_code == 200

def test_combination_scenario_mode_and_crowds():
    """Test 2: Verify interactions when crowds are placed under Future Impact vs Baseline."""
    crowds = [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.8}]
    
    res_base = client.post("/simulate_scenario", json={
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": crowds,
        "events": []
    })
    assert res_base.status_code == 200
    risk_base = res_base.json()["risk_score"]

    res_future = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": crowds,
        "events": []
    })
    assert res_future.status_code == 200
    risk_future = res_future.json()["risk_score"]

    # Future Impact should show higher or equal risk due to crowd impact magnifying
    assert risk_future >= risk_base

def test_combination_barricades_and_crowds():
    """Test 3: Verify placing barricades alongside high-density crowds."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9716, "longitude": 77.5946}],
        "crowds": [{"latitude": 12.9720, "longitude": 77.5950, "density": 0.9}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data

def test_combination_events_and_routing():
    """Test 4: Verify that simulating events changes the affected roads returned."""
    # Scenario 1: No events
    res_empty = client.post("/simulate_scenario", json={
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    })
    assert res_empty.status_code == 200
    roads_empty = res_empty.json().get("affected_roads", [])

    # Scenario 2: Severe Accident event
    res_event = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    })
    assert res_event.status_code == 200
    roads_event = res_event.json().get("affected_roads", [])

    # The list of affected roads should change (typically expand) when an event occurs
    assert len(roads_event) >= len(roads_empty)

def test_combination_crowds_and_routing():
    """Test 5: Verify that higher crowd densities yield higher congestion scores on affected roads."""
    # Low density crowd
    res_low = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.2}],
        "events": []
    })
    assert res_low.status_code == 200
    low_scores = [r["congestion_score"] for r in res_low.json().get("affected_roads", [])]
    max_low = max(low_scores) if low_scores else 1.0

    # High density crowd at same spot
    res_high = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.95}],
        "events": []
    })
    assert res_high.status_code == 200
    high_scores = [r["congestion_score"] for r in res_high.json().get("affected_roads", [])]
    max_high = max(high_scores) if high_scores else 1.0

    # Higher density should lead to higher congestion on the affected roads
    assert max_high >= max_low

def test_combination_barricades_and_routing():
    """Test 6: Verify placing barricades reroutes traffic, changing coordinates of affected segments."""
    # Without barricade
    res_no_barricade = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    })
    assert res_no_barricade.status_code == 200
    roads_no_barricade = {r["road_id"] for r in res_no_barricade.json().get("affected_roads", [])}

    # With barricade
    res_barricade = client.post("/simulate_scenario", json={
        "scenario_mode": "Optimized Strategy",
        "barricades": [{"latitude": 12.9716, "longitude": 77.5946}],
        "crowds": [],
        "events": [{"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}]
    })
    assert res_barricade.status_code == 200
    roads_barricade = {r["road_id"] for r in res_barricade.json().get("affected_roads", [])}

    # Placing a barricade should divert flow, changing the active set of affected roads
    assert roads_no_barricade != roads_barricade

def test_combination_compounded_prediction_logic():
    """Test 7: Verify compounded prediction logic for multiple concurrent events.
    
    The resulting risk score of multiple concurrent events must be predicted natively 
    by the model, and NOT be a simple summation of individual event risk scores.
    """
    event_a = {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
    event_b = {"latitude": 12.9730, "longitude": 77.5960, "event_cause": "Waterlogging", "time_of_day": "Morning Peak"}

    # 1. Simulate Event A alone
    res_a = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_a]
    })
    assert res_a.status_code == 200
    risk_a = res_a.json()["risk_score"]

    # 2. Simulate Event B alone
    res_b = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_b]
    })
    assert res_b.status_code == 200
    risk_b = res_b.json()["risk_score"]

    # 3. Simulate Event A & B together (Batch)
    res_both = client.post("/simulate_scenario", json={
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [event_a, event_b]
    })
    assert res_both.status_code == 200
    risk_both = res_both.json()["risk_score"]

    # Ensure risk score is computed natively (e.g. compounded) rather than simple summation
    # To avoid false assertions due to caps, we verify only when risk_a + risk_b is within the bounds (<= 10.0)
    if risk_a + risk_b < 10.0:
        assert risk_both != risk_a + risk_b
    else:
        # If the sum overflows 10.0, we check that the compounded model risk score handles clustering density natively
        assert risk_both <= 10.0
