
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import os


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_graph_data(csv_file):
    df = pd.read_csv(csv_file)
    coords = list(zip(df['lat'], df['lon']))
    n = len(coords)
    distance_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                distance_matrix[i][j] = haversine_distance(*coords[i], *coords[j])
    names = df['name'].tolist() if 'name' in df.columns else [f"Titik {i+1}" for i in range(n)]
    return df, distance_matrix, names


def estimate_fuel_cost(distance, fuel_price, cost_other, efficiency_km_per_liter=5):
    fuel_used = round((distance / 1000) / efficiency_km_per_liter, 2)
    total_cost = fuel_used * fuel_price + cost_other
    return fuel_used, total_cost


def save_convergence_plot(history, filename='data/convergence.png'):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.figure(figsize=(6, 3))
    plt.plot(history, marker='o', linewidth=2, color='black')
    plt.title('Konvergensi ACO')
    plt.xlabel('Iterasi')
    plt.ylabel('Jarak Total (meter)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
