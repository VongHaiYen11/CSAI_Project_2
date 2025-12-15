import time
import heapq
import os
import sys
from copy import deepcopy
import itertools 

# ============================================================
# 1. SETUP ĐƯỜNG DẪN IMPORT
# ============================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import các hàm từ file CNF_udth.py nằm ở thư mục cha
try:
    from CNF_udth import (
        parse_board, 
        find_potential_bridges, 
        create_variables, 
        generate_capacity_constraints, 
        generate_geometry_constraints,
        Island
    )
except ImportError as e:
    print("Lỗi Import: Không tìm thấy file CNF_udth.py hoặc các hàm cần thiết.")
    print("Hãy chắc chắn file Astar.py nằm trong folder Algorithms và CNF_udth.py nằm trong folder Source.")
    raise e

# ============================================================
# PHẦN 2: CLASS A* (Logic giải thuật)
# ============================================================

class DSU:
    """Helper class cho Heuristic"""
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

class AStar:
    def __init__(self):
        self.solution_vars = None
        self.matrix = None # Lưu matrix input để dùng khi tạo kết quả

    def solve(self, matrix):
        print("\n--- Preprocessing ---")
        # start_time = time.perf_counter()
        self.matrix = matrix
        
        # 1. SETUP
        self.islands = parse_board(matrix)
        self.bridges = find_potential_bridges(matrix, self.islands)
        self.var_map, self.reverse_map, self.num_vars = create_variables(self.bridges)
        
        # Sinh clauses
        self.clauses = generate_capacity_constraints(self.islands, self.bridges, self.var_map)
        self.clauses += generate_geometry_constraints(self.bridges, self.var_map)
        
        print(f"Setup done: {len(self.islands)} islands, {len(self.clauses)} clauses.")

        # 2. CHUẨN BỊ A*
        self.bridge_pairs = []
        seen = set()
        for b in self.bridges:
            u, v, _ = b
            key = tuple(sorted((u.id, v.id)))
            if key in seen: continue
            seen.add(key)
            self.bridge_pairs.append((self.var_map[(u, v, 1)], self.var_map[(u, v, 2)]))

        # --- TẠO COUNTER ĐỂ FIX LỖI SO SÁNH DICT ---
        counter = itertools.count() 

        print("\n--- Starting A* solver ---")
        start_time = time.perf_counter()

        # Init Queue (Min-Heap)
        pq = []
        initial_state = {
            "index": 0, "0": [], "1": [],
            "gx": 0, "fx": float('inf'), "components": len(self.islands)
        }
        
        # Đánh giá node đầu tiên
        res = self._evaluate_state(initial_state)
        if res:
            initial_state["gx"], initial_state["fx"], initial_state["components"] = res[0], res[0]+res[1], res[2]
            # Push: (fx, -index, count, state)
            heapq.heappush(pq, (initial_state["fx"], 0, next(counter), initial_state))

        visited = 0
        
        # 3. VÒNG LẶP CHÍNH
        while pq:
            # Pop: Lấy 4 phần tử
            curr_fx, _, _, state = heapq.heappop(pq)
            visited += 1

            # Goal Check
            if state["index"] >= len(self.bridge_pairs):
                if state["components"] == 1:
                    duration = time.perf_counter() - start_time
                    
                    self.solution_vars = state["1"]
                    
                    # --- TRẢ VỀ KẾT QUẢ + THỜI GIAN ---
                    result_matrix = self.get_result_matrix()
                    return result_matrix, duration
                
                continue

            # Branching (3 hướng: 0, 1, 2 cầu)
            var1, var2 = self.bridge_pairs[state["index"]]
            options = [
                ([],           [var1, var2]), # Case 0 cầu
                ([var1],       [var2]),       # Case 1 cầu
                ([var1, var2], [])            # Case 2 cầu
            ]

            for add_to_1, add_to_0 in options:
                new_state = deepcopy(state)
                new_state["1"].extend(add_to_1)
                new_state["0"].extend(add_to_0)
                new_state["index"] += 1
                
                eval_res = self._evaluate_state(new_state)
                if eval_res:
                    new_state["gx"] = eval_res[0]
                    new_state["fx"] = eval_res[0] + eval_res[1]
                    new_state["components"] = eval_res[2]
                    # Push: Thêm next(counter) vào tuple
                    heapq.heappush(pq, (new_state["fx"], -new_state["index"], next(counter), new_state))

        print("No solution found.")
        return None, (time.time() - start_time)

    def _evaluate_state(self, state):
        # Map assignment
        assignment = {}
        for x in state["1"]: assignment[x] = True
        for x in state["0"]: assignment[x] = False

        # 1. Check CNF
        for clause in self.clauses:
            violated = True
            satisfied = False
            for lit in clause:
                val = assignment.get(abs(lit))
                if val is None: # Chưa gán
                    violated = False
                    continue
                if (lit > 0 and val) or (lit < 0 and not val):
                    satisfied = True
                    violated = False
                    break
            if violated: return False

        # 2. Check Liên Thông (Heuristic)
        dsu = DSU(self.islands)
        for var_id in state["1"]:
            if var_id in self.reverse_map:
                u, v, _, _ = self.reverse_map[var_id]
                dsu.union(u.id, v.id)
        
        gx = 0 
        hx = (dsu.num_components - 1) * 10
        return [gx, hx, dsu.num_components]

    def get_result_matrix(self):
        """Hàm helper để tạo ma trận kết quả (List 2D)"""
        if not self.solution_vars: return None
        
        rows, cols = len(self.matrix), len(self.matrix[0])
        # Tạo lưới rỗng chứa string "0"
        grid_str = [["0" for _ in range(cols)] for _ in range(rows)]
        
        # Điền số đảo
        for isl in self.islands:
            grid_str[isl.r][isl.c] = str(isl.val)
            
        # Điền cầu
        sol_set = set(self.solution_vars)
        for b in self.bridges:
            u, v, direction = b
            id1 = self.var_map[(u, v, 1)]
            id2 = self.var_map[(u, v, 2)]
            
            if id1 not in sol_set: continue # Ko có cầu
            
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

    # def print_solution(self):
    #     """In kết quả ra màn hình sử dụng get_result_matrix"""
    #     grid = self.get_result_matrix()
    #     if not grid: return

    #     print("\n--- KẾT QUẢ ---")
    #     for row in grid:
    #         formatted = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
    #         print(formatted)

# ============================================================
# PHẦN 3: MAIN DEMO (INPUT TỪ HÌNH 1)
# ============================================================

# if __name__ == "__main__":
#     matrix_input = [
#         [2,0,0,2,0,1,0],
#           [0,0,2,0,4,0,4],
#           [0,0,0,1,0,0,0],
#           [
#             2,0,4,0,0,0,0],
#            [ 0,0,0,0,2,0,4],
#             [1,0,3,0,0,0,0],
#            [ 0,1,0,3,0,0,2]
#     ]

#     solver = AStar()
    
#     # Lấy kết quả trả về: Ma trận + Thời gian
#     result_grid, run_time = solver.solve(matrix_input)
    
#     if result_grid:
#         print(f"\nTime returned: {run_time}s")
#         print("Result Matrix returned:")
#         # Duyệt qua từng dòng và in format đẹp
#         for row in result_grid:
#             # Tạo chuỗi: [ "0" , "2" , "=" ... ]
#             formatted_row = "[ " + " , ".join([f"'{x}'" for x in row]) + " ]"
#             print(formatted_row)