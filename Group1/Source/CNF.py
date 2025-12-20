from pysat.pb import PBEnc
from is_intersect import is_intersect


class Island:
    """Represents an island in the Hashiwokakero puzzle."""
    
    def __init__(self, r, c, val):
        self.r = r
        self.c = c
        self.val = val
        self.id = f"{r}_{c}"

    def __eq__(self, other):
        """Check if two islands are at the same position."""
        return isinstance(other, Island) and self.r == other.r and self.c == other.c

    def __hash__(self):
        """Hash based on position for use in sets and dictionaries."""
        return hash((self.r, self.c))

    def __repr__(self):
        """String representation of the island."""
        return f"Island({self.r},{self.c}, val={self.val})"



class CNFGenerator:
    """Converts a Hashiwokakero puzzle board into CNF clauses for SAT solving."""
    
    def parse_board(self, matrix):
        """Convert a numeric matrix into a list of Island objects."""
        rows = len(matrix)
        cols = len(matrix[0])
        islands = []
        
        for r in range(rows):
            for c in range(cols):
                val = matrix[r][c]
                if val > 0:
                    islands.append(Island(r, c, val))
        
        return islands
    
    def find_potential_bridges(self, grid, islands):
        """Find all potential bridges between islands. Only considers bridges going right or down."""
        rows = len(grid)
        cols = len(grid[0])
        bridges = []
        
        for start_node in islands:
            r, c = start_node.r, start_node.c
            
            # Look right (horizontal)
            for nc in range(c + 1, cols):
                if grid[r][nc] != 0:
                    end_node = next(isl for isl in islands if isl.r == r and isl.c == nc)
                    bridges.append((start_node, end_node, 'H'))
                    break
            
            # Look down (vertical)
            for nr in range(r + 1, rows):
                if grid[nr][c] != 0:
                    end_node = next(isl for isl in islands if isl.r == nr and isl.c == c)
                    bridges.append((start_node, end_node, 'V'))
                    break
        
        return bridges
    
    def create_variables(self, bridges):
        """Create variable mappings for bridge variables. Each bridge has two variables."""
        var_map = {}
        reverse_map = {}
        counter = 1
        
        for bridge in bridges:
            u, v, direction = bridge
            
            # Variable for first bridge
            var_map[(u, v, 1)] = counter
            reverse_map[counter] = (u, v, 1, direction)
            counter += 1
            
            # Variable for second bridge
            var_map[(u, v, 2)] = counter
            reverse_map[counter] = (u, v, 2, direction)
            counter += 1
        
        return var_map, reverse_map, counter - 1
    
    def generate_capacity_constraints(self, islands, bridges, var_map, top_id):
        """Generate CNF clauses enforcing island capacity constraints using PBEnc."""
        cnf_clauses = []
        current_max_id = top_id

        for island in islands:
            connected_vars = []
            for (u, v, _) in bridges:
                if u == island or v == island:
                    # Each bridge variable contributes 1 unit if True
                    connected_vars.append(var_map[(u, v, 1)])
                    connected_vars.append(var_map[(u, v, 2)])

            # Enforce: sum of True variables equals island value
            pb = PBEnc.equals(
                lits=connected_vars,
                bound=island.val,
                top_id=current_max_id,
                encoding=1  # Sequential Counter encoding
            )
            
            cnf_clauses.extend(pb.clauses)
            
            # Update current_max_id based on newly generated auxiliary variables
            if pb.clauses:
                for clause in pb.clauses:
                    for lit in clause:
                        current_max_id = max(current_max_id, abs(lit))

        return cnf_clauses, current_max_id
    
    def generate_bridge_dependency_constraints(self, bridges, var_map):
        """Generate CNF clauses enforcing bridge dependency: bridge 2 requires bridge 1."""
        clauses = []
        for bridge in bridges:
            u, v, _ = bridge
            var1 = var_map[(u, v, 1)]
            var2 = var_map[(u, v, 2)]
            # Clause: -var2 OR var1 (if var2 then var1)
            clauses.append([-var2, var1])
        
        return clauses
    
    def generate_crossing_constraints(self, bridges, var_map):
        """Generate CNF clauses preventing bridge crossings."""
        clauses = []
        
        horizontal_bridges = [b for b in bridges if b[2] == 'H']
        vertical_bridges = [b for b in bridges if b[2] == 'V']

        for h_bridge in horizontal_bridges:
            for v_bridge in vertical_bridges:
                # Use is_intersect function to check if bridges cross
                if is_intersect(h_bridge[0], h_bridge[1], v_bridge[0], v_bridge[1]):
                    var_h1 = var_map[(h_bridge[0], h_bridge[1], 1)]
                    var_v1 = var_map[(v_bridge[0], v_bridge[1], 1)]
                    # At least one bridge must be absent: -var_h1 OR -var_v1
                    clauses.append([-var_h1, -var_v1])
        
        return clauses
    
    def remove_duplicate_clauses(self, cnf_clauses):
        """Remove duplicate clauses from a CNF formula."""
        seen = set()
        unique_clauses = []

        for clause in cnf_clauses:
            clause_sorted = tuple(sorted(clause))
            if clause_sorted not in seen:
                seen.add(clause_sorted)
                unique_clauses.append(clause)
        
        return unique_clauses
    
    def generate_cnf_clauses(self, matrix):
        """Generate complete CNF formula for a Hashiwokakero puzzle."""
        islands = self.parse_board(matrix)
        bridges = self.find_potential_bridges(matrix, islands)
        var_map, reverse_map, last_bridge_id = self.create_variables(bridges)
        
        cnf = []
        
        dep_clauses = self.generate_bridge_dependency_constraints(bridges, var_map)
        cnf.extend(dep_clauses)
        
        geo_clauses = self.generate_crossing_constraints(bridges, var_map)
        cnf.extend(geo_clauses)
        
        cap_clauses, final_num_vars = self.generate_capacity_constraints(
            islands, bridges, var_map, last_bridge_id
        )
        cnf.extend(cap_clauses)

        cnf = self.remove_duplicate_clauses(cnf)

        return cnf, reverse_map, islands, bridges, var_map, final_num_vars