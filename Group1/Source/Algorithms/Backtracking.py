class Backtracking:
    def __init__(self, matrix):
        self.matrix = matrix
        self.n = len(matrix)

        self.islands = []
        for i in range(self.n):
            for j in range(self.n):
                if matrix[i][j] > 0:
                    self.islands.append((i, j, matrix[i][j]))

        self.island_value = {(x, y): v for (x, y, v) in self.islands}
        self.edges = self.generate_edges()

        self.current_degree = {(x, y): 0 for (x, y, v) in self.islands}

        # list of (a, b, count)
        self.solution = []

    # ---------------------------------------------------------
    def generate_edges(self):
        edges = []
        island_pos = {(x, y): v for (x, y, v) in self.islands} # Speed up the searching process (for a neighbor island)

        for (x, y, v) in self.islands:
            # RIGHT
            c = y + 1
            while c < self.n:
                if (x, c) in island_pos:
                    edges.append(((x, y), (x, c)))
                    break
                c += 1

            # DOWN
            r = x + 1
            while r < self.n:
                if (r, y) in island_pos:
                    edges.append(((x, y), (r, y)))
                    break
                r += 1

        return edges

    # ---------------------------------------------------------
    def is_intersect(self, a1, b1, a2, b2):
        # Nếu hai cầu có chung endpoint → không tính là intersect
        if a1 == a2 or a1 == b2 or b1 == a2 or b1 == b2:
            return False

        # Kiểm tra orientation theo grid
        horizontal1 = (a1[0] == b1[0])  # cùng row → ngang
        horizontal2 = (a2[0] == b2[0])

        # Cùng hướng → không thể cắt nhau
        if horizontal1 and horizontal2:
            return False
        if not horizontal1 and not horizontal2:
            return False

        # Đảo thứ tự để bridge1 luôn là horizontal
        if not horizontal1 and horizontal2:
            return self.is_intersect(a2, b2, a1, b1)

        # Bây giờ:
        # bridge1: horizontal (cùng row)
        # bridge2: vertical   (cùng column)

        row_h = a1[0]      # row của horizontal
        col_v = a2[1]      # column của vertical

        # Khoảng horizontal của bridge1
        y_low  = min(a1[1], b1[1])
        y_high = max(a1[1], b1[1])

        # Khoảng vertical của bridge2
        x_low  = min(a2[0], b2[0])
        x_high = max(a2[0], b2[0])

        # Kiểm tra giao điểm: col_v nằm trong horizontal, row_h nằm trong vertical
        return (y_low < col_v < y_high) and (x_low < row_h < x_high)


    # ---------------------------------------------------------
    def can_add_bridge(self, a, b):
        for (start, end, _) in self.solution:
            if self.is_intersect(a, b, start, end):
                return False
        return True

    # ---------------------------------------------------------
    def place_bridge(self, a, b, count):
        self.current_degree[a] += count
        self.current_degree[b] += count
        self.solution.append((a, b, count))

    def remove_bridge(self, a, b, count):
        self.current_degree[a] -= count
        self.current_degree[b] -= count
        self.solution.pop()

    # ---------------------------------------------------------
    def backtracking_edge(self, brigde_idx):
        if brigde_idx == len(self.edges):
            for (x, y, island_val) in self.islands:
                if self.current_degree[(x, y)] != island_val:
                    return False
            return True

        a, b = self.edges[brigde_idx]
        va = self.island_value[a]
        vb = self.island_value[b]

        for count in [0, 1, 2]:
            if self.current_degree[a] + count > va:
                continue
            if self.current_degree[b] + count > vb:
                continue
            if count > 0 and not self.can_add_bridge(a, b):
                continue

            if count > 0:
                self.place_bridge(a, b, count)

            if self.backtracking_edge(brigde_idx + 1):
                return True

            if count > 0:
                self.remove_bridge(a, b, count)

        return False

    # ---------------------------------------------------------
    def solve(self):
        ok = self.backtracking_edge(0)
        res = self.build_output_matrix()
        return ok, res

    # ---------------------------------------------------------
    # Build output matrix with symbols
    # ---------------------------------------------------------
    def build_output_matrix(self):
        out = [["0" for _ in range(self.n)] for _ in range(self.n)]

        # put islands
        for x, y, v in self.islands:
            out[x][y] = str(v)

        # fill bridges into matrix
        for a, b, count in self.solution:
            if a[0] == b[0]:  # horizontal
                row = a[0]
                for y in range(min(a[1], b[1]) + 1, max(a[1], b[1])):
                    out[row][y] = "-" if count == 1 else "="
            else:  # vertical
                col = a[1]
                for x in range(min(a[0], b[0]) + 1, max(a[0], b[0])):
                    out[x][col] = "|" if count == 1 else "$"

        return out



matrix = [
    [0, 2, 0, 5, 0, 0, 2],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 2, 0, 2, 0, 4],
    [0, 0, 0, 0, 0, 0, 0],
    [0, 1, 0, 5, 0, 2, 0],
    [0, 0, 0, 0, 0, 0, 0],
    [4, 0, 0, 0, 0, 0, 3],
]

solver = Backtracking(matrix)
ok, final_grid = solver.solve()

print("Solved:", ok)
for row in final_grid:
    print(row)
