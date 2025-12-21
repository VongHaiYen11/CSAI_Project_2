import os
import sys
import time

from pysat.solvers import Glucose3

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from cnf import CNFGenerator
from connectivity import check_connectivity


class TimeoutException(Exception):
    """Exception raised when algorithm exceeds time limit."""
    pass


class PySAT:
    """PySAT solver for Hashiwokakero puzzles using Glucose3 SAT solver."""
    
    def __init__(self):
        """Initialize PySAT solver."""
        self.solution_vars = None
        self.matrix = None
    
    def solve(self, matrix, timeout=300):
        """Solve Hashiwokakero puzzle using SAT solver with Glucose3."""
        self.matrix = matrix
        
        # Generate CNF clauses from puzzle
        cnf_generator = CNFGenerator()
        clauses, reverse_map, islands, bridges, var_map, num_vars = cnf_generator.generate_cnf_clauses(matrix)
        
        print(f"Timeout: {timeout}s")
        
        # Solve with SAT solver
        start = time.perf_counter()
        self.timeout = timeout
        iterations = 0
        
        try:
            with Glucose3(bootstrap_with=clauses) as solver:
                while solver.solve():
                    # Check timeout periodically (every 100 iterations)
                    iterations += 1
                    if iterations % 100 == 0:
                        elapsed = time.perf_counter() - start
                        if elapsed >= self.timeout:
                            raise TimeoutException()
                    
                    model = solver.get_model()
                    
                    # Check connectivity constraint
                    if check_connectivity(model, islands, reverse_map):
                        duration = time.perf_counter() - start
                        return self.build_output_matrix(model, reverse_map, islands, bridges, var_map), duration
                    else:
                        # Block this solution and continue searching
                        solver.add_clause([-x for x in model])
            
            duration = time.perf_counter() - start
            return None, duration
        
        except TimeoutException:
            duration = time.perf_counter() - start
            print(f"\n⏱ TIMEOUT after {duration:.2f}s")
            print(f"Iterations: {iterations:,}")
            return None, duration
    
    def build_output_matrix(self, model, reverse_map, islands, bridges, var_map):
        """Build output matrix from SAT model."""
        n = len(self.matrix)
        grid = [["0"] * n for _ in range(n)]
        
        # Place islands
        for island in islands:
            grid[island.r][island.c] = str(island.val)
        
        # Process active bridge variables
        active_vars = set(v for v in model if v > 0)
        bridge_map = {}
        
        for var, (u, v, cnt, d) in reverse_map.items():
            if var not in active_vars:
                continue
            key = (u, v)
            if key not in bridge_map:
                bridge_map[key] = {"has1": False, "has2": False, "dir": d}
            if cnt == 1:
                bridge_map[key]["has1"] = True
            elif cnt == 2:
                bridge_map[key]["has2"] = True
        
        # Draw bridges
        for (u, v), info in bridge_map.items():
            count = 2 if info["has2"] else 1 if info["has1"] else 0
            if count == 0:
                continue
            
            direction = info["dir"]
            if direction == "H":
                char = "=" if count == 2 else "-"
                for c in range(u.c + 1, v.c):
                    grid[u.r][c] = char
            else:
                char = "$" if count == 2 else "|"
                for r in range(u.r + 1, v.r):
                    grid[r][u.c] = char
        
        return grid