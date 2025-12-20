def check_connectivity(model, islands, reverse_map):
    """Check if all islands are connected using BFS."""
    adj = {island.id: [] for island in islands}
    active_vars = [x for x in model if x > 0]
    
    # Build adjacency list from active bridge variables
    for var_id in active_vars:
        if var_id in reverse_map:
            u, v, _, _ = reverse_map[var_id]
            # Avoid duplicate edges (double bridges)
            if v.id not in adj[u.id]:
                adj[u.id].append(v.id)
            if u.id not in adj[v.id]:
                adj[v.id].append(u.id)
    
    # BFS to check connectivity
    if not islands:
        return True
    
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


def count_components(islands, active_bridge_vars, reverse_map):
    """Count connected components using BFS."""
    if not islands:
        return 1, True
    
    # Build adjacency list
    adj = {island.id: [] for island in islands}
    for var_id in active_bridge_vars:
        if var_id in reverse_map:
            u, v, _, _ = reverse_map[var_id]
            if v.id not in adj[u.id]:
                adj[u.id].append(v.id)
            if u.id not in adj[v.id]:
                adj[v.id].append(u.id)
    
    # BFS to count connected components
    visited = set()
    num_components = 0
    
    for island in islands:
        if island.id in visited:
            continue
        
        # Start BFS from this unvisited island
        num_components += 1
        queue = [island.id]
        visited.add(island.id)
        
        while queue:
            curr = queue.pop(0)  # BFS: use queue (FIFO)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    
    is_connected = (num_components == 1)
    return num_components, is_connected


def check_connectivity_from_edges(islands, edges):
    """Check if all islands form a connected graph using BFS. Works with tuples (row, col, value) for islands."""
    if not islands:
        return True
    
    n = len(islands)
    adj = [[] for _ in range(n)]
    
    # Build mapping (position -> index)
    pos_to_idx = {}
    for i, (x, y, _) in enumerate(islands):
        pos_to_idx[(x, y)] = i
    
    # Build adjacency list from edges
    for a, b, count in edges:
        if count == 0:
            continue
        if a in pos_to_idx and b in pos_to_idx:
            ia = pos_to_idx[a]
            ib = pos_to_idx[b]
            adj[ia].append(ib)
            adj[ib].append(ia)
    
    # BFS to check connectivity
    visited = [False] * n
    queue = [0]
    visited[0] = True
    
    while queue:
        u = queue.pop(0)  # BFS: use queue (FIFO)
        for v in adj[u]:
            if not visited[v]:
                visited[v] = True
                queue.append(v)
    
    return all(visited)

