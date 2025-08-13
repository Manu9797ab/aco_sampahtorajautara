import osmnx as ox
import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt


def load_graph_data(csv_file):
    # Baca file CSV yang berisi titik koordinat
    df = pd.read_csv(csv_file)
    coords = list(zip(df['lat'], df['lon']))

    # Buat graf dari titik tengah
    center_lat = df['lat'].mean()
    center_lon = df['lon'].mean()

    G = ox.graph_from_point((center_lat, center_lon), dist=2000, network_type='drive')

    # Ambil node terdekat dari setiap titik
    node_ids = [ox.distance.nearest_nodes(G, lon, lat) for lat, lon in coords]

    # Hitung jarak antar semua titik dalam node_ids
    n = len(node_ids)
    distance_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                try:
                    distance_matrix[i][j] = nx.shortest_path_length(G, source=node_ids[i], target=node_ids[j], weight='length')
                except nx.NetworkXNoPath:
                    distance_matrix[i][j] = float('inf')

    # Ambil nama titik dari CSV
    names = df['nama'].tolist() if 'nama' in df.columns else [f'Titik {i+1}' for i in range(n)]

    return df, G, node_ids, distance_matrix, names



def calculate_route_distance(routes, distance_matrix):
    return sum(distance_matrix[route[i]][route[i + 1]] for route in routes for i in range(len(route) - 1))


def estimate_fuel_cost(distance_m, fuel_price, other_cost):
    fuel_consumption_l_per_km = 0.05  # 0.5 liter per 10 km
    fuel_used = (distance_m / 1000) * fuel_consumption_l_per_km
    total_cost = (fuel_used * fuel_price) + other_cost
    return round(fuel_used, 2), round(total_cost, 2)

def estimate_fuel_cost(distance, fuel_price, cost_other, efficiency_km_per_liter=5):
    fuel_used = round((distance / 1000) / efficiency_km_per_liter, 2)  # jarak dalam km
    total_cost = fuel_used * fuel_price + cost_other
    return fuel_used, total_cost


def ensure_dir(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def save_convergence_plot(history, filename='data/convergence.png'):
    plt.figure(figsize=(6, 3))
    plt.plot(history, marker='o', linewidth=2, color='black')
    plt.title('Konvergensi ACO')
    plt.xlabel('Iterasi')
    plt.ylabel('Jarak Total (meter)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
