# ==============================
# COMPARISON: MANUAL CNF vs PySAT PBEnc
# ==============================
import itertools
from pysat.pb import PBEnc

# --- Lặp lại class và hàm cơ bản từ CNF_udth ---
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
    islands = []
    for r in range(len(matrix)):
        for c in range(len(matrix[0])):
            val = matrix[r][c]
            if val > 0:
                islands.append(Island(r, c, val))
    return islands

def find_potential_bridges(grid, islands):
    rows, cols = len(grid), len(grid[0])
    bridges = []
    for start in islands:
        r, c = start.r, start.c
        # Horizontal
        for nc in range(c+1, cols):
            if grid[r][nc] != 0:
                end = next(i for i in islands if i.r == r and i.c == nc)
                bridges.append((start, end, 'H'))
                break
        # Vertical
        for nr in range(r+1, rows):
            if grid[nr][c] != 0:
                end = next(i for i in islands if i.r == nr and i.c == c)
                bridges.append((start, end, 'V'))
                break
    return bridges

def create_variables(bridges):
    var_map, reverse_map = {}, {}
    counter = 1
    for u, v, _ in bridges:
        var_map[(u,v,1)] = counter
        reverse_map[counter] = (u,v,1)
        counter += 1
        var_map[(u,v,2)] = counter
        reverse_map[counter] = (u,v,2)
        counter += 1
    return var_map, reverse_map, counter-1

# --- Manual CNF function ---
def exactly_k(vars_list, k):
    clauses = []
    n = len(vars_list)

    # Lower Bound (ít nhất k)
    r = n - k + 1
    if k > 0 and r > 0:
        for combo in itertools.combinations(vars_list, r):
            clauses.append(list(combo))

    # Upper Bound (nhiều nhất k)
    if k < n:
        for combo in itertools.combinations(vars_list, k + 1):
            clauses.append([-x for x in combo])

    return clauses

def manual_capacity_clauses(islands, bridges, var_map):
    clauses = []
    for isl in islands:
        connected = []
        for u,v,_ in bridges:
            if u==isl or v==isl:
                connected.append(var_map[(u,v,1)])
                connected.append(var_map[(u,v,2)])
        k = isl.val
        clauses.extend(exactly_k(connected, k))
    return remove_duplicate_clauses(clauses)

def remove_duplicate_clauses(cnf_clauses):
    """
    Loại bỏ clause trùng lặp.
    Mỗi clause được sắp xếp các literal để đảm bảo nhận dạng trùng lặp.
    """
    seen = set()
    unique_clauses = []

    for cl in cnf_clauses:
        cl_sorted = tuple(sorted(cl))
        if cl_sorted not in seen:
            seen.add(cl_sorted)
            unique_clauses.append(cl)
    
    return unique_clauses

# --- PySAT PBEnc function ---
def pysat_capacity_clauses(islands, bridges, var_map):
    from pysat.formula import CNF
    cnf = []
    top_id = max(var_map.values())
    for isl in islands:
        connected = []
        for u,v,_ in bridges:
            if u==isl or v==isl:
                connected.append(var_map[(u,v,1)])
                connected.append(var_map[(u,v,2)])
        pb = PBEnc.equals(lits=connected, bound=isl.val, top_id=top_id, encoding=1)
        print("Pb clause: ", pb.clauses)
        cnf.extend(pb.clauses)
        # Update top_id để tránh trùng biến phụ
        for cl in pb.clauses:
            for lit in cl:
                top_id = max(top_id, abs(lit))
    return remove_duplicate_clauses(cnf)

# --- Example matrix ---
matrix = [
    [0, 2, 0],
    [0, 0, 0],
    [1, 0, 1]
]

# --- Generate variables ---
islands = parse_board(matrix)
bridges = find_potential_bridges(matrix, islands)
var_map, reverse_map, num_vars = create_variables(bridges)

# --- Manual CNF ---
manual_cnf = manual_capacity_clauses(islands, bridges, var_map)

# --- PySAT CNF ---
pysat_cnf = pysat_capacity_clauses(islands, bridges, var_map)

# --- Print results ---
print("=== Manual CNF clauses ===")
for cl in manual_cnf:
    print(cl)
print(f"Total manual clauses: {len(manual_cnf)}\n")

print("=== PySAT PBEnc CNF clauses ===")
for cl in pysat_cnf:
    print(cl)
print(f"Total PySAT clauses: {len(pysat_cnf)}")
