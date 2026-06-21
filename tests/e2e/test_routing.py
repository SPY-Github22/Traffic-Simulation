from fastapi.testclient import TestClient
import pytest
import math
from main import app

client = TestClient(app)

# Bengaluru Bounds: 12.7 < lat < 13.2, 77.4 < lon < 77.8

# ==========================================
# TIER 1: FEATURE COVERAGE (5 tests)
# ==========================================

def test_routing_returns_geojson_coordinates():
    """Verify that coordinates in affected_roads are [longitude, latitude] arrays."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.5}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "affected_roads" in data
    for road in data["affected_roads"]:
        coords = road["coordinates"]
        for p in coords:
            # GeoJSON style: longitude first, then latitude
            assert 77.4 <= p[0] <= 77.8 # Longitude bounds
            assert 12.7 <= p[1] <= 13.2 # Latitude bounds

def test_routing_segment_has_minimum_points():
    """Verify that each affected road has at least 2 points forming a line segment."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [
            {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    for road in data.get("affected_roads", []):
        assert len(road["coordinates"]) >= 2

def test_routing_road_id_non_empty():
    """Verify that each affected road has a non-empty string as road_id."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.3}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    for road in data.get("affected_roads", []):
        assert isinstance(road["road_id"], str)
        assert len(road["road_id"].strip()) > 0

def test_routing_congestion_scores_within_bounds():
    """Verify that all returned congestion scores on affected roads are in range [1.0, 10.0]."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.9}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    for road in data.get("affected_roads", []):
        assert 1.0 <= road["congestion_score"] <= 10.0

def test_routing_congestion_decay_with_distance():
    """Verify that affected_roads have a decaying congestion score based on distance from the event center.
    Roads closer to the event coordinate must have higher or equal congestion scores than roads further away.
    """
    event_lat = 12.9716
    event_lon = 77.5946
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [],
        "events": [
            {"latitude": event_lat, "longitude": event_lon, "event_cause": "Accident", "time_of_day": "Morning Peak"}
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    affected_roads = data.get("affected_roads", [])
    
    if len(affected_roads) >= 2:
        road_distances = []
        for road in affected_roads:
            coords = road["coordinates"]
            avg_lon = sum(pt[0] for pt in coords) / len(coords)
            avg_lat = sum(pt[1] for pt in coords) / len(coords)
            dist = math.sqrt((avg_lat - event_lat)**2 + (avg_lon - event_lon)**2)
            road_distances.append((dist, road["congestion_score"]))
        
        # Sort by distance
        road_distances.sort(key=lambda x: x[0])
        
        # Verify decay: further roads have lower or equal congestion scores than closer roads
        for i in range(len(road_distances) - 1):
            dist_a, score_a = road_distances[i]
            dist_b, score_b = road_distances[i+1]
            assert score_a >= score_b


# ==========================================
# TIER 2: BOUNDARY & CORNER (5 tests)
# ==========================================

def test_routing_precisely_on_boundary_limits():
    """Verify that simulating events right at the bounding box limits returns 200 or 422 cleanly."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {"latitude": 12.7, "longitude": 77.4, "event_cause": "Accident", "time_of_day": "Morning Peak"}
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code in [200, 422]

def test_routing_high_precision_coordinates():
    """Verify that the routing engine handles coordinates with extremely high float precision."""
    payload = {
        "scenario_mode": "Baseline",
        "barricades": [],
        "crowds": [],
        "events": [
            {
                "latitude": 12.971612345678,
                "longitude": 77.594612345678,
                "event_cause": "Accident",
                "time_of_day": "Morning Peak"
            }
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_routing_disconnected_graph_handling():
    """Verify routing engine handles a scenario with multiple barricades that block all paths."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946},
            {"latitude": 12.9717, "longitude": 77.5947},
            {"latitude": 12.9718, "longitude": 77.5948}
        ],
        "crowds": [],
        "events": [
            {"latitude": 12.9716, "longitude": 77.5946, "event_cause": "Accident", "time_of_day": "Morning Peak"}
        ]
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_routing_duplicate_barricades_at_same_node():
    """Verify routing engine handles multiple duplicate barricades at the same coordinates."""
    payload = {
        "scenario_mode": "Optimized Strategy",
        "barricades": [
            {"latitude": 12.9716, "longitude": 77.5946},
            {"latitude": 12.9716, "longitude": 77.5946}
        ],
        "crowds": [],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200

def test_routing_road_id_uniqueness():
    """Verify that affected_roads list does not contain duplicate road_ids."""
    payload = {
        "scenario_mode": "Future Impact",
        "barricades": [],
        "crowds": [{"latitude": 12.9716, "longitude": 77.5946, "density": 0.8}],
        "events": []
    }
    response = client.post("/simulate_scenario", json=payload)
    assert response.status_code == 200
    data = response.json()
    road_ids = [road["road_id"] for road in data.get("affected_roads", [])]
    assert len(road_ids) == len(set(road_ids))
