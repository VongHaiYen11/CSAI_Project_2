"""
HASHIWOKAKERO SOLVER - MAIN COMPARISON & VERIFICATION
=====================================================
Run & compare multiple solvers against Ground Truth Solutions
"""

import os
import time
import json
import argparse
import sys

# Import các thuật toán (Giữ nguyên của bạn)
from Algorithms.BruteForce import BruteForce
from Algorithms.Backtracking import Backtracking
from Algorithms.Astar import AStar
from CNF_udth import solve_hashi, parse_board


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "Inputs")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Output")
# Folder chứa đáp án đúng (Ground Truth)
SOLUTIONS_FOLDER = os.path.join(BASE_DIR, "Solutions") 

# RESULTS_FILE = os.path.join(BASE_DIR, "comparison_results.json")

ALGO_NAMES = ["BruteForce", "Backtracking", "AStar", "PySAT"]

TIMEOUT = 60  # seconds

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# Tạo folder Solutions nếu chưa có (để bạn bỏ file đáp án vào)
os.makedirs(SOLUTIONS_FOLDER, exist_ok=True) 

for algo in ALGO_NAMES:
    os.makedirs(os.path.join(OUTPUT_FOLDER, algo), exist_ok=True)


# ============================================================
# IO HELPERS & FORMATTING
# ============================================================

def read_input(path):
    matrix = []
    with open(path, "r") as f:
        for line in f:
            matrix.append([int(x.strip()) for x in line.split(",")])
    return matrix

def read_solution(path):
    """
    Đọc file đáp án mẫu từ folder Solutions.
    Giả định file đáp án có format giống file output: [ "1", "-", "2" ]
    """
    if not os.path.exists(path):
        return None
    
    grid = []
    try:
        with open(path, "r") as f:
            for line in f:
                # Loại bỏ ngoặc vuông và parse thành list
                # Ví dụ line: [ "1" , "-" , "2" ]
                clean_line = line.strip().replace("[", "").replace("]", "")
                row = [x.strip().replace('"', '').replace("'", "") for x in clean_line.split(",")]
                grid.append(row)
        return grid
    except Exception:
        return None

def write_output(folder_name, file_name, content):
    folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
    file_path = os.path.join(folder_path, file_name)
    
    with open(file_path, "w") as f:
        if isinstance(content, str):
            f.write(content)
        else:
            for row in content:
                f.write("[ " + " , ".join(f'"{x}"' for x in row) + " ]\n")

def print_separator(char="-", length=85):
    print(char * length)


# ============================================================
# RUNNERS (GIỮ NGUYÊN)
# ============================================================

def run_bruteforce(matrix, timeout):
    try:
        solver = BruteForce(matrix)
        result, duration = solver.solve(timeout=timeout)

        if duration >= timeout:
             return None, None, "TIMEOUT"

        if result is None: return None, None, "NO SOLUTION"
        return result, duration * 1000, "SUCCESS"
    except Exception as e: return None, None, f"ERROR: {e}"

def run_backtracking(matrix, timeout):
    try:
        solver = Backtracking(matrix)
        result, duration = solver.solve(timeout=timeout)

        if duration >= timeout:
             return None, None, "TIMEOUT"
        
        if result is None: return None, None, "NO SOLUTION"
        return result, duration * 1000, "SUCCESS"
    except Exception as e: return None, None, f"ERROR: {e}"

def run_astar(matrix, timeout):
    try:
        solver = AStar()
        result, duration = solver.solve(matrix)

        if duration >= timeout:
             return None, None, "TIMEOUT"
        
        if result is None: return None, None, "NO SOLUTION"
        return result, duration * 1000, "SUCCESS"
    except Exception as e: return None, None, f"ERROR: {e}"

