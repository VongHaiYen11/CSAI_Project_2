import time

class TimeoutException(Exception):
    """Raised when backtracking exceeds time limit"""
    pass

class Backtracking:
    def __init__(self, matrix):
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

        # Current solution: (a, b, count)
        self.solution = []

    # ---------------------------------------------------------
    # Generate all possible edges (right and down only)
    def generate_edges(self):
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

    # ---------------------------------------------------------
    # Check if two bridges intersect
    def is_intersect(self, a1, b1, a2, b2):
        # Share endpoint -> not intersect
        if a1 == a2 or a1 == b2 or b1 == a2 or b1 == b2:
            return False

        h1 = (a1[0] == b1[0])
        h2 = (a2[0] == b2[0])

        # Same direction -> cannot intersect
        if h1 == h2:
            return False

        # Ensure first bridge is horizontal
        if not h1:
            return self.is_intersect(a2, b2, a1, b1)

        row = a1[0]
        col = a2[1]

        y1 = min(a1[1], b1[1])
        y2 = max(a1[1], b1[1])

        x1 = min(a2[0], b2[0])
        x2 = max(a2[0], b2[0])

        return (y1 < col < y2) and (x1 < row < x2)

    # ---------------------------------------------------------
    # Check if graph is connected
    def is_connected(self):
        if len(self.islands) == 0:
            return True

        n = len(self.islands)
        adj = [[] for _ in range(n)]

        # Build mapping (position -> index)
        pos_to_idx = {}
        for i in range(n):
            x, y, _ = self.islands[i]
            pos_to_idx[(x, y)] = i

        # Fill adjacency from placed bridges
        for a, b, count in self.solution:
            if count == 0:
                continue
            ia = pos_to_idx[a]
            ib = pos_to_idx[b]
            adj[ia].append(ib)
            adj[ib].append(ia)

        # DFS using stack
        visited = [False] * n
        stack = [0]
        visited[0] = True

        while stack:
            u = stack.pop()
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)

        # Check all visited
        for v in visited:
            if not v:
                return False
        return True

    # ---------------------------------------------------------
    # Check if we can place bridge without crossing
    def can_add_bridge(self, a, b):
        for x, y, _ in self.solution:
            if self.is_intersect(a, b, x, y):
                return False
        return True

    # ---------------------------------------------------------
    # Place / remove bridges
    def place_bridge(self, a, b, count):
        self.current_degree[a] += count
        self.current_degree[b] += count
        self.solution.append((a, b, count))

    def remove_bridge(self, a, b, count):
        self.current_degree[a] -= count
        self.current_degree[b] -= count
        self.solution.pop()

    # ---------------------------------------------------------
    # Backtracking over edges
    def backtracking_edge(self, idx):
        self.nodes_visited += 1

        # Check timeout every ~1000 nodes or 1s
        if self.nodes_visited % 1000 == 0:
            elapsed = time.perf_counter() - self.start_time
            if elapsed > self.timeout:
                raise TimeoutException()

            if elapsed - self.last_log_time >= 5:
                # print(f"Progress: {self.nodes_visited:,} nodes | "
                #       f"Depth: {idx}/{len(self.edges)} | "
                #       f"Time: {elapsed:.2f}s")
                self.last_log_time = elapsed
        
        # All edges processed
        if idx == len(self.edges):
            # Check degrees
            for x, y, need in self.islands:
                if self.current_degree[(x, y)] != need:
                    return False
            # Check connectivity
            return self.is_connected()

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

    # ---------------------------------------------------------
    # Solve the puzzle
    def solve(self, timeout=300):
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

    # ---------------------------------------------------------
    # Build final matrix with bridges
    def build_output_matrix(self):
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


# ------------------- RUN -------------------
# matrix = [
#     [0, 2, 0, 5, 0, 0, 2],
#     [0, 0, 0, 0, 0, 0, 0],
#     [4, 0, 2, 0, 2, 0, 4],
#     [0, 0, 0, 0, 0, 0, 0],
#     [0, 1, 0, 5, 0, 2, 0],
#     [0, 0, 0, 0, 0, 0, 0],
#     [4, 0, 0, 0, 0, 0, 3],
# ]

# solver = Backtracking(matrix)
# result, runtime = solver.solve()

# if result is None:
#     print("No solution")
# else:
#     for row in result:
#         print(row)

# print("Time:", runtime)

# if __name__ == "__main__":
#     # Test case nhỏ
#     matrix_small = [
#         [0, 2, 0, 5, 0, 0, 2],
#         [0, 0, 0, 0, 0, 0, 0],
#         [4, 0, 2, 0, 2, 0, 4],
#         [0, 0, 0, 0, 0, 0, 0],
#         [0, 1, 0, 5, 0, 2, 0],
#         [0, 0, 0, 0, 0, 0, 0],
#         [4, 0, 0, 0, 0, 0, 3],
#     ]
    
#     # Test case lớn
#     matrix_large = [
#         [3, 0, 2, 0, 3, 0, 2],
#         [0, 0, 0, 0, 0, 0, 0],
#         [2, 0, 4, 0, 3, 0, 3],
#         [0, 0, 0, 0, 0, 0, 0],
#         [3, 0, 2, 0, 2, 0, 2],
#         [0, 0, 0, 0, 0, 0, 0],
#         [2, 0, 3, 0, 2, 0, 2],
#     ]
    
#     print("Testing with SMALL matrix:")
#     solver1 = Backtracking(matrix_small)
#     result1, runtime1 = solver1.solve(timeout=60)  # 60s timeout for test
    
#     if result1:
#         print("\n--- RESULT MATRIX ---")
#         for row in result1:
#             formatted = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
#             print(formatted)
#     else:
#         print("\nNo solution found (or timeout).")
    
#     print("\n" + "="*60)
#     print("\nTesting with LARGE matrix:")
#     solver2 = Backtracking(matrix_large)
#     result2, runtime2 = solver2.solve(timeout=10)  # 10s timeout for demo
    
#     if result2:
#         print("\n--- RESULT MATRIX ---")
#         for row in result2:
#             formatted = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
#             print(formatted)
#     else:
#         print("\nNo solution found (or timeout).")
