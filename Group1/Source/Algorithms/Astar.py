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
# HELPER CLASS: DSU (Giữ nguyên - Vì nó nhanh)
# ============================================================
class DSU:
    def __init__(self, islands):
        self.parent = {isl.id: isl.id for isl in islands}
        self.num_components = len(islands)
    def find(self, i):
        if self.parent[i] != i: self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
    def union(self, i, j):
        root_i, root_j = self.find(i), self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j
            self.num_components -= 1
            return True
        return False

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

        # 2. CHUẨN BỊ INPUT
        self.bridge_pairs = []
        seen = set()
        for b in self.bridges:
            u, v, _ = b
            key = tuple(sorted((u.id, v.id)))
            if key in seen: continue
            seen.add(key)
            self.bridge_pairs.append((self.var_map[(u, v, 1)], self.var_map[(u, v, 2)]))

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
        return None, (time.time() - start_time)

    def _evaluate_state(self, state):
        # 1. Map assignment & Check CNF (Hard Constraint)
        assignment = {}
        for x in state["1"]: assignment[x] = True
        for x in state["0"]: assignment[x] = False

        for clause in self.clauses:
            violated = True
            satisfied = False
            for lit in clause:
                val = assignment.get(abs(lit))
                if val is None: 
                    violated = False
                    continue
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    violated = False
                    break
            if violated: return False

        # 2. Heuristic (Chỉ dùng DSU cho nhanh)
        dsu = DSU(self.islands)
        for var_id in state["1"]:
            if var_id in self.reverse_map:
                u, v, _, _ = self.reverse_map[var_id]
                dsu.union(u.id, v.id)
        
        # Tính h(x)
        # Weight = 10 (Hoặc 5) để cân bằng với g(x)
        # Nếu g(x) tăng 1, mà h(x) giảm 10 -> Thuật toán thấy "hời", sẽ đi tiếp.
        heuristic_weight = 10 
        hx = (dsu.num_components - 1) * heuristic_weight
        
        return [hx, dsu.num_components]

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