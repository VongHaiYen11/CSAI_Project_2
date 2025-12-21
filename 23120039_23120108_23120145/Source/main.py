import argparse
import json
import os
import sys
import time
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

from Algorithms.astar import AStar
from Algorithms.backtracking import Backtracking
from Algorithms.bruteforce import BruteForce
from Algorithms.pysat import PySAT


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FOLDER = os.path.join(BASE_DIR, "Inputs")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "Outputs")
SOLUTIONS_FOLDER = os.path.join(BASE_DIR, "Solutions")
TABLES_CHARTS_FOLDER = os.path.join(BASE_DIR, "Tables_and_Charts")

ALGORITHM_NAMES = ["BruteForce", "Backtracking", "AStar", "PySAT"]
DEFAULT_TIMEOUT = 300  # seconds

# Create necessary directories
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(SOLUTIONS_FOLDER, exist_ok=True)
os.makedirs(TABLES_CHARTS_FOLDER, exist_ok=True)

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


def estimate_memory(matrix, algo_name):
    """Estimate memory usage in MB."""
    n = len(matrix)
    num_islands = sum(1 for r in matrix for x in r if x > 0)
    
    base_mem = (n * n * 8) / (1024 * 1024)
    
    if algo_name == "BruteForce":
        num_edges = num_islands * (num_islands - 1) // 2
        return max(0.01, base_mem + (num_edges * 3 * 8) / (1024 * 1024))
    elif algo_name == "Backtracking":
        return max(0.01, base_mem + (num_islands * 0.01))
    elif algo_name == "AStar":
        return max(0.01, base_mem + (num_islands * num_islands * 0.001))
    elif algo_name == "PySAT":
        num_edges = num_islands * (num_islands - 1) // 2
        num_clauses = num_edges * 10
        return max(0.01, base_mem + (num_clauses * 0.0001))
    
    return base_mem


def run_bruteforce(matrix, timeout):
    """Run the brute force algorithm."""
    try:
        solver = BruteForce(matrix)
        result, duration = solver.solve(timeout=timeout)

        if duration >= timeout:
            return None, None, "TIMEOUT"

        if result is None:
            return None, None, "NO SOLUTION"
        
        return result, duration, "SUCCESS"  # Returns time in seconds
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
        
        return result, duration, "SUCCESS"  # Returns time in seconds
    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_astar(matrix, timeout):
    """Run the A* algorithm."""
    try:
        solver = AStar()
        result, duration = solver.solve(matrix, timeout=timeout)

        if duration >= timeout:
            return None, None, "TIMEOUT"
        
        if result is None:
            return None, None, "NO SOLUTION"
        
        return result, duration, "SUCCESS"  # Returns time in seconds
    except Exception as e:
        return None, None, f"ERROR: {e}"


def run_pysat(matrix, timeout):
    """Run the PySAT algorithm."""
    try:
        solver = PySAT()
        result, duration = solver.solve(matrix, timeout=timeout)

        if duration >= timeout:
            return None, None, "TIMEOUT"
        if result is None:
            return None, None, "NO SOLUTION"

        return result, duration, "SUCCESS"  # Returns time in seconds
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
        mem_usage = None
        
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
            mem_usage = estimate_memory(matrix, name)
            
            if status == "SUCCESS":
                time_str = f"{t:.4f}"
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
                time_str = f"{t:.4f}" if t is not None else "-"
                res_display = "NO SOLUTION"
                note = "Unsolvable"
                check_status = "FAILED"
                write_output(name, out_name, "NO SOLUTION: No valid arrangement found.")

        # Store result for best selection
        results[name] = {
            "result": res, 
            "time": t, 
            "status": status, 
            "check": check_status,
            "memory": mem_usage
        }
        table_rows.append(f"| {name:<15} | {time_str:<15} | {res_display:<15} | {note:<18} |")

    # Clear processing message
    print("\r" + " " * 50 + "\r", end="", flush=True)

    # Print results table to console
    print_separator("=")
    print(f" TESTING: {input_file}")
    if expected_grid:
        print(f" (Has Reference Solution)")
    else:
        print(f" (No Reference Solution Found in {SOLUTIONS_FOLDER})")
    print_separator("=")
    print(f"Size: {n}x{n} | Islands: {num_islands}")
    
    print_separator("-", 85)
    print(f"| {'ALGORITHM':<15} | {'TIME (s)':<15} | {'RESULT':<15} | {'NOTE':<18} |")
    print_separator("-", 85)
    
    for row in table_rows:
        print(row)
        
    print_separator("-", 85)

    best_algo, _, best_time = select_best(results)

    if best_algo:
        print(f"✓ Best valid solver: {best_algo} ({best_time:.4f} s)")
    else:
        print("✗ No correct solution found")
    
    # Save this test result to individual file
    save_individual_test_table(input_file, n, num_islands, expected_grid, 
                                table_rows, results, best_algo, best_time)

    return {
        "input": input_file,
        "size": f"{n}x{n}",
        "islands": num_islands,
        "results": results,
        "best_algo": best_algo,
        "best_time": best_time
    }


