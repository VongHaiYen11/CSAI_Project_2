# ==========================================
# FILE: CNF_udth.py
# MÔ TẢ: Sinh CNF cho bài Hashiwokakero (Fix lỗi quản lý biến PBEnc)
# ==========================================
import itertools
from pysat.pb import PBEnc
from pysat.formula import CNF

class Island:
    def __init__(self, r, c, val):
        self.r = r  # Hàng (Row)
        self.c = c  # Cột (Col)
        self.val = val # Số ghi trên đảo
        self.id = f"{r}_{c}" # ID định danh duy nhất (string)

    def __eq__(self, other):
        return isinstance(other, Island) and self.r == other.r and self.c == other.c

    def __hash__(self):
        return hash((self.r, self.c))

    def __repr__(self):
        return f"Island({self.r},{self.c}, val={self.val})"

def parse_board(matrix):
    """Chuyển ma trận số thành danh sách đối tượng Island"""
    rows = len(matrix)
    cols = len(matrix[0])
    islands = []
    for r in range(rows):
        for c in range(cols):
            val = matrix[r][c]
            if val > 0:
                islands.append(Island(r, c, val))
    return islands

# ==========================================
# 2. LOGIC TÌM CẦU & QUẢN LÝ BIẾN
# ==========================================

def find_potential_bridges(grid, islands):
    rows = len(grid)
    cols = len(grid[0])
    bridges = [] 
    
    for start_node in islands:
        r, c = start_node.r, start_node.c
        
        # 1. Nhìn sang PHẢI (Horizontal)
        for nc in range(c + 1, cols):
            if grid[r][nc] != 0: 
                end_node = next(isl for isl in islands if isl.r == r and isl.c == nc)
                bridges.append((start_node, end_node, 'H')) 
                break 
            
        # 2. Nhìn xuống DƯỚI (Vertical)
        for nr in range(r + 1, rows):
            if grid[nr][c] != 0: 
                end_node = next(isl for isl in islands if isl.r == nr and isl.c == c)
                bridges.append((start_node, end_node, 'V')) 
                break
    return bridges

def create_variables(bridges):
    var_map = {} 
    reverse_map = {} 
    counter = 1
    
    for b in bridges:
        u, v, direction = b
        # Biến cho Cầu 1
        var_map[(u, v, 1)] = counter
        reverse_map[counter] = (u, v, 1, direction)
        counter += 1
        
        # Biến cho Cầu 2
        var_map[(u, v, 2)] = counter
        reverse_map[counter] = (u, v, 2, direction)
        counter += 1
        
    return var_map, reverse_map, counter - 1

# ==========================================
# 3. SINH LUẬT CNF (CONSTRAINTS)
# ==========================================

def generate_capacity_constraints(islands, bridges, var_map, top_id):
    """
    Sửa lỗi quan trọng: Cập nhật top_id liên tục để tránh trùng biến phụ của PBEnc
    """
    cnf_clauses = []
    current_max_id = top_id

    for island in islands:
        connected_vars = []
        for (u, v, _) in bridges:
            if u == island or v == island:
                # Mỗi biến Bridge-1 đóng góp 1 đơn vị, Bridge-2 đóng góp 1 đơn vị
                connected_vars.append(var_map[(u, v, 1)])
                connected_vars.append(var_map[(u, v, 2)])

        # Tổng số biến True phải bằng island.val
        pb = PBEnc.equals(
            lits=connected_vars,
            bound=island.val,
            top_id=current_max_id,
            encoding=1 # Sequential Counter
        )
        
        cnf_clauses.extend(pb.clauses)
        
        # Cập nhật current_max_id dựa trên các biến phụ mới sinh ra
        if pb.clauses:
            for clause in pb.clauses:
                for lit in clause:
                    current_max_id = max(current_max_id, abs(lit))

    return cnf_clauses, current_max_id

def generate_geometry_constraints(bridges, var_map):
    clauses = []
    
    # 1. Luật phụ: Cầu 2 tồn tại thì Cầu 1 BẮT BUỘC phải tồn tại (-Var2 v Var1)
    for b in bridges:
        u, v, _ = b
        v1 = var_map[(u, v, 1)]
        v2 = var_map[(u, v, 2)]
        clauses.append([-v2, v1]) 

    # 2. Luật Cấm Cắt Nhau (Crossing)
    horiz_bridges = [b for b in bridges if b[2] == 'H']
    vert_bridges = [b for b in bridges if b[2] == 'V']

    for h in horiz_bridges:
        for v in vert_bridges:
            h_r = h[0].r
            h_c1, h_c2 = sorted((h[0].c, h[1].c))
            
            v_c = v[0].c
            v_r1, v_r2 = sorted((v[0].r, v[1].r))
            
            # Kiểm tra giao cắt hình chữ thập
            if (h_c1 < v_c < h_c2) and (v_r1 < h_r < v_r2):
                id_h1 = var_map[(h[0], h[1], 1)]
                id_v1 = var_map[(v[0], v[1], 1)]
                # Không thể có ít nhất 1 cầu ngang VÀ ít nhất 1 cầu dọc cùng lúc
                clauses.append([-id_h1, -id_v1])
                
    return clauses

def generate_cnf_clauses(matrix):
    """Hàm tổng hợp chính"""
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, reverse_map, last_bridge_id = create_variables(bridges)
    
    cnf = []
    
    # 1. Sinh luật hình học (Chỉ dùng các biến cầu hiện có)
    geo_clauses = generate_geometry_constraints(bridges, var_map)
    cnf.extend(geo_clauses)
    
    # 2. Sinh luật sức chứa (Có sinh thêm biến phụ)
    cap_clauses, final_num_vars = generate_capacity_constraints(
        islands, bridges, var_map, last_bridge_id
    )
    cnf.extend(cap_clauses)

    return cnf, reverse_map, islands, bridges, var_map, final_num_vars