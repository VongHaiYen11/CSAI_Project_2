from pysat.solvers import Glucose3
import itertools

# ==========================================
# 1. CẤU TRÚC DỮ LIỆU & PARSER
# ==========================================

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

# ==========================================
# 4. KIỂM TRA LIÊN THÔNG & SOLVER
# ==========================================

def check_connectivity(model, islands, reverse_map):
    adj = {isl.id: [] for isl in islands}
    active_vars = [x for x in model if x > 0]
    
    for var_id in active_vars:
        if var_id in reverse_map:
            u, v, _, _ = reverse_map[var_id]
            # Chỉ thêm cạnh nếu chưa tồn tại (tránh add 2 lần do cầu đôi)
            if v.id not in adj[u.id]: adj[u.id].append(v.id)
            if u.id not in adj[v.id]: adj[v.id].append(u.id)
            
    # BFS
    if not islands: return True
    start_id = islands[0].id
    queue = [start_id]
    visited = {start_id}
    
    while queue:
        curr = queue.pop(0)
        for neighbor in adj[curr]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
                
    return len(visited) == len(islands)

def solve_hashi(matrix):
    # Setup dữ liệu
    islands = parse_board(matrix)
    bridges = find_potential_bridges(matrix, islands)
    var_map, reverse_map, num_vars = create_variables(bridges)
    
    # Tạo CNF
    cnf = []
    cnf.extend(generate_capacity_constraints(islands, bridges, var_map))
    cnf.extend(generate_geometry_constraints(bridges, var_map))
    
    # Chạy Solver
    with Glucose3(bootstrap_with=cnf) as solver:
        while solver.solve():
            model = solver.get_model()
            if check_connectivity(model, islands, reverse_map):
                return model, reverse_map # Tìm thấy!
            else:
                solver.add_clause([-x for x in model]) # Chặn nghiệm sai
                
    return None, None

# ==========================================
# 5. XUẤT KẾT QUẢ DẠNG LƯỚI (OUTPUT GRID)
# ==========================================

def print_solution_grid(matrix, model, reverse_map):
    rows = len(matrix)
    cols = len(matrix[0])
    
    # 1. Tạo lưới ban đầu chỉ có số đảo
    output = [[' ' for _ in range(cols)] for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if matrix[r][c] != 0:
                output[r][c] = str(matrix[r][c])
            else:
                output[r][c] = '0' # Hoặc khoảng trắng nếu muốn đẹp

    # 2. Lọc các biến True (được chọn)
    active_vars = [x for x in model if x > 0]
    
    # 3. Gom nhóm cầu (để biết cầu đơn hay cầu đôi)
    # Key: (u, v), Value: số lượng cầu (1 hoặc 2)
    final_bridges = {}
    for var_id in active_vars:
        if var_id in reverse_map:
            u, v, idx, direction = reverse_map[var_id]
            key = (u, v)
            if key not in final_bridges:
                final_bridges[key] = {'count': 0, 'dir': direction}
            final_bridges[key]['count'] = max(final_bridges[key]['count'], idx)

    # 4. Vẽ cầu lên lưới
    for (u, v), info in final_bridges.items():
        count = info['count']
        direction = info['dir']
        
        # Chọn ký tự vẽ
        if direction == 'H':
            char = '-' if count == 1 else '='
            # Vẽ từ cột u.c + 1 đến v.c
            for c in range(u.c + 1, v.c):
                output[u.r][c] = char
        else: # Vertical
            char = '|' if count == 1 else '$' # Dùng ký tự $ cho cầu dọc đôi
            # Vẽ từ hàng u.r + 1 đến v.r
            for r in range(u.r + 1, v.r):
                output[r][u.c] = char

    # 5. In ra màn hình
    print("\n--- KẾT QUẢ ---")
    for row in output:
        # Format đẹp kiểu list string như yêu cầu
        print(f"[{', '.join(f'{x:>2}' for x in row)}]")

# ==========================================
# 6. CHẠY THỬ (MAIN)
# ==========================================

# Input Test Case
matrix = [
    [0, 2, 0, 5, 0, 0, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 2, 0, 2, 0, 4],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 5, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 0, 0, 0, 0, 3],
]

model, reverse_map = solve_hashi(matrix)

if model:
    print_solution_grid(matrix, model, reverse_map)
else:
    print("Không tìm thấy nghiệm!")