# ============================================================
# NEW: VISUALIZATION FUNCTIONS
# ============================================================

def save_individual_test_table(input_file, n, num_islands, expected_grid, 
                                table_rows, results, best_algo, best_time):
    """Save individual test result to a table file."""
    output_lines = []
    
    # Title
    output_lines.append("=" * 85)
    output_lines.append(f" TESTING: {input_file}")
    if expected_grid:
        output_lines.append(" (Has Reference Solution)")
    else:
        output_lines.append(f" (No Reference Solution Found)")
    output_lines.append("=" * 85)
    output_lines.append(f"Size: {n}x{n} | Islands: {num_islands}")
    output_lines.append("")
    
    # Create table data
    table_data = []
    for name in ["BruteForce", "Backtracking", "AStar", "PySAT"]:
        algo_result = results.get(name, {})
        status = algo_result.get("status", "N/A")
        check = algo_result.get("check", "N/A")
        time_s = algo_result.get("time")
        
        if status == "SKIPPED":
            time_str = "-"
            result_str = "SKIPPED"
            note = "Size Limit"
        elif status == "SUCCESS":
            time_str = f"{time_s:.4f}"
            if check == "CORRECT":
                result_str = "CORRECT"
                note = "Match"
            elif check == "WRONG":
                result_str = "WRONG"
                note = "Mismatch"
            else:
                result_str = "SAVED"
                note = "No Solution File"
        elif status == "TIMEOUT":
            time_str = "> LIMIT"
            result_str = "TIMEOUT"
            note = "Time Limit"
        else:
            time_str = f"{time_s:.4f}" if time_s else "-"
            result_str = "ERROR"
            note = "Unsolvable"
        
        table_data.append([name, time_str, result_str, note])
    
    # Format table
    headers = ["ALGORITHM", "TIME (s)", "RESULT", "NOTE"]
    table_str = tabulate(table_data, headers=headers, tablefmt="grid")
    output_lines.append(table_str)
    output_lines.append("")
    
    # Best solver
    if best_algo:
        output_lines.append(f"✓ Best valid solver: {best_algo} ({best_time:.4f} s)")
    else:
        output_lines.append("✗ No correct solution found")
    
    output_lines.append("=" * 85)
    
    # Save to file
    test_name = input_file.replace("input-", "test_").replace(".txt", "")
    output_path = os.path.join(TABLES_CHARTS_FOLDER, f"{test_name}_result.txt")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))


def generate_table_for_algorithm(all_results, algo_name, timeout):
    """Generate comparison table for one algorithm."""
    table_data = []
    
    for result in all_results:
        input_name = result["input"].replace("input-", "").replace(".txt", "")
        algo_result = result["results"].get(algo_name, {})
        
        status = algo_result.get("status", "N/A")
        check = algo_result.get("check", "N/A")
        time_s = algo_result.get("time")  # Already in seconds
        memory_mb = algo_result.get("memory")
        
        # Format status
        if status == "SUCCESS" and check == "CORRECT":
            status_str = "CORRECT"
        elif status == "TIMEOUT":
            status_str = "TIMEOUT"
        elif status == "SKIPPED":
            status_str = "SKIPPED"
        else:
            status_str = "ERROR"
        
        # Format time (already in seconds)
        if status == "SUCCESS" and time_s is not None:
            time_str = f"{time_s:.4f}"
        elif status == "TIMEOUT":
            time_str = f"> {timeout:.2f}"
        else:
            time_str = "-"
        
        # Format memory
        mem_str = f"{memory_mb:.2f}" if memory_mb else "-"
        
        table_data.append([
            f"input-{input_name}",
            status_str,
            time_str,
            mem_str
        ])
    
    return table_data


