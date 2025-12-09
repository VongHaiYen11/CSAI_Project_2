import time
import itertools

class BruteForce:
    def __init__(self, matrix):
        self.matrix = matrix
        self.n = len(matrix)
        
        # Danh sách đảo: (row, col, value)
        self.islands = []
        for i in range(self.n):
            for j in range(self.n):
                if matrix[i][j] > 0:
                    self.islands.append((i, j, matrix[i][j]))
        
        # Tạo tất cả các cạnh có thể nối
        self.edges = self.generate_edges()
        
    def generate_edges(self):
        """Tìm tất cả các cặp đảo có thể nối (chỉ nhìn phải và xuống dưới)"""
        edges = []
        island_pos = {(x, y): True for x, y, _ in self.islands}
        
        for x, y, _ in self.islands:
            # Nhìn sang phải
            c = y + 1
            while c < self.n:
                if (x, c) in island_pos:
                    edges.append(((x, y), (x, c)))
                    break
                c += 1
            
            # Nhìn xuống dưới
            r = x + 1
            while r < self.n:
                if (r, y) in island_pos:
                    edges.append(((x, y), (r, y)))
                    break
                r += 1
        
        return edges
    
    def is_intersect(self, a1, b1, a2, b2):
        """Kiểm tra 2 cầu có cắt nhau không"""
        # Cùng endpoint → không cắt
        if a1 == a2 or a1 == b2 or b1 == a2 or b1 == b2:
            return False
        
        h1 = (a1[0] == b1[0])  # Bridge 1 ngang?
        h2 = (a2[0] == b2[0])  # Bridge 2 ngang?
        
        # Cùng hướng → không cắt
        if h1 == h2:
            return False
        
        # Đảm bảo bridge 1 là ngang
        if not h1:
            return self.is_intersect(a2, b2, a1, b1)
        
        # Bridge 1 ngang (hàng row), Bridge 2 dọc (cột col)
        row = a1[0]
        col = a2[1]
        
        y1, y2 = sorted([a1[1], b1[1]])
        x1, x2 = sorted([a2[0], b2[0]])
        
        # Cắt nếu cột của bridge 2 nằm giữa 2 đầu bridge 1
        # VÀ hàng của bridge 1 nằm giữa 2 đầu bridge 2
        return (y1 < col < y2) and (x1 < row < x2)
    
    def is_connected_with_config(self, config):
        """Kiểm tra liên thông với configuration cho trước"""
        n = len(self.islands)
        adj = [[] for _ in range(n)]
        
        # Map vị trí đảo → index
        pos_to_idx = {}
        for i, (x, y, _) in enumerate(self.islands):
            pos_to_idx[(x, y)] = i
        
        # Build adjacency list từ config
        for i, (a, b) in enumerate(self.edges):
            if config[i] > 0:  # Có cầu
                ia = pos_to_idx[a]
                ib = pos_to_idx[b]
                adj[ia].append(ib)
                adj[ib].append(ia)
        
        # DFS kiểm tra liên thông
        visited = [False] * n
        stack = [0]
        visited[0] = True
        
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if not visited[v]:
                    visited[v] = True
                    stack.append(v)
        
        return all(visited)
    
    def is_valid_config(self, config):
        """Kiểm tra một configuration có hợp lệ không"""
        
        # 1. Kiểm tra mỗi đảo có đúng số cầu theo yêu cầu
        degree = {(x, y): 0 for x, y, _ in self.islands}
        
        for i, (a, b) in enumerate(self.edges):
            count = config[i]
            degree[a] += count
            degree[b] += count
        
        for x, y, required in self.islands:
            if degree[(x, y)] != required:
                return False
        
        # 2. Kiểm tra cầu không cắt nhau
        for i in range(len(self.edges)):
            if config[i] == 0:
                continue
            for j in range(i + 1, len(self.edges)):
                if config[j] == 0:
                    continue
                a1, b1 = self.edges[i]
                a2, b2 = self.edges[j]
                if self.is_intersect(a1, b1, a2, b2):
                    return False
        
        # 3. Kiểm tra liên thông
        return self.is_connected_with_config(config)
    
    def build_output(self, config):
        """Xây dựng ma trận output từ configuration"""
        out = [["0" for _ in range(self.n)] for _ in range(self.n)]
        
        # Đặt đảo
        for x, y, v in self.islands:
            out[x][y] = str(v)
        
        # Vẽ cầu
        for i, (a, b) in enumerate(self.edges):
            count = config[i]
            if count == 0:
                continue
            
            # Ngang
            if a[0] == b[0]:
                row = a[0]
                symbol = "-" if count == 1 else "="
                for y in range(min(a[1], b[1]) + 1, max(a[1], b[1])):
                    out[row][y] = symbol
            # Dọc
            else:
                col = a[1]
                symbol = "|" if count == 1 else "$"
                for x in range(min(a[0], b[0]) + 1, max(a[0], b[0])):
                    out[x][col] = symbol
        
        return out
    
    def solve(self):
        """Brute Force: Thử tất cả các configuration"""
        start = time.perf_counter()
        
        num_edges = len(self.edges)
        total_configs = 3 ** num_edges
        
        print(f"\n=== BRUTE FORCE ===")
        print(f"Number of edges: {num_edges}")
        print(f"Total configurations to try: {total_configs}")
        print("Starting brute force search...\n")
        
        # Vét cạn tất cả các configuration
        checked = 0
        for config in itertools.product([0, 1, 2], repeat=num_edges):
            checked += 1
            
            # In progress mỗi 10000 lần thử (tùy chỉnh)
            if checked % 10000 == 0:
                print(f"Checked {checked}/{total_configs} configurations...")
            
            if self.is_valid_config(config):
                duration = time.perf_counter() - start
                print(f"\n✓ Solution found after checking {checked} configurations!")
                print(f"Time: {duration:.6f}s")
                return self.build_output(config), duration
        
        duration = time.perf_counter() - start
        print(f"\n✗ No solution found after checking all {total_configs} configurations")
        print(f"Time: {duration:.6f}s")
        return None, duration


# =============== MAIN TEST ===============

if __name__ == "__main__":
    matrix = [
        [0, 2, 0, 5, 0, 0, 2],
        [0, 0, 0, 0, 0, 0, 0],
        [4, 0, 2, 0, 2, 0, 4],
        [0, 0, 0, 0, 0, 0, 0],
        [0, 1, 0, 5, 0, 2, 0],
        [0, 0, 0, 0, 0, 0, 0],
        [4, 0, 0, 0, 0, 0, 3],
    ]
    
    solver = BruteForce(matrix)
    result, runtime = solver.solve()
    
    if result:
        print("\n--- RESULT MATRIX ---")
        for row in result:
            formatted = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
            print(formatted)
    else:
        print("\nNo solution exists.")

    print(f"\nTotal Time: {runtime:.6f}s")