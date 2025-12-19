import itertools
from pysat.pb import PBEnc
from pysat.formula import CNF

# ==========================================
# CẤU TRÚC DỮ LIỆU CHUNG
# ==========================================
class Island:
    def __init__(self, r, c, val):
        self.r, self.c, self.val = r, c, val
        self.id = f"{r}_{c}"
    def __eq__(self, other):
        return isinstance(other, Island) and self.r == other.r and self.c == other.c
    def __hash__(self):
        return hash((self.r, self.c))
    def __repr__(self):
        return f"({self.r},{self.c})v{self.val}"

def parse_board(matrix):
    return [Island(r, c, matrix[r][c]) for r in range(len(matrix)) 
            for c in range(len(matrix[0])) if matrix[r][c] > 0]

def find_potential_bridges(grid, islands):
    rows, cols, bridges = len(grid), len(grid[0]), []
    for start_node in islands:
        r, c = start_node.r, start_node.c
        for nc in range(c + 1, cols):
            if grid[r][nc] != 0:
                bridges.append((start_node, next(i for i in islands if i.r == r and i.c == nc), 'H'))
                break
        for nr in range(r + 1, rows):
            if grid[nr][c] != 0:
                bridges.append((start_node, next(i for i in islands if i.r == nr and i.c == c), 'V'))
                break
    return bridges

def create_vars(bridges):
    var_map, counter = {}, 1
    for b in bridges:
        var_map[(b[0], b[1], 1)] = counter; counter += 1
        var_map[(b[0], b[1], 2)] = counter; counter += 1
    return var_map, counter - 1

# ==========================================
# VERSION 1: FIXED (Có quản lý top_id)
# ==========================================
def gen_v1_fixed(matrix):
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, last_id = create_vars(bridges)
    cnf_clauses = []
    
    # 1. Capacity with top_id management
    curr_id = last_id
    for island in islands:
        lits = [var_map[(u, v, k)] for (u, v, _) in bridges for k in [1, 2] if u == island or v == island]
        pb = PBEnc.equals(lits=lits, bound=island.val, top_id=curr_id, encoding=1)
        cnf_clauses.extend(pb.clauses)
        if pb.clauses:
            curr_id = max(max(abs(lit) for lit in cls) for cls in pb.clauses)
    
    # 2. Geometry
    for b in bridges:
        cnf_clauses.append([-var_map[(b[0], b[1], 2)], var_map[(b[0], b[1], 1)]])
    
    return cnf_clauses, curr_id

# ==========================================
# VERSION 2: ORIGINAL (Không quản lý top_id)
# ==========================================
def gen_v2_original(matrix):
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, last_id = create_vars(bridges)
    cnf_clauses = []
    
    # 1. Capacity WITHOUT top_id management
    for island in islands:
        lits = [var_map[(u, v, k)] for (u, v, _) in bridges for k in [1, 2] if u == island or v == island]
        pb = PBEnc.equals(lits=lits, bound=island.val, encoding=1) # Thiếu top_id
        cnf_clauses.extend(pb.clauses)
    
    # 2. Geometry
    for b in bridges:
        cnf_clauses.append([-var_map[(b[0], b[1], 2)], var_map[(b[0], b[1], 1)]])
        
    return cnf_clauses, "N/A (Broken)"

# ==========================================
# RUN TEST
# ==========================================
if __name__ == "__main__":
    # Ma trận 3x3 đơn giản: Hai đảo (2) đối diện nhau
    test_matrix = [
        [2, 0, 2],
        [0, 0, 0],
        [0, 0, 0]
    ]
    
    print("=== SO SÁNH SINH CLAUSE HASHIWOKAKERO ===")
    
    c1, max_v1 = gen_v1_fixed(test_matrix)
    c2, max_v2 = gen_v2_original(test_matrix)
    
    print(f"\n[V1 - FIXED]")
    print(f"- Số lượng Clause: {len(c1)}")
    print(f"- ID biến lớn nhất: {max_v1}")
    print(f"- 5 Clause đầu tiên: {c1[:5]}")
    
    print(f"\n[V2 - ORIGINAL]")
    print(f"- Số lượng Clause: {len(c2)}")
    print(f"- ID biến lớn nhất: {max_v2}")
    print(f"- 5 Clause đầu tiên: {c2[:5]}")
    
    print("\n--- PHÂN TÍCH ---")
    if any(lit in [1, 2] for cls in c2 for lit in cls if abs(lit) > 2):
        print("CẢNH BÁO: V2 đang sinh biến phụ trùng lặp với biến gốc (1, 2)!")
    else:
        print("V2 có thể may mắn chưa trùng, nhưng ID biến sẽ bị loạn khi map lớn.")