import os
import pickle
import rustworkx as rx
import networkx as nx
import numpy as np
from scipy.spatial import KDTree
import osmnx as ox
import polyline

def generate_graph():
    print("Downloading street network for Bangalore (12km radius)...")
    # Using 12km radius from city center to get a robust network
    center_point = (12.9716, 77.5946)
    
    # Configure osmnx to retain geometries
    ox.settings.useful_tags_way = ox.settings.useful_tags_way + ['name', 'highway', 'lanes', 'maxspeed']
    
    G_nx = ox.graph_from_point(center_point, dist=12000, network_type="drive")
    print(f"Downloaded network with {len(G_nx.nodes)} nodes and {len(G_nx.edges)} edges.")

    # Convert to rustworkx
    print("Converting to rustworkx graph...")
    G_rx = rx.PyDiGraph()
    
    node_mapping = {}
    node_indices = {}
    
    for n, data in G_nx.nodes(data=True):
        idx = G_rx.add_node({
            'osmid': n,
            'lat': data.get('y', 0.0),
            'lon': data.get('x', 0.0)
        })
        node_mapping[n] = idx
        node_indices[idx] = idx  # Wait, node_indices mapped from n to idx before.
        # Actually, in the frontend or simulation, we want to know idx->idx or n->idx?
        # Let's map idx to idx to be consistent with generate_grid_graph.py
        
    # Need original node mapping for the KDTree order mapping
    original_node_to_idx = {n: idx for n, idx in node_mapping.items()}
    rx_node_indices = {idx: idx for idx in G_rx.node_indices()}
        
    for u, v, key, data in G_nx.edges(keys=True, data=True):
        # Calculate weight (length in meters)
        weight = data.get('length', 10.0)
        
        edge_attr = {
            'weight': weight,
            'highway': data.get('highway', 'unclassified'),
            'osmid': data.get('osmid', 0),
            'length': weight
        }
        
        # We need the exact coordinates of the edge for the frontend overlay
        # If 'geometry' exists, it's a LineString
        coords = []
        if 'geometry' in data:
            coords = list(data['geometry'].coords)
        else:
            # Straight line between u and v
            u_node = G_nx.nodes[u]
            v_node = G_nx.nodes[v]
            coords = [(u_node['x'], u_node['y']), (v_node['x'], v_node['y'])]
            
        # polyline encodes (lat, lon), coords are (lon, lat) from shapely/osmnx
        lat_lon_coords = [(pt[1], pt[0]) for pt in coords]
        encoded = polyline.encode(lat_lon_coords)
        edge_attr['polyline'] = encoded
            
        G_rx.add_edge(node_mapping[u], node_mapping[v], edge_attr)

    print("Building KDTree for spatial indexing...")
    # Build KDTree using the rustworkx node order so kdtree index matches rustworkx node index
    coords = []
    # Guarantee we iterate nodes exactly matching G_rx.node_indices()
    # In rustworkx, node indices are contiguous if we didn't delete any.
    ordered_rx_indices = sorted(G_rx.node_indices())
    
    # We need a reverse mapping: rx_idx -> node data
    rx_idx_to_node_data = {}
    for n, idx in node_mapping.items():
        rx_idx_to_node_data[idx] = G_nx.nodes[n]
        
    for idx in ordered_rx_indices:
        data = rx_idx_to_node_data[idx]
        coords.append([data.get('y', 0.0), data.get('x', 0.0)]) # [lat, lon]
        
    kdtree = KDTree(np.array(coords))

    # Save everything
    output_data = {
        "graph": G_rx,
        "kdtree": kdtree,
        "node_indices": rx_node_indices
    }
    
    output_path = "routing_graph.pkl"
    print(f"Saving to {output_path}...")
    with open(output_path, "wb") as f:
        pickle.dump(output_data, f)
        
    print("Done! Real graph generated successfully.")

if __name__ == "__main__":
    generate_graph()

