import os
import sys
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from is_intersect import is_intersect
from connectivity import check_connectivity_from_edges


class TimeoutException(Exception):
    """Exception raised when algorithm exceeds time limit."""
    pass


class Backtracking:
    """Backtracking solver for Hashiwokakero puzzles using depth-first search with pruning."""
    
    def __init__(self, matrix):
        """Initialize backtracking solver."""
        self.matrix = matrix
        self.n = len(matrix)

        # List of islands: (row, col, value)
        self.islands = []
        for i in range(self.n):
            for j in range(self.n):
                if matrix[i][j] > 0:
                    self.islands.append((i, j, matrix[i][j]))

        # Map: island position -> required degree
        self.island_value = {}
        for x, y, v in self.islands:
            self.island_value[(x, y)] = v

        # Current number of bridges connected to each island
        self.current_degree = {}
        for x, y, _ in self.islands:
            self.current_degree[(x, y)] = 0

        # All possible bridge edges
        self.edges = self.generate_edges()

        # Current solution: (start_pos, end_pos, bridge_count)
        self.solution = []

    def generate_edges(self):
        """Generate all possible bridge edges going right or down."""
        edges = []
        island_pos = {}
        for x, y, _ in self.islands:
            island_pos[(x, y)] = True

        for x, y, _ in self.islands:
            # Look right
            c = y + 1
            while c < self.n:
                if (x, c) in island_pos:
                    edges.append(((x, y), (x, c)))
                    break
                c += 1

            # Look down
            r = x + 1
            while r < self.n:
                if (r, y) in island_pos:
                    edges.append(((x, y), (r, y)))
                    break
                r += 1

        return edges

    def can_add_bridge(self, a, b):
        """Check if a bridge can be placed without crossing existing bridges."""
        for x, y, _ in self.solution:
            if is_intersect(a, b, x, y):
                return False
        return True

    def place_bridge(self, a, b, count):
        """Place a bridge in the current solution."""
        self.current_degree[a] += count
        self.current_degree[b] += count
        self.solution.append((a, b, count))

    def remove_bridge(self, a, b, count):
        """Remove the last bridge from the current solution."""
        self.current_degree[a] -= count
        self.current_degree[b] -= count
        self.solution.pop()

    def backtracking_edge(self, idx):
        """Recursive backtracking over bridge edges."""
        self.nodes_visited += 1

        # Check timeout every ~1000 nodes or 1s
        if self.nodes_visited % 1000 == 0:
            elapsed = time.perf_counter() - self.start_time
            if elapsed > self.timeout:
                raise TimeoutException()

            if elapsed - self.last_log_time >= 5:
                self.last_log_time = elapsed
        
        # All edges processed
        if idx == len(self.edges):
            # Check degrees
            for x, y, need in self.islands:
                if self.current_degree[(x, y)] != need:
                    return False
            # Check connectivity
            return check_connectivity_from_edges(self.islands, self.solution)

        a, b = self.edges[idx]
        va = self.island_value[a]
        vb = self.island_value[b]

        # Try 0, 1, 2 bridges
        for count in (0, 1, 2):
            if self.current_degree[a] + count > va:
                continue
            if self.current_degree[b] + count > vb:
                continue
            if count > 0 and not self.can_add_bridge(a, b):
                continue

            if count > 0:
                self.place_bridge(a, b, count)

            if self.backtracking_edge(idx + 1):
                return True

            if count > 0:
                self.remove_bridge(a, b, count)

        return False

    def solve(self, timeout=300):
        """Solve the puzzle using backtracking."""
        print("\n=== BACKTRACKING ===")
        print(f"Edges: {len(self.edges)} | Islands: {len(self.islands)}")
        print(f"Timeout: {timeout}s")
        print("Starting search...\n")

        self.start_time = time.perf_counter()
        self.timeout = timeout
        self.nodes_visited = 0
        self.last_log_time = 0.0

        try:
            ok = self.backtracking_edge(0)
            duration = time.perf_counter() - self.start_time

            if ok:
                print(f"\n✓ Solution found")
                print(f"Nodes visited: {self.nodes_visited:,}")
                print(f"Time: {duration:.6f}s")
                return self.build_output_matrix(), duration
            else:
                print(f"\n✗ No solution exists")
                print(f"Nodes visited: {self.nodes_visited:,}")
                print(f"Time: {duration:.6f}s")
                return None, duration
        
        except TimeoutException:
            duration = time.perf_counter() - self.start_time
            print(f"\n⏱ TIMEOUT after {duration:.2f}s")
            print(f"Nodes visited: {self.nodes_visited:,}")
            return None, duration

    def build_output_matrix(self):
        """Build output matrix from solution."""
        out = [["0" for _ in range(self.n)] for _ in range(self.n)]

        # Place islands
        for x, y, v in self.islands:
            out[x][y] = str(v)

        # Draw bridges
        for a, b, count in self.solution:
            if a[0] == b[0]:
                row = a[0]
                for y in range(min(a[1], b[1]) + 1, max(a[1], b[1])):
                    out[row][y] = "-" if count == 1 else "="
            else:
                col = a[1]
                for x in range(min(a[0], b[0]) + 1, max(a[0], b[0])):
                    out[x][col] = "|" if count == 1 else "$"

        return out
