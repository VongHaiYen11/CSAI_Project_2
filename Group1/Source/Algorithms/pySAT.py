# ==========================================
# FILE: HashiSolver.py
# MÔ TẢ: Chứa hàm solve_hashi và logic check liên thông
# ==========================================
from pysat.solvers import Glucose3
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from CNF import generate_cnf_clauses

def check_connectivity(model, islands, reverse_map):
    """Kiểm tra xem tất cả các đảo có liên thông với nhau không"""
    adj = {isl.id: [] for isl in islands}
    active_vars = [x for x in model if x > 0]
    
    for var_id in active_vars:
        if var_id in reverse_map:
            u, v, _, _ = reverse_map[var_id]
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

def pySAT(matrix):
    """
    Hàm gọi Solver:
    1. Lấy luật từ CNF_udth
    2. Đưa vào Glucose3
    3. Loop kiểm tra liên thông
    """
    # Lấy clauses và map từ file CNF
    clauses, reverse_map, islands, bridges, var_map, num_vars = generate_cnf_clauses(matrix)
    
    # Khởi tạo Solver
    with Glucose3(bootstrap_with=clauses) as solver:
        while solver.solve():
            model = solver.get_model()
            
            # Kiểm tra liên thông (Logic đồ thị)
            if check_connectivity(model, islands, reverse_map):
                return model, reverse_map
            else:
                # Nếu không liên thông, chặn nghiệm này và tìm tiếp
                solver.add_clause([-x for x in model])
                
    return None, None