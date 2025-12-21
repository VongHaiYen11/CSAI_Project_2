import itertools
import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from is_intersect import is_intersect
from connectivity import check_connectivity_from_edges
class BruteForce:
    """Brute force solver for Hashiwokakero puzzles exploring all possible bridge configurations."""
    
    def __init__(self, matrix):
        """Initialize brute force solver."""
        self.matrix = matrix
        self.n = len(matrix)
        
        # List of islands: (row, col, value)
        self.islands = []
        for i in range(self.n):
            for j in range(self.n):
                if matrix[i][j] > 0:
                    self.islands.append((i, j, matrix[i][j]))
        
        # Generate all possible bridge edges
        self.edges = self.generate_edges()
    
    def generate_edges(self):
        """Find all possible bridge edges going right or down."""
        edges = []
        island_pos = {(x, y): True for x, y, _ in self.islands}
        
        for x, y, _ in self.islands:
            # Look right (horizontal)
            c = y + 1
            while c < self.n:
                if (x, c) in island_pos:
                    edges.append(((x, y), (x, c)))
                    break
                c += 1
            
            # Look down (vertical)
            r = x + 1
            while r < self.n:
                if (r, y) in island_pos:
                    edges.append(((x, y), (r, y)))
                    break
                r += 1
        
        return edges
    
    def is_valid_config(self, config):
        """Check if a configuration is valid (island degrees, no crossing bridges, connectivity)."""
        
        # 1. Check each island has correct number of bridges
        degree = {(x, y): 0 for x, y, _ in self.islands}
        
        for i, (a, b) in enumerate(self.edges):
            count = config[i]
            degree[a] += count
            degree[b] += count
        
        for x, y, required in self.islands:
            if degree[(x, y)] != required:
                return False
        
        # 2. Check no bridges cross
        for i in range(len(self.edges)):
            if config[i] == 0:
                continue
            for j in range(i + 1, len(self.edges)):
                if config[j] == 0:
                    continue
                a1, b1 = self.edges[i]
                a2, b2 = self.edges[j]
                if is_intersect(a1, b1, a2, b2):
                    return False
        
        # 3. Check connectivity
        edges = []
        for i, (a, b) in enumerate(self.edges):
            if config[i] > 0:
                edges.append((a, b, config[i]))
        return check_connectivity_from_edges(self.islands, edges)
    
    def build_output(self, config):
        """Build output matrix from configuration."""
        out = [["0" for _ in range(self.n)] for _ in range(self.n)]
        
        # Place islands
        for x, y, v in self.islands:
            out[x][y] = str(v)
        
        # Draw bridges
        for i, (a, b) in enumerate(self.edges):
            count = config[i]
            if count == 0:
                continue
            
            # Horizontal
            if a[0] == b[0]:
                row = a[0]
                symbol = "-" if count == 1 else "="
                for y in range(min(a[1], b[1]) + 1, max(a[1], b[1])):
                    out[row][y] = symbol
            # Vertical
            else:
                col = a[1]
                symbol = "|" if count == 1 else "$"
                for x in range(min(a[0], b[0]) + 1, max(a[0], b[0])):
                    out[x][col] = symbol
        
        return out
    
    def solve(self, timeout=300):
        """Solve puzzle using brute force search exploring all possible bridge configurations."""
        start_time = time.perf_counter()

        num_edges = len(self.edges)
        total_configs = 3 ** num_edges

        print(f"\n=== BRUTE FORCE ===")
        print(f"Number of edges: {num_edges}")
        print(f"Total configurations to try: {total_configs}")
        print(f"Timeout: {timeout}s")
        print("Starting brute force search...\n")

        checked = 0
        last_log = start_time

        for config in itertools.product([0, 1, 2], repeat=num_edges):
            checked += 1

            # Timeout check
            now = time.perf_counter()
            if now - start_time >= timeout:
                elapsed = now - start_time
                return None, elapsed

            # Log progress every 5 seconds or every 10000 configs
            if checked % 10000 == 0 or (now - last_log) >= 5.0:
                elapsed = now - start_time
                progress = (checked / total_configs) * 100
                rate = checked / elapsed if elapsed > 0 else 0
                last_log = now

            if self.is_valid_config(config):
                elapsed = time.perf_counter() - start_time
                print(f"\n Solution found after checking {checked:,} configurations!")
                print(f"Time: {elapsed:.6f}s")
                return self.build_output(config), elapsed

        elapsed = time.perf_counter() - start_time
        print(f"\n No solution found after checking all {total_configs:,} configurations")
        print(f"Time: {elapsed:.6f}s")
        return None, elapsed