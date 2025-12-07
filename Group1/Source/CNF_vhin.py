from pysat.solvers import Glucose3

# ----------- Parse board -----------

def parse_board(matrix):
    islands = []
    n = len(matrix)
    for i in range(n):
        for j in range(n):
            if matrix[i][j] != 0:
                islands.append((i, j))
    return islands

# ----------- Generate possible bridges -----------

def generate_possible_bridges(islands):
    bridges = []
    for i, a in enumerate(islands):
        for j in range(i + 1, len(islands)):
            b = islands[j]
            # same row or same column
            if not (a[0] == b[0] or a[1] == b[1]):
                continue

            # check no island in between
            blocked = False
            if a[0] == b[0]:  # horizontal (same row)
                y1, y2 = sorted((a[1], b[1]))
                for c in islands:
                    if c == a or c == b:
                        continue
                    if c[0] == a[0] and y1 < c[1] < y2:
                        blocked = True
                        break
            else:  # vertical (same column)
                x1, x2 = sorted((a[0], b[0]))
                for c in islands:
                    if c == a or c == b:
                        continue
                    if c[1] == a[1] and x1 < c[0] < x2:
                        blocked = True
                        break
            if blocked:
                continue

            bridges.append((a, b, 1))
            bridges.append((a, b, 2))
    return bridges

# ----------- Map bridges to literals -----------

def map_bridges_to_literals(bridges):
    bridge_to_lit = {}
    lit_to_bridge = {}
    for idx, b in enumerate(bridges, start=1):
        bridge_to_lit[b] = idx
        lit_to_bridge[idx] = b
    return bridge_to_lit, lit_to_bridge

# ----------- Combinations -----------

def generate_combinations(arr, r):
    if r == 0:
        return [[]]
    if r > len(arr):
        return []

    result = []

    def backtrack(start, path):
        if len(path) == r:
            result.append(path[:])
            return
        for i in range(start, len(arr)):
            path.append(arr[i])
            backtrack(i + 1, path)
            path.pop()
    backtrack(0, [])
    return result

# ----------- Exactly k of n -----------

def exactly_k_of_n_true(k, vars_list):
    n = len(vars_list)
    clauses = []
    min_true = n - k + 1
    for comb in generate_combinations(vars_list, min_true):
        clauses.append(list(comb))
    min_false = k + 1
    for comb in generate_combinations(vars_list, min_false):
        clauses.append([-v for v in comb])
    return clauses

# ----------- Avoid cross -----------

def avoid_crosses(vertical_bridges, horizontal_bridges, bridge_to_lit):
    clauses = []
    for v in vertical_bridges:
        for h in horizontal_bridges:
            col = v[0][1]  # vertical column
            x_low, x_high = sorted((v[0][0], v[1][0]))
            row = h[0][0]  # horizontal row
            y_low, y_high = sorted((h[0][1], h[1][1]))
            if y_low < col < y_high and x_low < row < x_high:
                clauses.append([-bridge_to_lit[v], -bridge_to_lit[h]])
    return clauses

# ----------- Convert solution to grid -----------

def bridges_to_grid(matrix, solution_bridges):
    n = len(matrix)
    grid = [[str(matrix[i][j]) for j in range(n)] for i in range(n)]

    for b in solution_bridges:
        a, c, k = b
        if a[0] == c[0]:  # horizontal
            row = a[0]
            y1, y2 = sorted((a[1], c[1]))
            cell_char = "-" if k == 1 else "="
            for col in range(y1 + 1, y2):
                grid[row][col] = cell_char
        else:  # vertical
            col = a[1]
            x1, x2 = sorted((a[0], c[0]))
            cell_char = "|" if k == 1 else "$"
            for row in range(x1 + 1, x2):
                grid[row][col] = cell_char
    return grid

# ----------- Main SAT Solver -----------

def solve_hashiwokakero(matrix):
    islands = parse_board(matrix)
    bridges = generate_possible_bridges(islands)
    bridge_to_lit, lit_to_bridge = map_bridges_to_literals(bridges)
    cnf = []

    # exactly k bridges per island
    for island in islands:
        island_bridges = [bridge_to_lit[b] for b in bridges if b[0] == island or b[1] == island]
        k = matrix[island[0]][island[1]]
        cnf += exactly_k_of_n_true(k, island_bridges)

    # avoid crosses
    verticals = [b for b in bridges if b[0][1] == b[1][1]]
    horizontals = [b for b in bridges if b[0][0] == b[1][0]]
    cnf += avoid_crosses(verticals, horizontals, bridge_to_lit)

    solver = Glucose3()
    for clause in cnf:
        solver.add_clause(clause)

    if solver.solve():
        model = solver.get_model()
        solution = [lit_to_bridge[lit] for lit in model if lit > 0]
        return solution
    else:
        return None

# ----------- Example -----------

matrix = [
    [0, 2, 0, 5, 0, 0, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 2, 0, 2, 0, 4],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 5, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 0, 0, 0, 0, 3],
]

solution = solve_hashiwokakero(matrix)
if solution:
    output_grid = bridges_to_grid(matrix, solution)
    for row in output_grid:
        print(row)
else:
    print("No solution found")
