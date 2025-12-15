"""
HASHIWOKAKERO SOLVER - MAIN COMPARISON
====================================
Run & compare multiple solvers
"""

import os
import time
import json
from datetime import datetime

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
RESULTS_FILE = os.path.join(BASE_DIR, "comparison_results.json")

TIMEOUT = 200  # seconds

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# ============================================================
# IO HELPERS
# ============================================================

def read_input(path):
    matrix = []
    with open(path, "r") as f:
        for line in f:
            matrix.append([int(x.strip()) for x in line.split(",")])
    return matrix


def write_output(path, grid):
    with open(path, "w") as f:
        for row in grid:
            f.write("[ " + " , ".join(f'"{x}"' for x in row) + " ]\n")


# ============================================================
# RUNNERS
# ============================================================

def run_bruteforce(matrix, timeout):
    try:
        solver = BruteForce(matrix)
        result, duration = solver.solve(timeout=timeout)

        if result is None:
            return None, None, "NO SOLUTION"

        return result, duration * 1000, "SUCCESS"

    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_backtracking(matrix, timeout):
    try:
        solver = Backtracking(matrix)
        result, duration = solver.solve(timeout=timeout)

        if result is None:
            return None, None, "NO SOLUTION"

        return result, duration * 1000, "SUCCESS"

    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_astar(matrix, timeout):
    try:
        solver = AStar()
        result, duration = solver.solve(matrix)

        if result is None:
            return None, None, "NO SOLUTION"

        return result, duration * 1000, "SUCCESS"

    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_pysat(matrix, timeout):
    try:
        start = time.perf_counter()
        model, reverse_map = solve_hashi(matrix)
        elapsed = time.perf_counter() - start

        if elapsed > timeout:
            return None, None, "TIMEOUT"

        if not model:
            return None, None, "NO SOLUTION"

        n = len(matrix)
        grid = [["0"] * n for _ in range(n)]

        # Điền đảo
        islands = parse_board(matrix)
        for isl in islands:
            grid[isl.r][isl.c] = str(isl.val)

        # ===== CHỈ LẤY BIẾN ĐƯỢC CHỌN =====
        active_vars = set(v for v in model if v > 0)

        # Gom bridge theo cạnh
        bridge_map = {}
        for var, (u, v, cnt, d) in reverse_map.items():
            if var not in active_vars:
                continue

            key = (u, v)
            if key not in bridge_map:
                bridge_map[key] = {"has1": False, "has2": False, "dir": d}

            if cnt == 1:
                bridge_map[key]["has1"] = True
            elif cnt == 2:
                bridge_map[key]["has2"] = True

        # Vẽ cầu
        for (u, v), info in bridge_map.items():
            if info["has2"]:
                count = 2
            elif info["has1"]:
                count = 1
            else:
                continue

            d = info["dir"]
            char = "=" if d == "H" and count == 2 else \
                   "-" if d == "H" else \
                   "$" if count == 2 else "|"

            if d == "H":
                for c in range(u.c + 1, v.c):
                    grid[u.r][c] = char
            else:
                for r in range(u.r + 1, v.r):
                    grid[r][u.c] = char

        return grid, elapsed * 1000, "SUCCESS"

    except Exception as e:
        return None, None, f"ERROR: {e}"

# ============================================================
# SELECT BEST
# ============================================================

def select_best(results):
    priority = ["PySAT", "AStar", "Backtracking", "BruteForce"]

    valid = {
        k: v for k, v in results.items()
        if v["status"] == "SUCCESS"
    }

    if not valid:
        return None, None

    fastest = min(valid, key=lambda k: valid[k]["time"])
    t_fast = valid[fastest]["time"]

    for algo in priority:
        if algo in valid and valid[algo]["time"] <= 1.1 * t_fast:
            return algo, valid[algo]["result"]

    return fastest, valid[fastest]["result"]


# ============================================================
# MAIN LOGIC
# ============================================================

def compare_algorithms(input_file):
    print("=" * 60)
    print("Testing:", input_file)
    print("=" * 60)

    matrix = read_input(os.path.join(INPUT_FOLDER, input_file))
    n = len(matrix)
    islands = sum(1 for r in matrix for x in r if x > 0)

    print(f"Size: {n}x{n} | Islands: {islands}")

    results = {}

    runners = {
        "BruteForce": run_bruteforce if n <= 9 else None,
        "Backtracking": run_backtracking,
        "AStar": run_astar,
        "PySAT": run_pysat
    }

    for name, runner in runners.items():
        print(f"\n[{name}]")
        if runner is None:
            results[name] = {"status": "SKIPPED"}
            print("  SKIPPED")
            continue

        res, t, status = runner(matrix, timeout=TIMEOUT)
        results[name] = {"result": res, "time": t, "status": status}

        print(f"  Status: {status}")
        if t:
            print(f"  Time: {t:.2f} ms")

    best_algo, best_grid = select_best(results)

    if best_grid:
        out_name = input_file.replace("input-", "output-")
        write_output(os.path.join(OUTPUT_FOLDER, out_name), best_grid)
        print(f"\n✓ Best solution: {best_algo}")
    else:
        print("\n✗ No valid solution found")

    return {
        "input": input_file,
        "size": f"{n}x{n}",
        "islands": islands,
        "results": results,
        "best": best_algo
    }


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=str)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--timeout", type=int, default=TIMEOUT)
    args = parser.parse_args()

    TIMEOUT = args.timeout

    if args.test:
        compare_algorithms(args.test)
    else:
        all_results = []
        for f in sorted(os.listdir(INPUT_FOLDER)):
            if f.startswith("input-"):
                all_results.append(compare_algorithms(f))

        with open(RESULTS_FILE, "w") as fp:
            json.dump(all_results, fp, indent=2)

# sat_env\Scripts\activate