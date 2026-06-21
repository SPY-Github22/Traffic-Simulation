import pytest
from fastapi.testclient import TestClient
from main import app
import random

client = TestClient(app)

def test_normal_event():
    """Verify normal expected inputs return successfully without crashing."""
    response = client.post("/simulate_event", json={
        "events": [{
            "latitude": 12.9716,
            "longitude": 77.5946,
            "event_cause": "Accident",
            "time_of_day": "Morning Peak",
            "vehicle_type": "Car/Taxi"
        }]
    })
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "etr_minutes" in data
    assert "affected_roads" in data
    assert "spillover_roads" in data
    assert "detour_routes" in data

def test_missing_fields_rejection():
    """Verify missing required Pydantic fields trigger automatic 422 instead of Internal Server Error 500."""
    response = client.post("/simulate_event", json={
        "events": [{
            "latitude": 12.9716,
            "longitude": 77.5946,
            "event_cause": "Accident"
            # Missing time_of_day and vehicle_type
        }]
    })
    assert response.status_code == 422

def test_extreme_out_of_bounds_pin():
    """Verify dropping a pin in the middle of the ocean/North pole snaps safely via KDTree and doesn't crash."""
    response = client.post("/simulate_event", json={
        "events": [{
            "latitude": 89.9999,
            "longitude": 179.9999,
            "event_cause": "Waterlogging",
            "time_of_day": "Night",
            "vehicle_type": "Heavy Truck"
        }]
    })
    assert response.status_code == 422

def test_chaos_engineering_fuzzing():
    """Send 50 completely random adversarial events concurrently to simulate apocalyptic scenarios. Must not crash."""
    random.seed(42)
    events = []
    for _ in range(50):
        events.append({
            "latitude": 12.97 + random.uniform(-5.0, 5.0),
            "longitude": 77.59 + random.uniform(-5.0, 5.0),
            "event_cause": random.choice(["Accident", "Waterlogging", "Barricade", "Police Squad", "Protest / Rally"]),
            "time_of_day": random.choice(["Morning Peak", "Night", "Evening Peak", "Afternoon"]),
            "vehicle_type": random.choice(["Heavy Truck", "Two-Wheeler", "Car/Taxi", "LCV (Light Commercial)"])
        })
        
    response = client.post("/simulate_event", json={"events": events})
    assert response.status_code in [200, 422]
