# ==========================================
# FILE: CNF_udth.py
# MÔ TẢ: Chỉ chứa cấu trúc dữ liệu và hàm sinh luật CNF
# ==========================================
import itertools

class Island:
    def __init__(self, r, c, val):
        self.r = r  # Hàng (Row)
        self.c = c  # Cột (Col)
        self.val = val # Số ghi trên đảo
        self.id = f"{r}_{c}" # ID định danh duy nhất (string)

    # Cần 2 hàm này để dùng Island làm Key trong Dictionary (var_map)
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
    
    for i, start_node in enumerate(islands):
        r, c = start_node.r, start_node.c
        
        # 1. Nhìn sang PHẢI (Horizontal)
        for nc in range(c + 1, cols):
            if grid[r][nc] != 0: 
                # Tìm đảo đích có tọa độ (r, nc)
                end_node = next(isl for isl in islands if isl.r == r and isl.c == nc)
                bridges.append((start_node, end_node, 'H')) 
                break 
            
        # 2. Nhìn xuống DƯỚI (Vertical)
        for nr in range(r + 1, rows):
            if grid[nr][c] != 0: 
                # Tìm đảo đích có tọa độ (nr, c)
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

def exactly_k(vars_list, k):
    clauses = []
    n = len(vars_list)
    
    # Lower Bound (Ít nhất k)
    if k > 0:
        for combo in itertools.combinations(vars_list, n - k + 1):
            clauses.append(list(combo))
    
    # Upper Bound (Nhiều nhất k)
    for combo in itertools.combinations(vars_list, k + 1):
        clauses.append([-x for x in combo])
        
    return clauses

def generate_capacity_constraints(islands, bridges, var_map):
    clauses = []
    for island in islands:
        connected_vars = []
        for b in bridges:
            u, v, _ = b
            if u == island or v == island:
                connected_vars.append(var_map[(u, v, 1)])
                connected_vars.append(var_map[(u, v, 2)])
        
        k = island.val
        new_clauses = exactly_k(connected_vars, k)
        clauses.extend(new_clauses)
    return clauses

def generate_geometry_constraints(bridges, var_map):
    clauses = []
    
    # 1. Luật phụ: Cầu 2 cần Cầu 1 (-Var2 v Var1)
    for b in bridges:
        u, v, _ = b
        var1 = var_map[(u, v, 1)]
        var2 = var_map[(u, v, 2)]
        clauses.append([-var2, var1]) 

    # 2. Luật Cấm Cắt Nhau
    horiz_bridges = [b for b in bridges if b[2] == 'H']
    vert_bridges = [b for b in bridges if b[2] == 'V']

    for h in horiz_bridges:
        for v in vert_bridges:
            h_r = h[0].r
            h_c1, h_c2 = sorted((h[0].c, h[1].c))
            
            v_c = v[0].c
            v_r1, v_r2 = sorted((v[0].r, v[1].r))
            
            # Cắt nhau nếu Dọc nằm giữa Ngang VÀ Ngang nằm giữa Dọc
            if (h_c1 < v_c < h_c2) and (v_r1 < h_r < v_r2):
                id_h = var_map[(h[0], h[1], 1)]
                id_v = var_map[(v[0], v[1], 1)]
                clauses.append([-id_h, -id_v])
                
    return clauses

def generate_cnf_clauses(matrix):
    """Hàm tổng hợp để sinh toàn bộ luật CNF"""
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, reverse_map, num_vars = create_variables(bridges)
    
    cnf = []
    cnf.extend(generate_capacity_constraints(islands, bridges, var_map))
    cnf.extend(generate_geometry_constraints(bridges, var_map))

    # # 2. Luật Geometry (Cầu 2 cần Cầu 1)
    # for b in bridges:
    #     u, v, _ = b
    #     var1 = var_map[(u, v, 1)]
    #     var2 = var_map[(u, v, 2)]
    #     clauses.append([-var2, var1]) 

    # # 3. Luật Crossing (Cấm cắt nhau)
    # horiz_bridges = [b for b in bridges if b[2] == 'H']
    # vert_bridges = [b for b in bridges if b[2] == 'V']
    # for h in horiz_bridges:
    #     for v in vert_bridges:
    #         h_r = h[0].r
    #         h_c1, h_c2 = sorted((h[0].c, h[1].c))
    #         v_c = v[0].c
    #         v_r1, v_r2 = sorted((v[0].r, v[1].r))
            
    #         if (h_c1 < v_c < h_c2) and (v_r1 < h_r < v_r2):
    #             id_h = var_map[(h[0], h[1], 1)]
    #             id_v = var_map[(v[0], v[1], 1)]
    #             clauses.append([-id_h, -id_v])
                
    return cnf, reverse_map, islands, bridges, var_map, num_vars