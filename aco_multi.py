import numpy as np
import random

class AntColonyMulti:
    def __init__(self, distance_matrix, n_ants, n_iterations, alpha, beta, decay, n_vehicles):
        self.distances = distance_matrix
        self.pheromone = np.ones_like(distance_matrix) / len(distance_matrix)
        self.all_inds = list(range(len(distance_matrix)))
        self.n_ants = n_ants
        self.n_iterations = n_iterations
        self.alpha = alpha
        self.beta = beta
        self.decay = decay
        self.n_vehicles = n_vehicles

    def run(self):
        best_routes = None
        best_distance = float("inf")
        history = []

        for iteration in range(self.n_iterations):
            all_routes = []
            for _ in range(self.n_ants):
                routes = self.construct_routes()
                all_routes.append(routes)

            distances = [self.total_distance(r) for r in all_routes]
            min_dist = min(distances)

            if min_dist < best_distance:
                best_distance = min_dist
                best_routes = all_routes[distances.index(min_dist)]

            self.spread_pheromone(all_routes, distances)
            self.pheromone *= self.decay
            history.append(best_distance)

            print(f"Iterasi {iteration+1}: Jarak terbaik = {best_distance:.2f}")

        return best_routes, best_distance, history

    def construct_routes(self):
        unvisited = set(self.all_inds[1:])  # 0 adalah depot
        routes = [[] for _ in range(self.n_vehicles)]

        for k in range(self.n_vehicles):
            route = [0]
            while True:
                curr = route[-1]
                choices = list(unvisited)
                valid_choices = []
                valid_probs = []

                for j in choices:
                    d = self.distances[curr][j]
                    if not np.isfinite(d) or d == 0:
                        continue
                    pher = self.pheromone[curr][j] ** self.alpha
                    heur = (1 / d) ** self.beta
                    prob = pher * heur
                    valid_choices.append(j)
                    valid_probs.append(prob)

                if not valid_choices:
                    break  # tidak ada kota yang bisa dikunjungi

                total = sum(valid_probs)
                if total == 0:
                    break

                norm_probs = [p / total for p in valid_probs]
                next_city = random.choices(valid_choices, norm_probs)[0]
                route.append(next_city)
                unvisited.remove(next_city)

                # Batas jumlah kunjungan per truk (opsional)
                if len(route) > len(self.all_inds) // self.n_vehicles:
                    break

            route.append(0)  # kembali ke depot
            routes[k] = route

        return routes

    def total_distance(self, routes):
        total = 0
        for route in routes:
            for i in range(len(route) - 1):
                d = self.distances[route[i]][route[i + 1]]
                if np.isfinite(d):
                    total += d
                else:
                    total += 999999  # penalti jika tak terhubung (opsional)
        return total

    def spread_pheromone(self, routes_list, distances):
        for routes, dist in zip(routes_list, distances):
            if dist == 0 or not np.isfinite(dist):
                continue
            for route in routes:
                for i in range(len(route) - 1):
                    self.pheromone[route[i]][route[i + 1]] += 1.0 / dist