def run_pysat(matrix, timeout):
    try:
        model, reverse_map, duration = solve_hashi(matrix)

        if duration > timeout: return None, None, "TIMEOUT"
        if not model: return None, None, "NO SOLUTION"

        n = len(matrix)
        grid = [["0"] * n for _ in range(n)]
        islands = parse_board(matrix)
        for isl in islands: grid[isl.r][isl.c] = str(isl.val)

        active_vars = set(v for v in model if v > 0)
        bridge_map = {}
        for var, (u, v, cnt, d) in reverse_map.items():
            if var not in active_vars: continue
            key = (u, v)
            if key not in bridge_map: bridge_map[key] = {"has1": False, "has2": False, "dir": d}
            if cnt == 1: bridge_map[key]["has1"] = True
            elif cnt == 2: bridge_map[key]["has2"] = True

        for (u, v), info in bridge_map.items():
            count = 2 if info["has2"] else 1 if info["has1"] else 0
            if count == 0: continue
            
            d = info["dir"]
            char = "=" if d == "H" and count == 2 else \
                   "-" if d == "H" else \
                   "$" if count == 2 else "|"

            if d == "H":
                for c in range(u.c + 1, v.c): grid[u.r][c] = char
            else:
                for r in range(u.r + 1, v.r): grid[r][u.c] = char

        return grid, duration * 1000, "SUCCESS"
    except Exception as e: return None, None, f"ERROR: {e}"


# ============================================================
# SELECT BEST
# ============================================================

def select_best(results):
    priority = ["PySAT", "AStar", "Backtracking", "BruteForce"]
    # Chỉ chọn những thuật toán chạy thành công VÀ kết quả đúng (CORRECT)
    valid = {k: v for k, v in results.items() if v["status"] == "SUCCESS" and v.get("check") == "CORRECT"}
    
    # Nếu không có cái nào đúng, thử tìm cái SUCCESS (dù check WRONG hoặc ko có check)
    if not valid:
        valid = {k: v for k, v in results.items() if v["status"] == "SUCCESS"}

    if not valid: return None, None, None

    fastest = min(valid, key=lambda k: valid[k]["time"])
    t_fast = valid[fastest]["time"]

    for algo in priority:
        if algo in valid and valid[algo]["time"] <= 1.1 * t_fast:
            return algo, valid[algo]["result"], valid[algo]["time"]

    return fastest, valid[fastest]["result"], valid[fastest]["time"]


# ============================================================
# MAIN LOGIC
# ============================================================

