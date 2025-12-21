def is_intersect(a1, b1, a2, b2):
    """Check if two bridges intersect. Works with Island objects or (row, col) tuples."""
    # Helper to get row/col from either Island object or tuple
    def get_row(point):
        return point.r if hasattr(point, 'r') else point[0]
    
    def get_col(point):
        return point.c if hasattr(point, 'c') else point[1]
    
    # Same endpoint -> no intersection
    if a1 == a2 or a1 == b2 or b1 == a2 or b1 == b2:
        return False
    
    # Check if bridges are horizontal
    h1 = (get_row(a1) == get_row(b1))
    h2 = (get_row(a2) == get_row(b2))
    
    # Same direction -> cannot intersect
    if h1 == h2:
        return False
    
    # Ensure bridge 1 is horizontal
    if not h1:
        return is_intersect(a2, b2, a1, b1)
    
    # Bridge 1 horizontal, Bridge 2 vertical
    row = get_row(a1)
    col = get_col(a2)
    
    y1, y2 = sorted([get_col(a1), get_col(b1)])
    x1, x2 = sorted([get_row(a2), get_row(b2)])
    
    # Intersect if bridge 2's column is between bridge 1's endpoints
    # AND bridge 1's row is between bridge 2's endpoints
    return (y1 < col < y2) and (x1 < row < x2)

