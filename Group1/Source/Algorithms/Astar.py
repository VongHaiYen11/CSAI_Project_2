import time
import heapq
import os
import sys
from copy import deepcopy
import itertools 

# ============================================================
# IMPORT SETUP (Giữ nguyên)
# ============================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

try:
    from CNF import generate_cnf_clauses, Island
except ImportError as e:
    raise e

# ============================================================
# HELPER FUNCTION: BFS Connectivity Check
# ============================================================
def check_connectivity_bfs(islands, active_bridge_vars, reverse_map):
    """
    Check connectivity using BFS.
    Returns (num_components, is_connected)
    """
    if not islands:
        return 1, True
    
    # Build adjacency list
    adj = {isl.id: [] for isl in islands}
    for var_id in active_bridge_vars:
        if var_id in reverse_map:
            u, v, _, _ = reverse_map[var_id]
            if v.id not in adj[u.id]:
                adj[u.id].append(v.id)
            if u.id not in adj[v.id]:
                adj[v.id].append(u.id)
    
    # BFS to count connected components
    visited = set()
    num_components = 0
    
    for isl in islands:
        if isl.id in visited:
            continue
        
        # Start BFS from this unvisited island
        num_components += 1
        queue = [isl.id]
        visited.add(isl.id)
        
        while queue:
            curr = queue.pop(0)  # BFS: use queue (FIFO)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    
    is_connected = (num_components == 1)
    return num_components, is_connected

