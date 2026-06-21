from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)

# ==========================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 scenarios)
# ==========================================

def test_real_world_scenario_1_baseline_congestion_mapping():
    """Scenario 1: Baseline Congestion Mapping (Low Complexity)
    
    Verifies that a baseline system query without active crowds, events, or barricades
    successfully maps normal traffic conditions and returns low risk/congestion metrics.
    """
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # Risk score should be low under baseline conditions
    assert data["risk_score"] < 5.0
    # Road closures are highly unlikely in pure baseline
    assert data["requires_road_closure"] < 0.5
    # Standard output fields exist
    assert isinstance(data["affected_roads"], list)
    assert isinstance(data["recommended_actions"], list)

def test_real_world_scenario_2_rush_hour_event_with_crowd_congestion():
    """Scenario 2: Rush Hour Event with Crowd Congestion (Medium Complexity)
    
    Simulates a major morning peak accident overlapping with a high-density crowd.
    Verifies that the predictive engine outputs significantly elevated risk scores.
    """
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 0.9}
        ],
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
    # Risk score and road closure probability should be high due to compounded rush hour congestion
    assert data["risk_score"] > 5.0
    assert data["requires_road_closure"] >= 0.5
    
    # Verify affected roads show high congestion scores
    for road in data["affected_roads"]:
        assert road["congestion_score"] > 3.0

def test_real_world_scenario_3_road_blockage_and_alternative_route_guidance():
    """Scenario 3: Road Blockage and Alternative Route Guidance (Medium Complexity)
    
    Simulates placing barricades on a primary road segment to bypass traffic.
    Verifies that the routing engine suggests alternative routing paths and actions.
    """
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946},
            {"latitude": 12.9720, "longitude": 77.5950}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # Recommended actions should contain route guidance / barricade action instructions
    assert len(data["recommended_actions"]) >= 1
    action = data["recommended_actions"][0]
    assert action["action_type"] == "Barricade"
    assert "route" in action["description"].lower() or "deploy" in action["description"].lower()

def test_real_world_scenario_4_crowd_and_event_dynamic_response():
    """Scenario 4: Crowd and Event Dynamic Response (High Complexity)
    
    Simulates a Protest / Rally event in the central business district (CBD)
    during evening peak hour, alongside substantial crowd density (0.75).
    Verifies that the system registers high congestion scores on CBD roads and triggers closures.
    """
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [
            {"latitude": 12.9716, "longitude": 77.5946, "density": 0.75}
        ],
        "events": [
            {
                "latitude": 12.9716,
                "longitude": 77.5946,
                "event_cause": "Protest / Rally",
                "time_of_day": "Evening Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    # The event should trigger critical levels of risk
    assert data["risk_score"] >= 7.0
    assert data["requires_road_closure"] > 0.5
    # The affected roads list must be non-empty representing the central roads
    assert len(data["affected_roads"]) > 0

def test_real_world_scenario_5_optimized_strategy_barricade_verification():
    """Scenario 5: Optimized Strategy Barricade Verification (High Complexity)
    
    Compares Future Impact mode to Optimized Strategy mode under identical
    high-demand protest and crowd conditions.
    Verifies that the optimization strategy successfully mitigates risk scores and targeted road congestion.
    """
    event = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "event_cause": "Protest / Rally",
        "time_of_day": "Morning Peak"
    }
    crowd = {"latitude": 12.9716, "longitude": 77.5946, "density": 0.8}
    
    # 1. Simulate Future Impact
    payload_future = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [crowd],
        "events": [event]
    }
    res_future = client.post("/simulate_scenario", json=payload_future)
    assert res_future.status_code == 200
    future_data = res_future.json()
    risk_future = future_data["risk_score"]
    roads_future = {r["road_id"]: r["congestion_score"] for r in future_data.get("affected_roads", [])}

    # 2. Simulate Optimized Strategy with strategic diversion barricades
    payload_opt = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9710, "longitude": 77.5940},
            {"latitude": 12.9725, "longitude": 77.5955}
        ],
        "crowds": [crowd],
        "events": [event]
    }
    res_opt = client.post("/simulate_scenario", json=payload_opt)
    assert res_opt.status_code == 200
    opt_data = res_opt.json()
    risk_opt = opt_data["risk_score"]
    roads_opt = {r["road_id"]: r["congestion_score"] for r in opt_data.get("affected_roads", [])}

    # Optimization MUST yield equal or lower system-wide risk
    assert risk_opt <= risk_future

    # Congestion on targeted road segments should be lower or equal
    for road_id, score_fut in roads_future.items():
        if road_id in roads_opt:
            assert roads_opt[road_id] <= score_fut
