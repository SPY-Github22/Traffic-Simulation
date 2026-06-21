import networkx as nx
import numpy as np

class TrafficSimulator:
    def __init__(self):
        # Create a simple road network
        # Nodes: Junctions in Bengaluru
        # Edges: Roads with base capacity and free-flow travel time (weight)
        self.G = nx.DiGraph()
        
        # Scenario layout:
        # Route 1: J1 -> J2 -> J3 (short path, free-flow weight 4.0, capacity 100)
        # Route 2: J1 -> J4 -> J3 (longer path, free-flow weight 8.0, capacity 100)
        self.G.add_edge("J1", "J2", weight=2.0, capacity=100)
        self.G.add_edge("J2", "J3", weight=2.0, capacity=100)
        self.G.add_edge("J1", "J4", weight=4.0, capacity=100)
        self.G.add_edge("J4", "J3", weight=4.0, capacity=100)
        
    def calculate_congestion_scores(self, events=None, barricades=None, total_demand=100):
        """
        Calculates edge-by-edge congestion scores.
        - events: dict of {edge: severity} that increases travel cost (weight)
        - barricades: list of edges that are closed (removed from network)
        - total_demand: total volume of cars seeking to go J1 -> J3
        """
        G_temp = self.G.copy()
        
        # 1. Apply events: increase travel time weight
        if events:
            for edge, severity in events.items():
                if G_temp.has_edge(*edge):
                    G_temp[edge[0]][edge[1]]['weight'] += severity
                    
        # 2. Apply barricades: close the road segment by removing the edge
        blocked_edges = set()
        if barricades:
            for edge in barricades:
                if G_temp.has_edge(*edge):
                    G_temp.remove_edge(*edge)
                    blocked_edges.add(edge)
                    
        # 3. Shortest path routing
        traffic_volume = {edge: 0 for edge in self.G.edges()}
        try:
            path = nx.shortest_path(G_temp, source="J1", target="J3", weight="weight")
            # All demand takes the shortest path
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                traffic_volume[(u, v)] += total_demand
        except nx.NetworkXNoPath:
            # If all paths are blocked, traffic cannot route
            pass
            
        # 4. Congestion Score calculation:
        # Scale score from 1.0 (free flow) to 10.0 (gridlock)
        # Score = 1.0 + min(9.0, (volume / capacity) * current_edge_weight)
        congestion_scores = {}
        for edge in self.G.edges():
            u, v = edge
            if edge in blocked_edges:
                # A barricaded road is closed. Congestion is 0.0 (or 1.0) because no vehicles pass.
                # In terms of throughput congestion score, we set it to 1.0 (free-flow/empty).
                congestion_scores[edge] = 1.0
            else:
                vol = traffic_volume[edge]
                cap = self.G[u][v]['capacity']
                weight = self.G[u][v]['weight']
                if events and edge in events:
                    weight += events[edge]
                # Scale congestion score
                score = 1.0 + min(9.0, (vol / cap) * weight)
                congestion_scores[edge] = score
                
        return congestion_scores

def verify_logical_consistency():
    sim = TrafficSimulator()
    
    # Test 1: Baseline Congestion (Shortest path J1 -> J2 -> J3 is chosen)
    scores_base = sim.calculate_congestion_scores()
    print("Baseline Congestion Scores:")
    for edge, score in scores_base.items():
        print(f"  {edge}: {score:.2f}")
    
    # Assert J1-J2 and J2-J3 carry the traffic and have > 1.0 congestion, while J1-J4 and J4-J3 have 1.0
    assert scores_base[("J1", "J2")] > 1.0
    assert scores_base[("J1", "J4")] == 1.0
    
    # Test 2: Event (Accident) occurs on road J1 -> J2
    # This should increase congestion on that road segment
    events = {("J1", "J2"): 10.0}
    scores_event = sim.calculate_congestion_scores(events=events)
    print("\nCongestion Scores with Accident on J1 -> J2:")
    for edge, score in scores_event.items():
        print(f"  {edge}: {score:.2f}")
        
    assert scores_event[("J1", "J2")] > scores_base[("J1", "J2")], "Event must increase targeted road congestion score!"
    
    # Test 3: Deploy barricade on J1 -> J2 (Direct Closure)
    # The road is closed, so congestion on J1 -> J2 must drop to 1.0 (empty)
    # Traffic is forced to route via J1 -> J4 -> J3
    barricades_direct = [("J1", "J2")]
    scores_barricade_direct = sim.calculate_congestion_scores(events=events, barricades=barricades_direct)
    print("\nCongestion Scores with Barricade on J1 -> J2:")
    for edge, score in scores_barricade_direct.items():
        print(f"  {edge}: {score:.2f}")
        
    assert scores_barricade_direct[("J1", "J2")] < scores_event[("J1", "J2")], "Direct barricade must strictly reduce congestion on the closed road!"
    assert scores_barricade_direct[("J1", "J2")] == 1.0, "Closed road congestion must be 1.0 (empty)."
    assert scores_barricade_direct[("J1", "J4")] > 1.0, "Traffic must detour to J1 -> J4 -> J3."

    # Test 4: Detour mitigation (place barricade upstream to divert traffic before it reaches a downstream bottleneck)
    # Event is on J2 -> J3 (bottleneck)
    events_bottleneck = {("J2", "J3"): 10.0}
    scores_bottleneck = sim.calculate_congestion_scores(events=events_bottleneck)
    print("\nCongestion Scores with Event on J2 -> J3 (Downstream):")
    for edge, score in scores_bottleneck.items():
        print(f"  {edge}: {score:.2f}")
        
    # Place barricade upstream on J1 -> J2 to detour traffic to J1 -> J4 -> J3
    barricades_detour = [("J1", "J2")]
    scores_detour = sim.calculate_congestion_scores(events=events_bottleneck, barricades=barricades_detour)
    print("\nCongestion Scores with Upstream Barricade on J1 -> J2 (Detour):")
    for edge, score in scores_detour.items():
        print(f"  {edge}: {score:.2f}")
        
    # Assert that placing the upstream barricade reduced congestion on the targeted downstream road J2 -> J3
    assert scores_detour[("J2", "J3")] < scores_bottleneck[("J2", "J3")], "Upstream detour barricade must reduce congestion on the targeted downstream road!"
    
    # Test 5: Congestion score bounds compliance
    for score in list(scores_base.values()) + list(scores_event.values()) + list(scores_barricade_direct.values()) + list(scores_detour.values()):
        assert 1.0 <= score <= 10.0, f"Congestion score {score} is out of bounds [1.0, 10.0]!"

    print("\nAll logical consistency checks passed successfully!")

if __name__ == "__main__":
    verify_logical_consistency()
