from pysat.solvers import Glucose3

# ----------- Data Classes -----------

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return f"({self.x},{self.y})"

class Bridge:
    def __init__(self, start: Point, end: Point, bridge_idx: int):
        self.start = start
        self.end = end
        self.bridge_idx = bridge_idx  # 1 hoặc 2

    def __eq__(self, other):
        # Undirected equality: (A,B,k) == (B,A,k)
        return (
            isinstance(other, Bridge)
            and self.bridge_idx == other.bridge_idx
            and (
                (self.start == other.start and self.end == other.end)
                or (self.start == other.end and self.end == other.start)
            )
        )

    def __hash__(self):
        # Use frozenset so {A,B} == {B,A} for the same bridge_idx
        return hash((frozenset({self.start, self.end}), self.bridge_idx))

    def __str__(self):
        return f"br_{self.start}_{self.end}_{self.bridge_idx}"

# ----------- Parse matrix input -----------

def parse_board(matrix):
    """
    matrix: nxn, 0 = không có đảo, >0 = số cầu yêu cầu
    Trả về:
        islands: list of Points
    """
    n = len(matrix)
    islands = []
    for i in range(n):
        for j in range(n):
            if matrix[i][j] != 0:
                islands.append(Point(i,j))
    return islands

# ----------- Generate possible bridges -----------

def generate_possible_bridges(islands):
    """
    Generate all valid bridge candidates between islands (without crossing check).
    - Only between islands on the same row or column.
    - At most 2 bridges between a pair.
    - Each unordered pair (A,B) is considered exactly once.
    - No other island is allowed between A and B along that line.
    """
    bridges = []

    for i, a in enumerate(islands):
        for j in range(i + 1, len(islands)):
            b = islands[j]

            # Only aligned islands can be connected
            if not (a.x == b.x or a.y == b.y):
                continue

            # Enforce "no island in between" along the row/column
            blocked = False
            if a.x == b.x:  # vertical
                y1, y2 = sorted((a.y, b.y))
                for c in islands:
                    if c is a or c is b:
                        continue
                    if c.x == a.x and y1 < c.y < y2:
                        blocked = True
                        break
            else:  # a.y == b.y, horizontal
                x1, x2 = sorted((a.x, b.x))
                for c in islands:
                    if c is a or c is b:
                        continue
                    if c.y == a.y and x1 < c.x < x2:
                        blocked = True
                        break

            if blocked:
                continue

            # Unique unordered pair (a,b); create 1-bridge and 2-bridge variants
            bridges.append(Bridge(a, b, 1))
            bridges.append(Bridge(a, b, 2))
    return bridges

# ----------- Mapping Bridge -> Literal -----------

def map_bridges_to_literals(bridges):
    bridge_to_lit = {}
    lit_to_bridge = {}
    for idx, b in enumerate(bridges, start=1):
        bridge_to_lit[b] = idx
        lit_to_bridge[idx] = b
    return bridge_to_lit, lit_to_bridge

# ----------- Combinations (manual, no itertools) -----------

def generate_combinations(arr, r):
    """
    Generate all r-length combinations of elements in arr.
    Equivalent to itertools.combinations(arr, r) but implemented manually.
    """
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
            
            # 1. Check if the vertical bridge's column (v.start.x) is STRICTLY between 
            #    the horizontal bridge's endpoints.
            x1, x2 = sorted((h.start.x, h.end.x))
            v_x = v.start.x
            x_cross = (x1 < v_x < x2)

            # 2. Check if the horizontal bridge's row (h.start.y) is STRICTLY between
            #    the vertical bridge's endpoints.
            y1, y2 = sorted((v.start.y, v.end.y))
            h_y = h.start.y
            y_cross = (y1 < h_y < y2)
            
            # Intersection (crossing) only occurs if both conditions are met.
            if x_cross and y_cross:
                clauses.append([-bridge_to_lit[v], -bridge_to_lit[h]])
    return clauses


# ----------- Convert solution to output grid -----------

def bridges_to_grid(matrix, solution_bridges):
    """
    Convert a list of chosen Bridge objects into the required output format:
    - Grid is based on the original matrix size (n x n).
    - Islands remain as their number (as strings, e.g. "2").
    - Empty cells remain "0".
    - Bridges:
        - Horizontal, single: "-"
        - Horizontal, double: "="
        - Vertical, single:   "|"
        - Vertical, double:   "$"
    Returns:
        A list of rows, where each row is a list of string cells.
    """
    n = len(matrix)

    # Start with islands / empty cells as strings
    grid = [[str(matrix[i][j]) for j in range(n)] for i in range(n)]

    for b in solution_bridges:
        a = b.start
        c = b.end

        # Horizontal bridge
        if a.x == c.x:
            # same row index? -> actually x is row, y is column; vertical when x differs
            pass

    # Correct handling: x is row, y is column
    grid = [[str(matrix[i][j]) for j in range(n)] for i in range(n)]

    for b in solution_bridges:
        a, c = b.start, b.end

        # Vertical bridge: same column (y), different row (x)
        if a.y == c.y:
            col = a.y
            x1, x2 = sorted((a.x, c.x))
            cell_char = "|" if b.bridge_idx == 1 else "$"
            for row in range(x1 + 1, x2):
                grid[row][col] = cell_char

        # Horizontal bridge: same row (x), different column (y)
        elif a.x == c.x:
            row = a.x
            y1, y2 = sorted((a.y, c.y))
            cell_char = "-" if b.bridge_idx == 1 else "="
            for col in range(y1 + 1, y2):
                grid[row][col] = cell_char

    return grid


# ----------- Main Solver Function -----------

def solve_hashiwokakero(matrix):
    islands = parse_board(matrix)
    bridges = generate_possible_bridges(islands)
    bridge_to_lit, lit_to_bridge = map_bridges_to_literals(bridges)
    cnf = []

    # Constraint: exactly k bridges per island
    for island in islands:
        # Include all bridges incident to this island (start OR end)
        island_bridges = [
            bridge_to_lit[b]
            for b in bridges
            if b.start == island or b.end == island
        ]
        k = matrix[island.x][island.y]
        cnf += exactly_k_of_n_true(k, island_bridges)

    # Constraint: avoid cross
    verticals = [b for b in bridges if b.start.x == b.end.x]
    horizontals = [b for b in bridges if b.start.y == b.end.y]
    cnf += avoid_crosses(verticals, horizontals, bridge_to_lit)

    # Solve
    solver = Glucose3()
    for clause in cnf:
        solver.add_clause(clause)

    if solver.solve():
        model = solver.get_model()
        solution = []
        for lit in model:
            if lit > 0:
                solution.append(lit_to_bridge[lit])
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