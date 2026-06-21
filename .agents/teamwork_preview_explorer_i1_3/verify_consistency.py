import networkx as nx
import numpy as np

class TrafficSimulator:
    def __init__(self):
        # Create a simple road network
        self.G = nx.DiGraph()
        # Nodes: Junctions
        # Edges: Roads with base capacity and free-flow travel time (weight)
        self.G.add_edge("J1", "J2", weight=2.0, capacity=100)
        self.G.add_edge("J2", "J3", weight=2.0, capacity=100)
        self.G.add_edge("J1", "J4", weight=4.0, capacity=100)
        self.G.add_edge("J4", "J3", weight=4.0, capacity=100)
        # Alternative path: J1 -> J2 -> J3 (weight 4) vs J1 -> J4 -> J3 (weight 8)
        
    def calculate_congestion_scores(self, events=None, barricades=None):
        # Copy graph so we don't modify the base network
        G_temp = self.G.copy()
        
        # Apply events: increase weight (cost) of affected roads
        if events:
            for edge, severity in events.items():
                if G_temp.has_edge(*edge):
                    G_temp[edge[0]][edge[1]]['weight'] += severity
                    
        # Apply barricades: block roads (remove edge to prevent path finding)
        blocked_edges = set()
        if barricades:
            for edge in barricades:
                if G_temp.has_edge(*edge):
                    G_temp.remove_edge(*edge)
                    blocked_edges.add(edge)
                    
        # Calculate traffic volume based on shortest path routing between all pairs
        # We assume traffic travels from J1 to J3
        traffic_volume = {edge: 0 for edge in self.G.edges()}
        
        # Let's simulate routing for 100 vehicles from J1 to J3
        try:
            path = nx.shortest_path(G_temp, source="J1", target="J3", weight="weight")
            # Increment traffic volume along the path
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                traffic_volume[(u, v)] += 100
        except nx.NetworkXNoPath:
            # No path available (e.g. both routes blocked)
            pass
            
        # Calculate congestion score for each road:
        # Congestion = base_weight * (traffic_volume / capacity)
        congestion_scores = {}
        for edge in self.G.edges():
            u, v = edge
            if edge in blocked_edges:
                # Closed road has 0.0 congestion score because no cars can pass
                congestion_scores[edge] = 0.0
            else:
                vol = traffic_volume[edge]
                cap = self.G[u][v]['capacity']
                base_w = self.G[u][v]['weight']
                # If an event is on this road, base weight is higher
                if events and edge in events:
                    base_w += events[edge]
                # Congestion score scaled 1.0 to 10.0
                score = 1.0 + min(9.0, (vol / cap) * base_w)
                congestion_scores[edge] = score
                
        return congestion_scores

def test_logical_consistency():
    sim = TrafficSimulator()
    
    # Scenario 1: Base state (no events, no barricades)
    # Shortest path is J1 -> J2 -> J3 (weight 4)
    scores_base = sim.calculate_congestion_scores()
    print("Base Congestion scores:", scores_base)
    
    # Scenario 2: Event (Accident) on road J1 -> J2 (targeted road)
    # J1 -> J2 becomes congested
    events = {("J1", "J2"): 10.0}
    scores_event = sim.calculate_congestion_scores(events=events)
    print("Congestion scores with event:", scores_event)
    
    # Verify that event increases congestion on the targeted road
    assert scores_event[("J1", "J2")] > scores_base[("J1", "J2")], "Event should increase congestion"
    
    # Scenario 3: Place barricade on J1 -> J2 (direct mitigation)
    # Closes J1 -> J2, forcing traffic to J1 -> J4 -> J3
    barricades_direct = [("J1", "J2")]
    scores_mitigated_direct = sim.calculate_congestion_scores(events=events, barricades=barricades_direct)
    print("Congestion scores with direct barricade:", scores_mitigated_direct)
    
    # Verify that direct barricade strictly reduces targeted road congestion score
    assert scores_mitigated_direct[("J1", "J2")] < scores_event[("J1", "J2")], "Direct barricade should reduce congestion on targeted road"
    assert scores_mitigated_direct[("J1", "J2")] == 0.0, "Directly barricaded road should have 0.0 congestion score"
    
    # Scenario 4: Detour mitigation (place barricade upstream to divert traffic before it reaches J2 -> J3)
    events_2 = {("J2", "J3"): 10.0}
    scores_event_2 = sim.calculate_congestion_scores(events=events_2)
    print("Congestion scores with event on J2-J3:", scores_event_2)
    
    # Place barricade on J1 -> J2 (upstream of J2 -> J3) to detour traffic to J1 -> J4 -> J3
    barricades_detour = [("J1", "J2")]
    scores_mitigated_detour = sim.calculate_congestion_scores(events=events_2, barricades=barricades_detour)
    print("Congestion scores with detour barricade on J1-J2:", scores_mitigated_detour)
    
    # Verify that detour barricade reduces congestion on the targeted congested road J2 -> J3
    assert scores_mitigated_detour[("J2", "J3")] < scores_event_2[("J2", "J3")], "Detour barricade should reduce congestion on targeted road J2-J3"
    
    print("All logical consistency checks passed successfully!")

if __name__ == "__main__":
    test_logical_consistency()
