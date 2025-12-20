import argparse
import json
import os
import sys
import time

from Algorithms.astar import AStar
from Algorithms.backtracking import Backtracking
from Algorithms.bruteforce import BruteForce
from Algorithms.pysat import PySAT


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "Inputs")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Outputs")
SOLUTIONS_FOLDER = os.path.join(BASE_DIR, "Solutions")

ALGORITHM_NAMES = ["BruteForce", "Backtracking", "AStar", "PySAT"]
DEFAULT_TIMEOUT = 60  # seconds

# Create necessary directories
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SOLUTIONS_FOLDER, exist_ok=True)

for algo_name in ALGORITHM_NAMES:
    os.makedirs(os.path.join(OUTPUT_FOLDER, algo_name), exist_ok=True)


def read_input(path):
    """Read puzzle input from a file."""
    matrix = []
    with open(path, "r") as f:
        for line in f:
            matrix.append([int(x.strip()) for x in line.split(",")])
    return matrix


def read_solution(path):
    """Read expected solution from a file. Assumes solution file has format matching output."""
    if not os.path.exists(path):
        return None
    
    grid = []
    try:
        with open(path, "r") as f:
            for line in f:
                # Remove brackets and parse into list
                clean_line = line.strip().replace("[", "").replace("]", "")
                row = [x.strip().replace('"', '').replace("'", "") for x in clean_line.split(",")]
                grid.append(row)
        return grid
    except Exception:
        return None


def write_output(folder_name, file_name, content):
    """Write algorithm output to a file."""
    folder_path = os.path.join(OUTPUT_FOLDER, folder_name)
    file_path = os.path.join(folder_path, file_name)
    
    with open(file_path, "w") as f:
        if isinstance(content, str):
            f.write(content)
        else:
            for row in content:
                f.write("[ " + " , ".join(f'"{x}"' for x in row) + " ]\n")


def print_separator(char="-", length=85):
    """Print a separator line for formatting output."""
    print(char * length)


def run_bruteforce(matrix, timeout):
    """Run the brute force algorithm."""
    try:
        solver = BruteForce(matrix)
        result, duration = solver.solve(timeout=timeout)

        if duration >= timeout:
            return None, None, "TIMEOUT"

        if result is None:
            return None, None, "NO SOLUTION"
        
        return result, duration * 1000, "SUCCESS"
    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_backtracking(matrix, timeout):
    """Run the backtracking algorithm."""
    try:
        solver = Backtracking(matrix)
        result, duration = solver.solve(timeout=timeout)

        if duration >= timeout:
            return None, None, "TIMEOUT"
        
        if result is None:
            return None, None, "NO SOLUTION"
        
        return result, duration * 1000, "SUCCESS"
    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_astar(matrix, timeout):
    """Run the A* algorithm."""
    try:
        solver = AStar()
        result, duration = solver.solve(matrix)

        if duration >= timeout:
            return None, None, "TIMEOUT"
        
        if result is None:
            return None, None, "NO SOLUTION"
        
        return result, duration * 1000, "SUCCESS"
    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_pysat(matrix, timeout):
    """Run the PySAT algorithm."""
    try:
        solver = PySAT()
        result, duration = solver.solve(matrix)

        if duration > timeout:
            return None, None, "TIMEOUT"
        if result is None:
            return None, None, "NO SOLUTION"

        return result, duration * 1000, "SUCCESS"
    except Exception as e:
        return None, None, f"ERROR: {e}"


def select_best(results):
    """Select the best algorithm result based on correctness and speed. Priority order: PySAT > AStar > Backtracking > BruteForce."""
    priority = ["PySAT", "AStar", "Backtracking", "BruteForce"]
    
    # First preference: successful algorithms with correct results
    valid = {
        k: v for k, v in results.items()
        if v["status"] == "SUCCESS" and v.get("check") == "CORRECT"
    }
    
    # Fallback: any successful algorithm
    if not valid:
        valid = {k: v for k, v in results.items() if v["status"] == "SUCCESS"}

    if not valid:
        return None, None, None

    # Find fastest
    fastest = min(valid, key=lambda k: valid[k]["time"])
    fastest_time = valid[fastest]["time"]

    # Return highest priority algorithm within 10% of fastest time
    for algo in priority:
        if algo in valid and valid[algo]["time"] <= 1.1 * fastest_time:
            return algo, valid[algo]["result"], valid[algo]["time"]

    return fastest, valid[fastest]["result"], valid[fastest]["time"]


