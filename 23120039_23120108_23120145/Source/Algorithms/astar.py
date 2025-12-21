import heapq
import itertools
import os
import sys
import time
from copy import deepcopy

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from cnf import CNFGenerator, Island
    from connectivity import count_components
    from is_intersect import is_intersect
except ImportError as e:
    raise e


class TimeoutException(Exception):
    """Exception raised when algorithm exceeds time limit."""
    pass


class AStar:
    """A* solver for Hashiwokakero puzzles using heuristic search."""
    
    def __init__(self):
        """Initialize A* solver."""
        self.solution_vars = None
        self.matrix = None

    def solve(self, matrix, timeout=300):
        """Solve puzzle using A* search."""
        print("\n--- Preprocessing ---")
        self.matrix = matrix

        cnf_generator = CNFGenerator()
        (self.clauses, 
         self.reverse_map, 
         self.islands, 
         self.bridges, 
         self.var_map, 
         self.num_vars) = cnf_generator.generate_cnf_clauses(matrix)
        
        print(f"Setup done: {len(self.islands)} islands.")
        print(f"Timeout: {timeout}s")

        self.bridge_pairs = []
        seen = set()
        for bridge in self.bridges:
            u, v, _ = bridge
            key = tuple(sorted((u.id, v.id)))
            if key in seen:
                continue
            seen.add(key)
            var1 = self.var_map.get((u, v, 1))
            var2 = self.var_map.get((u, v, 2))
            if var1 is not None and var2 is not None:
                self.bridge_pairs.append((var1, var2))

        self.island_incident = {island.id: [] for island in self.islands}
        self.island_demand = {island.id: island.val for island in self.islands}
        for (u, v, _) in self.bridges:
            v1 = self.var_map[(u, v, 1)]
            v2 = self.var_map[(u, v, 2)]
            self.island_incident[u.id].append((v1, v2))
            self.island_incident[v.id].append((v1, v2))

        horizontal_bridges = [b for b in self.bridges if b[2] == 'H']
        vertical_bridges = [b for b in self.bridges if b[2] == 'V']
        self.crossing_pairs = []
        for h_bridge in horizontal_bridges:
            for v_bridge in vertical_bridges:
                if is_intersect(h_bridge[0], h_bridge[1], v_bridge[0], v_bridge[1]):
                    id_h1 = self.var_map[(h_bridge[0], h_bridge[1], 1)]
                    id_v1 = self.var_map[(v_bridge[0], v_bridge[1], 1)]
                    self.crossing_pairs.append((id_h1, id_v1))

        counter = itertools.count()

        print("\n--- Starting A* (Standard Version) ---")
        start_time = time.perf_counter()
        self.timeout = timeout

        pq = []
        initial_state = {
            "index": 0, "0": [], "1": [],
            "gx": 0, "fx": 0, "components": len(self.islands)
        }
        
        res = self._evaluate_state(initial_state)
        if res:
            hx = res[0]
            initial_state["components"] = res[1]
            initial_state["fx"] = initial_state["gx"] + hx
            heapq.heappush(pq, (initial_state["fx"], 0, next(counter), initial_state))

        visited_nodes = 0
        
        try:
            while pq:
                # Check timeout periodically (every 1000 nodes or every iteration for small problems)
                if visited_nodes % 1000 == 0:
                    elapsed = time.perf_counter() - start_time
                    if elapsed >= self.timeout:
                        raise TimeoutException()
                
                curr_fx, _, _, state = heapq.heappop(pq)
                visited_nodes += 1

                if state["index"] >= len(self.bridge_pairs):
                    eval_res = self._evaluate_state(state)
                    if eval_res:
                        num_components = eval_res[1]
                        if num_components == 1:
                            duration = time.perf_counter() - start_time
                            self.solution_vars = state["1"]
                            print(f"Solved! Visited nodes: {visited_nodes}")
                            return self.get_result_matrix(), duration
                    continue

                var1, var2 = self.bridge_pairs[state["index"]]
                
                options = [
                    ([],           [var1, var2]),
                    ([var1],       [var2]),
                    ([var1, var2], [])
                ]

                for add_to_1, add_to_0 in options:
                    new_state = deepcopy(state)
                    new_state["1"].extend(add_to_1)
                    new_state["0"].extend(add_to_0)
                    new_state["index"] += 1
                    new_state["gx"] = state["gx"] + 1
                    
                    eval_res = self._evaluate_state(new_state)
                    if eval_res:
                        new_hx = eval_res[0]
                        new_state["components"] = eval_res[1]
                        new_state["fx"] = new_state["gx"] + new_hx
                        heapq.heappush(pq, (new_state["fx"], -new_state["index"], next(counter), new_state))

            print("No solution found.")
            return None, (time.perf_counter() - start_time)
        
        except TimeoutException:
            duration = time.perf_counter() - start_time
            print(f"\n⏱ TIMEOUT after {duration:.2f}s")
            print(f"Visited nodes: {visited_nodes:,}")
            return None, duration

    def _evaluate_state(self, state):
        """Evaluate a state for A* search, checking constraints and computing connectivity heuristic."""
        assignment = {}
        for x in state["1"]:
            assignment[x] = True
        for x in state["0"]:
            assignment[x] = False
        
        for h1, v1 in self.crossing_pairs:
            if assignment.get(h1) and assignment.get(v1):
                return False

        for island in self.islands:
            isl_id = island.id
            demand = self.island_demand[isl_id]
            min_deg = 0
            max_deg = 0

            for v1, v2 in self.island_incident[isl_id]:
                a1 = assignment.get(v1)
                a2 = assignment.get(v2)

                if a1 is True:
                    if a2 is True:
                        min_deg += 2
                        max_deg += 2
                    elif a2 is False:
                        min_deg += 1
                        max_deg += 1
                    else:
                        min_deg += 1
                        max_deg += 2
                elif a1 is False:
                    if a2 is True:
                        return False
                    elif a2 is False:
                        pass
                    else:
                        pass
                else:
                    if a2 is True:
                        return False
                    elif a2 is False:
                        max_deg += 1
                    else:
                        max_deg += 2

            if min_deg > demand or max_deg < demand:
                return False

        num_components, _ = count_components(self.islands, state["1"], self.reverse_map)
        heuristic_weight = 10
        hx = (num_components - 1) * heuristic_weight
        
        return [hx, num_components]
    
    def get_result_matrix(self):
        """Build result matrix from solution variables."""
        if not self.solution_vars:
            return None
        
        rows, cols = len(self.matrix), len(self.matrix[0])
        grid_str = [["0" for _ in range(cols)] for _ in range(rows)]
        
        for isl in self.islands:
            grid_str[isl.r][isl.c] = str(isl.val)
        
        sol_set = set(self.solution_vars)
        for b in self.bridges:
            u, v, direction = b
            id1 = self.var_map[(u, v, 1)]
            id2 = self.var_map[(u, v, 2)]
            if id1 not in sol_set:
                continue
            
            is_double = id2 in sol_set
            if direction == 'H':
                symbol = "=" if is_double else "-"
                r = u.r
                c_start, c_end = sorted((u.c, v.c))
                for c in range(c_start + 1, c_end):
                    grid_str[r][c] = symbol
            else:
                symbol = "$" if is_double else "|"
                c = u.c
                r_start, r_end = sorted((u.r, v.r))
                for r in range(r_start + 1, r_end):
                    grid_str[r][c] = symbol
        
        return grid_str