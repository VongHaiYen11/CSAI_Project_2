# ==========================================
# FILE: CNF_udth.py
# MÔ TẢ: Chỉ chứa cấu trúc dữ liệu và hàm sinh luật CNF
# ==========================================
import itertools

class Island:
    def __init__(self, r, c, val):
        self.r = r
        self.c = c
        self.val = val
        self.id = f"{r}_{c}"

    def __eq__(self, other):
        return isinstance(other, Island) and self.r == other.r and self.c == other.c

    def __hash__(self):
        return hash((self.r, self.c))

    def __repr__(self):
        return f"Island({self.r},{self.c}, val={self.val})"

def parse_board(matrix):
    rows = len(matrix)
    cols = len(matrix[0])
    islands = []
    for r in range(rows):
        for c in range(cols):
            val = matrix[r][c]
            if val > 0:
                islands.append(Island(r, c, val))
    return islands

def find_potential_bridges(grid, islands):
    rows = len(grid)
    cols = len(grid[0])
    bridges = [] 
    
    for start_node in islands:
        r, c = start_node.r, start_node.c
        # 1. Ngang (Horizontal)
        for nc in range(c + 1, cols):
            if grid[r][nc] != 0: 
                end_node = next(isl for isl in islands if isl.r == r and isl.c == nc)
                bridges.append((start_node, end_node, 'H')) 
                break 
        # 2. Dọc (Vertical)
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
        # Cầu 1
        var_map[(u, v, 1)] = counter
        reverse_map[counter] = (u, v, 1, direction)
        counter += 1
        # Cầu 2
        var_map[(u, v, 2)] = counter
        reverse_map[counter] = (u, v, 2, direction)
        counter += 1
        
    return var_map, reverse_map, counter - 1

def exactly_k(vars_list, k):
    clauses = []
    n = len(vars_list)
    if k > 0:
        for combo in itertools.combinations(vars_list, n - k + 1):
            clauses.append(list(combo))
    for combo in itertools.combinations(vars_list, k + 1):
        clauses.append([-x for x in combo])
    return clauses

def generate_cnf_clauses(matrix):
    """Hàm tổng hợp để sinh toàn bộ luật CNF"""
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, reverse_map, num_vars = create_variables(bridges)
    
    clauses = []
    
    # 1. Luật Capacity (Số lượng cầu nối với đảo)
    for island in islands:
        connected_vars = []
        for b in bridges:
            u, v, _ = b
            if u == island or v == island:
                connected_vars.append(var_map[(u, v, 1)])
                connected_vars.append(var_map[(u, v, 2)])
        clauses.extend(exactly_k(connected_vars, island.val))

    # 2. Luật Geometry (Cầu 2 cần Cầu 1)
    for b in bridges:
        u, v, _ = b
        var1 = var_map[(u, v, 1)]
        var2 = var_map[(u, v, 2)]
        clauses.append([-var2, var1]) 

    # 3. Luật Crossing (Cấm cắt nhau)
    horiz_bridges = [b for b in bridges if b[2] == 'H']
    vert_bridges = [b for b in bridges if b[2] == 'V']
    for h in horiz_bridges:
        for v in vert_bridges:
            h_r = h[0].r
            h_c1, h_c2 = sorted((h[0].c, h[1].c))
            v_c = v[0].c
            v_r1, v_r2 = sorted((v[0].r, v[1].r))
            
            if (h_c1 < v_c < h_c2) and (v_r1 < h_r < v_r2):
                id_h = var_map[(h[0], h[1], 1)]
                id_v = var_map[(v[0], v[1], 1)]
                clauses.append([-id_h, -id_v])
                
    return clauses, reverse_map, islands, bridges, var_map, num_vars