def compare_algorithms(input_file, timeout):
    """Compare all algorithms on a single input file."""
    print(f"\nProcessing {input_file}...", end="", flush=True)

    matrix = read_input(os.path.join(INPUT_FOLDER, input_file))
    n = len(matrix)
    num_islands = sum(1 for row in matrix for x in row if x > 0)

    # Read expected solution (convention: input-01.txt -> solution-01.txt)
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
        check_status = "N/A"
        
        # Case 1: Algorithm skipped due to size limit
        if runner is None:
            res, t, status = None, None, "SKIPPED"
            time_str = "-"
            res_display = "NO SOLUTION"
            note = "Size Limit"
            write_output(name, out_name, "NO SOLUTION: Grid size too large (Size Limit).")

        # Case 2: Run algorithm
        else:
            res, t, status = runner(matrix, timeout=timeout)
            
            if status == "SUCCESS":
                time_str = f"{t:.2f}"
                write_output(name, out_name, res)
                
                # Verify result against expected solution
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
                write_output(name, out_name, f"NO SOLUTION: Timeout (> {timeout}s).")
                
            else:  # NO SOLUTION or ERROR
                time_str = f"{t:.2f}" if t is not None else "-"
                res_display = "NO SOLUTION"
                note = "Unsolvable"
                check_status = "FAILED"
                write_output(name, out_name, "NO SOLUTION: No valid arrangement found.")

        # Store result for best selection
        results[name] = {"result": res, "time": t, "status": status, "check": check_status}
        table_rows.append(f"| {name:<15} | {time_str:<15} | {res_display:<15} | {note:<18} |")

    # Clear processing message
    print("\r" + " " * 50 + "\r", end="", flush=True)

    # Print results table
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


def main():
    """Main entry point for the comparison script."""
    parser = argparse.ArgumentParser(
        description="Compare Hashiwokakero solving algorithms"
    )
    parser.add_argument("--test", type=str, help="Run specific input file")
    parser.add_argument("--all", action="store_true", help="Run all inputs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                       help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    timeout = args.timeout
    summary_data = []

    if args.test:
        data = compare_algorithms(args.test, timeout)
        summary_data.append(data)
    else:
        # Get list of input files
        if os.path.exists(INPUT_FOLDER):
            input_files = sorted([
                f for f in os.listdir(INPUT_FOLDER) if f.startswith("input-")
            ])
            if not input_files:
                print(f"No input files found in {INPUT_FOLDER}")
            for filename in input_files:
                data = compare_algorithms(filename, timeout)
                summary_data.append(data)
        else:
            print(f"Input folder not found: {INPUT_FOLDER}")

    # Print final summary table
    print("\n\n")
    print_separator("=", 90)
    print(f"{'FINAL SUMMARY REPORT':^90}")
    print_separator("=", 90)
    
    print(f"| {'INPUT FILE':<15} | {'SIZE':<8} | {'ISLANDS':<8} | {'BEST ALGO':<15} | {'TIME (ms)':<15} |")
    print_separator("-", 90)

    for item in summary_data:
        fname = item["input"]
        size = item["size"]
        num_isl = item["islands"]
        best = item["best_algo"] if item["best_algo"] else "NONE"
        
        t_val = item.get("best_time")
        t_str = f"{t_val:.2f}" if t_val is not None else "-"

        if best == "NONE":
            t_str = "-"

        print(f"| {fname:<15} | {size:<8} | {num_isl:<8} | {best:<15} | {t_str:<15} |")

    print_separator("-", 90)
    print(f"Outputs saved in: {OUTPUT_FOLDER}")
    print(f"Expected Solutions read from: {SOLUTIONS_FOLDER}")


if __name__ == "__main__":
    main()