# ============================================================
# CLASS A* (Đã sửa logic g(x))
# ============================================================
class AStar:
    def __init__(self):
        self.solution_vars = None
        self.matrix = None 

    def solve(self, matrix):
        print("\n--- Preprocessing ---")
        self.matrix = matrix

        # 1. SETUP
        (self.clauses, 
         self.reverse_map, 
         self.islands, 
         self.bridges, 
         self.var_map, 
         self.num_vars) = generate_cnf_clauses(matrix)
        
        print(f"Setup done: {len(self.islands)} islands.")

        # 2. CHUẨN BỊ INPUT - Create bridge pairs for A* search
        # Mỗi cầu (giữa 2 đảo) có 2 biến:
        #   var1: tồn tại ít nhất 1 cầu
        #   var2: tồn tại cầu thứ 2
        self.bridge_pairs = []
        seen = set()
        for b in self.bridges:
            u, v, _ = b
            # Use sorted island IDs as key to avoid duplicates
            key = tuple(sorted((u.id, v.id)))
            if key in seen: 
                continue
            seen.add(key)
            # Get the two variables for this bridge pair
            var1 = self.var_map.get((u, v, 1))
            var2 = self.var_map.get((u, v, 2))
            if var1 is not None and var2 is not None:
                self.bridge_pairs.append((var1, var2))

        # 2.a. Tiền xử lý cho ràng buộc SỨC CHỨA (degree của đảo)
        # Với mỗi đảo, lưu danh sách các (var1, var2) của những cầu nối tới nó.
        self.island_incident = {isl.id: [] for isl in self.islands}
        self.island_demand = {isl.id: isl.val for isl in self.islands}
        for (u, v, _) in self.bridges:
            v1 = self.var_map[(u, v, 1)]
            v2 = self.var_map[(u, v, 2)]
            self.island_incident[u.id].append((v1, v2))
            self.island_incident[v.id].append((v1, v2))

        # 2.b. Tiền xử lý cho ràng buộc KHÔNG CẮT NHAU
        # Tạo danh sách các cặp cầu (ngang, dọc) cắt nhau.
        horiz_bridges = [b for b in self.bridges if b[2] == 'H']
        vert_bridges = [b for b in self.bridges if b[2] == 'V']
        self.crossing_pairs = []
        for h in horiz_bridges:
            for v in vert_bridges:
                h_r = h[0].r
                h_c1, h_c2 = sorted((h[0].c, h[1].c))
                v_c = v[0].c
                v_r1, v_r2 = sorted((v[0].r, v[1].r))
                # Kiểm tra giao cắt hình chữ thập
                if (h_c1 < v_c < h_c2) and (v_r1 < h_r < v_r2):
                    id_h1 = self.var_map[(h[0], h[1], 1)]
                    id_v1 = self.var_map[(v[0], v[1], 1)]
                    self.crossing_pairs.append((id_h1, id_v1))

        counter = itertools.count() 

        print("\n--- Starting A* (Standard Version) ---")
        start_time = time.perf_counter()

        # Init Queue
        pq = []
        # gx = 0 ở trạng thái đầu tiên
        initial_state = {
            "index": 0, "0": [], "1": [],
            "gx": 0, "fx": 0, "components": len(self.islands)
        }
        
        # Đánh giá node đầu tiên
        res = self._evaluate_state(initial_state) # Trả về [hx, components]
        if res:
            hx = res[0]
            initial_state["components"] = res[1]
            initial_state["fx"] = initial_state["gx"] + hx # f(x) = g(x) + h(x)
            heapq.heappush(pq, (initial_state["fx"], 0, next(counter), initial_state))

        visited_nodes = 0
        
        # 3. VÒNG LẶP CHÍNH
        while pq:
            curr_fx, _, _, state = heapq.heappop(pq)
            visited_nodes += 1

            # Goal Check
            if state["index"] >= len(self.bridge_pairs):
                # All bridge decisions made. Because every expanded state has already
                # passed `_evaluate_state` (CNF consistency w.r.t bridge variables),
                # we only need to check connectivity here.
                if state["components"] == 1:
                    duration = time.perf_counter() - start_time
                    self.solution_vars = state["1"]
                    print(f"Solved! Visited nodes: {visited_nodes}")
                    return self.get_result_matrix(), duration
                continue

            # Branching
            var1, var2 = self.bridge_pairs[state["index"]]
            
            # 3 Lựa chọn: 0, 1, 2 cầu
            options = [
                ([],           [var1, var2]), 
                ([var1],       [var2]),       
                ([var1, var2], [])            
            ]

            for add_to_1, add_to_0 in options:
                new_state = deepcopy(state)
                new_state["1"].extend(add_to_1)
                new_state["0"].extend(add_to_0)
                new_state["index"] += 1 # Tăng độ sâu
                
                # --- PHẦN QUAN TRỌNG: TÍNH LẠI GX, FX ---
                # g(x): Chi phí đi đến đây (mỗi bước tốn 1 đơn vị công sức)
                new_state["gx"] = state["gx"] + 1 
                
                # h(x): Ước lượng còn bao xa
                eval_res = self._evaluate_state(new_state)
                if eval_res:
                    new_hx = eval_res[0]
                    new_state["components"] = eval_res[1]
                    
                    # f(x) = g(x) + h(x)
                    new_state["fx"] = new_state["gx"] + new_hx
                    
                    # Push vào heap
                    heapq.heappush(pq, (new_state["fx"], -new_state["index"], next(counter), new_state))

        print("No solution found.")
        return None, (time.perf_counter() - start_time)

    def _evaluate_state(self, state):
        # 1. Map assignment (chỉ cho biến cầu var1, var2)
        assignment = {}
        for x in state["1"]: 
            assignment[x] = True
        for x in state["0"]: 
            assignment[x] = False
        #
        # 2. RÀNG BUỘC HÌNH HỌC: KHÔNG CẮT NHAU
        # Nếu 2 cầu (1 ngang, 1 dọc) cắt nhau thì không được cùng tồn tại.
        for h1, v1 in self.crossing_pairs:
            if assignment.get(h1) and assignment.get(v1):
                return False

        # 3. RÀNG BUỘC SỨC CHỨA (degree) CHO MỖI ĐẢO
        # Với mỗi đảo, ta tính:
        #   - min_deg: bậc nhỏ nhất có thể (nếu sau này chọn tối thiểu)
        #   - max_deg: bậc lớn nhất có thể (nếu sau này chọn tối đa)
        # Nếu min_deg > demand hoặc max_deg < demand => vô nghiệm, cắt tỉa.
        for isl in self.islands:
            isl_id = isl.id
            demand = self.island_demand[isl_id]
            min_deg = 0
            max_deg = 0

            for v1, v2 in self.island_incident[isl_id]:
                a1 = assignment.get(v1)
                a2 = assignment.get(v2)

                if a1 is True:
                    if a2 is True:
                        # Hai cầu đều chắc chắn tồn tại
                        min_deg += 2
                        max_deg += 2
                    elif a2 is False:
                        # Chỉ có 1 cầu
                        min_deg += 1
                        max_deg += 1
                    else:  # a2 is None
                        # Đã có 1 cầu, có thể thêm cầu 2
                        min_deg += 1
                        max_deg += 2
                elif a1 is False:
                    if a2 is True:
                        # Vi phạm: CNF đã mã hoá v2 -> v1, nên không thể v1=0, v2=1
                        return False
                    elif a2 is False:
                        # Không có cầu nào ở cặp này
                        # min_deg += 0, max_deg += 0
                        pass
                    else:  # a2 is None
                        # v1=0 thì v2 không thể là 1 trong tương lai (do v2->v1)
                        # nên min=max=0 ở cặp này
                        pass
                else:  # a1 is None
                    if a2 is True:
                        # Nếu v2=1 thì bắt buộc v1=1, nhưng v1 chưa set -> coi là không hợp lệ
                        return False
                    elif a2 is False:
                        # Chưa biết v1, nhưng có thể chọn v1=1 sau này -> tối đa +1
                        max_deg += 1
                    else:  # cả hai đều None
                        # Có thể chọn 0,1 hoặc 2 cầu sau này -> [0,2]
                        max_deg += 2

            if min_deg > demand or max_deg < demand:
                return False

        # 4. Heuristic (Sử dụng BFS để kiểm tra liên thông)
        # Only use bridge variables (those in reverse_map) for connectivity
        num_components, _ = check_connectivity_bfs(
            self.islands, state["1"], self.reverse_map
        )
        
        # Tính h(x)
        # Weight = 10 (Hoặc 5) để cân bằng với g(x)
        # Nếu g(x) tăng 1, mà h(x) giảm 10 -> Thuật toán thấy "hời", sẽ đi tiếp.
        heuristic_weight = 10 
        hx = (num_components - 1) * heuristic_weight
        
        return [hx, num_components]

    def get_result_matrix(self):
        # (Giữ nguyên code cũ của bạn)
        if not self.solution_vars: return None
        rows, cols = len(self.matrix), len(self.matrix[0])
        grid_str = [["0" for _ in range(cols)] for _ in range(rows)]
        for isl in self.islands:
            grid_str[isl.r][isl.c] = str(isl.val)
        sol_set = set(self.solution_vars)
        for b in self.bridges:
            u, v, direction = b
            id1 = self.var_map[(u, v, 1)]
            id2 = self.var_map[(u, v, 2)]
            if id1 not in sol_set: continue 
            is_double = id2 in sol_set
            symbol = ""
            if direction == 'H':
                symbol = "=" if is_double else "-" 
                r = u.r
                c_start, c_end = sorted((u.c, v.c))
                for c in range(c_start + 1, c_end): grid_str[r][c] = symbol
            else:
                symbol = "$" if is_double else "|"
                c = u.c
                r_start, r_end = sorted((u.r, v.r))
                for r in range(r_start + 1, r_end): grid_str[r][c] = symbol
        return grid_str

    def print_solution(self):
        grid = self.get_result_matrix()
        if not grid: return
        print("\n--- KẾT QUẢ ---")
        for row in grid:
            formatted = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
            print(formatted)