def save_table(all_results, algo_name, timeout):
    """Save table to file."""
    table_data = generate_table_for_algorithm(all_results, algo_name, timeout)
    headers = ["Input", "Status", "Time (s)", "Memory (MB)"]
    
    table_str = tabulate(table_data, headers=headers, tablefmt="grid")
    
    # Add title
    title = f"Table 2: Test Results for {algo_name}\n\n"
    
    # Save to file
    output_path = os.path.join(TABLES_CHARTS_FOLDER, f"table_{algo_name}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(title)
        f.write(table_str)
    
    print(f"  ✓ Table saved: table_{algo_name}.txt")


def create_chart_for_algorithm(all_results, algo_name, timeout):
    """Create chart for one algorithm with log scale."""
    input_nums = []
    times_s = []
    timeout_indices = []
    
    for result in all_results:
        input_name = result["input"].replace("input-", "").replace(".txt", "")
        input_num = int(input_name)
        
        algo_result = result["results"].get(algo_name, {})
        status = algo_result.get("status")
        time_s = algo_result.get("time")  # Already in seconds
        
        input_nums.append(input_num)
        
        if status == "SUCCESS" and time_s is not None:
            times_s.append(time_s)  # Already in seconds
        elif status == "TIMEOUT":
            times_s.append(timeout)
            timeout_indices.append(len(input_nums) - 1)
        elif status == "SKIPPED":
            times_s.append(None)
        else:
            times_s.append(None)
    
    # Filter None values
    valid_data = [(x, y) for x, y in zip(input_nums, times_s) if y is not None]
    if not valid_data:
        print(f"  ⚠ No valid data for {algo_name}")
        return
    
    x_vals, y_vals = zip(*valid_data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot line
    ax.plot(x_vals, y_vals, marker='o', linewidth=2, 
           markersize=8, color='#2E7D32', label=algo_name)
    
    # Highlight timeout points
    if timeout_indices:
        timeout_x = [input_nums[i] for i in timeout_indices if times_s[i] is not None]
        timeout_y = [timeout for _ in timeout_x]
        
        if timeout_x:
            ax.scatter(timeout_x, timeout_y, color='red', s=200, 
                      marker='x', linewidths=3, zorder=5)
            
            # Add text annotation
            mid_x = (min(timeout_x) + max(timeout_x)) / 2 if len(timeout_x) > 1 else timeout_x[0]
            ax.text(mid_x, timeout * 2, f'Timeout Threshold ({timeout:.0f}s)', 
                   color='red', fontsize=11, fontweight='bold',
                   ha='center', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Styling
    ax.set_xlabel('Input (01 → 10)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
    ax.set_title(f'Figure 1: Execution Time of {algo_name} Algorithm by Input', 
                fontsize=12, fontweight='bold', pad=15)
    
    # Log scale
    ax.set_yscale('log')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', which='both')
    
    # Legend
    ax.legend(loc='upper left', fontsize=10)
    
    # X-axis ticks
    ax.set_xticks(input_nums)
    ax.set_xticklabels([f"{x}" for x in input_nums])
    
    plt.tight_layout()
    
    # Save
    output_path = os.path.join(TABLES_CHARTS_FOLDER, f"chart_{algo_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Chart saved: chart_{algo_name}.png")


def create_comparison_chart(all_results, timeout):
    """Create comparison chart for all algorithms."""
    algorithms = ["BruteForce", "Backtracking", "AStar", "PySAT"]
    colors = ['#D32F2F', '#1976D2', '#388E3C', '#F57C00']
    markers = ['s', 'o', '^', 'D']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    for idx, algo in enumerate(algorithms):
        input_nums = []
        times_s = []
        
        for result in all_results:
            input_name = result["input"].replace("input-", "").replace(".txt", "")
            input_num = int(input_name)
            
            algo_result = result["results"].get(algo, {})
            status = algo_result.get("status")
            time_s = algo_result.get("time")  # Already in seconds
            
            if status == "SUCCESS" and time_s is not None:
                input_nums.append(input_num)
                times_s.append(time_s)  # Already in seconds
            elif status == "TIMEOUT":
                input_nums.append(input_num)
                times_s.append(timeout)
        
        if input_nums:
            ax.plot(input_nums, times_s, marker=markers[idx], linewidth=2,
                   markersize=7, label=algo, color=colors[idx])
    
    ax.set_xlabel('Input Test Cases', fontsize=12, fontweight='bold')
    ax.set_ylabel('Execution Time (seconds, log scale)', fontsize=12, fontweight='bold')
    ax.set_title('Algorithm Performance Comparison', fontsize=14, fontweight='bold', pad=20)
    
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3, linestyle='--', which='both')
    ax.legend(loc='best', fontsize=10)
    
    plt.tight_layout()
    
    output_path = os.path.join(TABLES_CHARTS_FOLDER, "comparison_all_algorithms.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Comparison chart saved: comparison_all_algorithms.png")


def generate_all_visualizations(all_results, timeout):
    """Generate all tables and charts."""
    print("\n" + "="*60)
    print("GENERATING TABLES AND CHARTS")
    print("="*60)
    
    algorithms = ["BruteForce", "Backtracking", "AStar", "PySAT"]
    
    # Generate tables
    print("\n[1/4] Generating algorithm tables...")
    for algo in algorithms:
        save_table(all_results, algo, timeout)
    
    # Generate individual charts
    print("\n[2/4] Generating individual charts...")
    for algo in algorithms:
        create_chart_for_algorithm(all_results, algo, timeout)
    
    # Generate comparison chart
    print("\n[3/4] Generating comparison chart...")
    create_comparison_chart(all_results, timeout)
    
    # Generate final summary table
    print("\n[4/4] Generating final summary table...")
    save_final_summary_table(all_results)
    
    print("\n✓ All visualizations generated successfully!")
    print(f"  Location: {TABLES_CHARTS_FOLDER}")


def save_final_summary_table(all_results):
    """Save final summary table to file."""
    output_lines = []
    
    output_lines.append("=" * 90)
    output_lines.append(f"{'FINAL SUMMARY REPORT':^90}")
    output_lines.append("=" * 90)
    output_lines.append("")
    
    # Create table data
    table_data = []
    for item in all_results:
        fname = item["input"]
        size = item["size"]
        num_isl = item["islands"]
        best = item["best_algo"] if item["best_algo"] else "NONE"
        
        t_val = item.get("best_time")
        t_str = f"{t_val:.4f}" if t_val is not None and best != "NONE" else "-"
        
        table_data.append([fname, size, num_isl, best, t_str])
    
    headers = ["INPUT FILE", "SIZE", "ISLANDS", "BEST ALGO", "TIME (s)"]
    table_str = tabulate(table_data, headers=headers, tablefmt="grid")
    
    output_lines.append(table_str)
    output_lines.append("")
    output_lines.append("=" * 90)
    
    # Statistics
    output_lines.append("\nSTATISTICS:")
    output_lines.append("-" * 90)
    
    total_tests = len(all_results)
    
    for algo in ["BruteForce", "Backtracking", "AStar", "PySAT"]:
        success = sum(1 for r in all_results 
                     if r["results"].get(algo, {}).get("status") == "SUCCESS")
        timeout = sum(1 for r in all_results 
                     if r["results"].get(algo, {}).get("status") == "TIMEOUT")
        skipped = sum(1 for r in all_results 
                     if r["results"].get(algo, {}).get("status") == "SKIPPED")
        
        output_lines.append(f"\n{algo}:")
        output_lines.append(f"  ✓ Success: {success}/{total_tests}")
        if timeout > 0:
            output_lines.append(f"  ⏱ Timeout: {timeout}/{total_tests}")
        if skipped > 0:
            output_lines.append(f"  ⊘ Skipped: {skipped}/{total_tests}")
    
    output_lines.append("\n" + "=" * 90)
    
    # Save to file
    output_path = os.path.join(TABLES_CHARTS_FOLDER, "final_summary.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    
    print(f"  ✓ Final summary saved: final_summary.txt")


def main():
    """Main entry point for the comparison script."""
    parser = argparse.ArgumentParser(
        description="Compare Hashiwokakero solving algorithms"
    )
    parser.add_argument("--test", type=str, help="Run specific input file")
    parser.add_argument("--all", action="store_true", help="Run all inputs")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                       help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("--visualize", action="store_true", 
                       help="Generate tables and charts after running")
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
    
    print(f"| {'INPUT FILE':<15} | {'SIZE':<8} | {'ISLANDS':<8} | {'BEST ALGO':<15} | {'TIME (s)':<15} |")
    print_separator("-", 90)

    for item in summary_data:
        fname = item["input"]
        size = item["size"]
        num_isl = item["islands"]
        best = item["best_algo"] if item["best_algo"] else "NONE"
        
        t_val = item.get("best_time")
        t_str = f"{t_val:.4f}" if t_val is not None else "-"

        if best == "NONE":
            t_str = "-"

        print(f"| {fname:<15} | {size:<8} | {num_isl:<8} | {best:<15} | {t_str:<15} |")

    print_separator("-", 90)
    print(f"Outputs saved in: {OUTPUT_FOLDER}")
    print(f"Expected Solutions read from: {SOLUTIONS_FOLDER}")
    
    # Generate visualizations if requested or if running all tests
    if args.visualize or (args.all and not args.test):
        generate_all_visualizations(summary_data, timeout)


if __name__ == "__main__":
    main()