def compare_algorithms(input_file):
    print(f"\nProcessing {input_file}...", end="", flush=True)

    matrix = read_input(os.path.join(INPUT_FOLDER, input_file))
    n = len(matrix)
    num_islands = sum(1 for r in matrix for x in r if x > 0)

    # --- ĐỌC FILE ĐÁP ÁN (SOLUTION) ---
    # Quy ước tên file: input-01.txt -> solution-01.txt
    sol_file = input_file.replace("input-", "solution-")
    expected_grid = read_solution(os.path.join(SOLUTIONS_FOLDER, sol_file))
    
    results = {}
    runners = {
        "BruteForce": run_bruteforce if n <= 9 else None,
        "Backtracking": run_backtracking,
        "AStar": run_astar,
        "PySAT": run_pysat
    }

    table_rows = []

    for name, runner in runners.items():
        out_name = input_file.replace("input-", "output-")
        check_status = "N/A" # Trạng thái kiểm tra đáp án
        
        # --- TRƯỜNG HỢP 1: SIZE LIMIT (SKIPPED) ---
        if runner is None:
            res, t, status = None, None, "SKIPPED"
            time_str = "-"
            res_display = "NO SOLUTION" 
            note = "Size Limit"
            write_output(name, out_name, "NO SOLUTION: Grid size too large (Size Limit).")

        # --- TRƯỜNG HỢP 2: CHẠY THUẬT TOÁN ---
        else:
            res, t, status = runner(matrix, timeout=TIMEOUT)
            
            if status == "SUCCESS":
                time_str = f"{t:.2f}"
                write_output(name, out_name, res)
                
                # --- LOGIC KIỂM TRA ĐÁP ÁN (MỚI) ---
                if expected_grid is None:
                    res_display = "SAVED"
                    note = "No Solution File"
                    check_status = "UNKNOWN"
                else:
                    if res == expected_grid:
                        res_display = "CORRECT"
                        note = "Match"
                        check_status = "CORRECT"
                    else:
                        res_display = "WRONG"
                        note = "Mismatch"
                        check_status = "WRONG"
                
            elif status == "TIMEOUT":
                time_str = "> LIMIT"
                res_display = "NO SOLUTION"
                note = "Time Limit"
                check_status = "TIMEOUT"
                write_output(name, out_name, f"NO SOLUTION: Timeout (> {TIMEOUT}s).")
                
            else: # NO SOLUTION hoặc ERROR
                time_str = f"{t:.2f}" if t is not None else "-"
                res_display = "NO SOLUTION"
                note = "Unsolvable"
                check_status = "FAILED"
                write_output(name, out_name, "NO SOLUTION: No valid arrangement found.")

        # Lưu thêm check_status vào results để dùng cho select_best
        results[name] = {"result": res, "time": t, "status": status, "check": check_status}
        table_rows.append(f"| {name:<15} | {time_str:<15} | {res_display:<15} | {note:<18} |")

    # Xóa dòng "Processing..."
    print("\r" + " " * 50 + "\r", end="", flush=True)

    # ==========================
    # IN BẢNG KẾT QUẢ CỦA TEST
    # ==========================
    print_separator("=")
    print(f" TESTING: {input_file}")
    if expected_grid:
        print(f" (Has Reference Solution)")
    else:
        print(f" (No Reference Solution Found in {SOLUTIONS_FOLDER})")
    print_separator("=")
    print(f"Size: {n}x{n} | Islands: {num_islands}")
    
    print_separator("-", 85)
    print(f"| {'ALGORITHM':<15} | {'TIME (ms)':<15} | {'RESULT':<15} | {'NOTE':<18} |")
    print_separator("-", 85)
    
    for row in table_rows:
        print(row)
        
    print_separator("-", 85)

    best_algo, _, best_time = select_best(results)

    if best_algo:
        print(f"✓ Best valid solver: {best_algo} ({best_time:.2f} ms)")
    else:
        print("✗ No correct solution found")

    return {
        "input": input_file,
        "size": f"{n}x{n}",
        "islands": num_islands,
        "results": results,
        "best_algo": best_algo,
        "best_time": best_time
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str, help="Run specific input file")
    parser.add_argument("--all", action="store_true", help="Run all inputs")
    parser.add_argument("--timeout", type=int, default=TIMEOUT)
    args = parser.parse_args()

    TIMEOUT = args.timeout
    summary_data = []

    if args.test:
        data = compare_algorithms(args.test)
        summary_data.append(data)
    else:
        # Lấy danh sách input
        if os.path.exists(INPUT_FOLDER):
            input_files = sorted([f for f in os.listdir(INPUT_FOLDER) if f.startswith("input-")])
            if not input_files:
                print(f"No input files found in {INPUT_FOLDER}")
            for f in input_files:
                data = compare_algorithms(f)
                summary_data.append(data)
        else:
            print(f"Input folder not found: {INPUT_FOLDER}")

    # with open(RESULTS_FILE, "w") as fp:
    #     json.dump(summary_data, fp, indent=2, default=str)

    # ============================================================
    # FINAL SUMMARY TABLE
    # ============================================================
    print("\n\n")
    print_separator("=", 90)
    print(f"{'FINAL SUMMARY REPORT':^90}")
    print_separator("=", 90)
    
    print(f"| {'INPUT FILE':<15} | {'SIZE':<8} | {'ISLANDS':<8} | {'BEST ALGO':<15} | {'TIME (ms)':<15} |")
    print_separator("-", 90)

    for item in summary_data:
        fname = item["input"]
        size = item["size"]
        isl = item["islands"]
        best = item["best_algo"] if item["best_algo"] else "NONE"
        
        t_val = item.get("best_time")
        t_str = f"{t_val:.2f}" if t_val is not None else "-"

        # Nếu best algo là NONE do tất cả đều sai kết quả
        if best == "NONE":
            t_str = "-"

        print(f"| {fname:<15} | {size:<8} | {isl:<8} | {best:<15} | {t_str:<15} |")

    print_separator("-", 90)
    # print(f"Report saved to: {RESULTS_FILE}")
    print(f"Outputs saved in: {OUTPUT_FOLDER}")
    print(f"Expected Solutions read from: {SOLUTIONS_FOLDER}")