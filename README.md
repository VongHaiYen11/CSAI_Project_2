# Hashiwokakero Puzzle Solver

A comprehensive implementation and comparison of multiple algorithms for solving Hashiwokakero (Bridges) puzzles. This project evaluates four different solving approaches: Brute Force, Backtracking, A* Search, and PySAT (SAT-based solving).

## Overview

Hashiwokakero is a logic puzzle where the goal is to connect islands (numbered cells) with bridges. The number on each island indicates how many bridges must connect to it. Bridges can be drawn horizontally or vertically, and must not cross each other.

## Project Structure

```
23120039_23120108_23120145/
├── Source/
│   ├── Algorithms/
│   │   ├── astar.py          # A* search algorithm implementation
│   │   ├── backtracking.py   # Backtracking with pruning
│   │   ├── bruteforce.py     # Brute force exhaustive search
│   │   └── pysat.py          # SAT-based solving using PySAT
│   ├── Inputs/               # Test input files (input-01.txt to input-10.txt)
│   ├── Outputs/              # Algorithm outputs organized by algorithm
│   │   ├── AStar/
│   │   ├── Backtracking/
│   │   ├── BruteForce/
│   │   └── PySAT/
│   ├── Solutions/            # Expected solutions for verification
│   ├── main.py              # Main comparison script
│   ├── cnf.py               # CNF generation for SAT solving
│   ├── connectivity.py      # Connectivity checking utilities
│   ├── is_intersect.py      # Bridge intersection detection
│   └── requirements.txt     # Python dependencies
└── README.md               # This file
```

## Features

- **Multiple Algorithm Implementations**: Four different solving approaches
- **Performance Comparison**: Automated benchmarking and timing
- **Solution Verification**: Automatic correctness checking against expected solutions
- **Timeout Handling**: Configurable time limits for each algorithm
- **Comprehensive Reporting**: Detailed comparison tables and summaries

## Requirements

- Python 3.7+
- Required packages (see `requirements.txt`):
  - `numpy >= 1.20.0`
  - `pysat`
  - `python-sat[pblib]`

## Installation

1. Clone or download this repository
2. Navigate to the Source directory:
   ```bash
   cd 23120039_23120108_23120145/Source
   ```
3. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run a Single Test Case

Test all algorithms on a specific input file:
```bash
python main.py --test input-01.txt
```

### Run All Test Cases

Test all algorithms on all input files:
```bash
python main.py --all
```
or simply:
```bash
python main.py
```

### Custom Timeout

Set a custom timeout (in seconds) for algorithms:
```bash
python main.py --all --timeout 120
```

## Input Format

Input files are located in the `Inputs/` directory. Each file contains a comma-separated grid where:
- `0` represents an empty cell
- Numbers `1-8` represent islands with the required number of bridge connections

Example (`input-01.txt`):
```
0,2,0,5,0,0,2
0,0,0,0,0,0,0
4,0,2,0,2,0,4
0,0,0,0,0,0,0
0,1,0,5,0,2,0
0,0,0,0,0,0,0
4,0,0,0,0,0,3
```

## Output Format

Solutions are saved in the `Outputs/` directory, organized by algorithm. Each output file contains the solved puzzle grid where:
- Numbers represent islands
- `-` represents a horizontal bridge
- `|` represents a vertical bridge
- `=` represents a double horizontal bridge
- `$` represents a double vertical bridge
- `0` represents empty cells

Example output:
```
[ "0" , "2" , "=" , "5" , "-" , "-" , "2" ]
[ "0" , "0" , "0" , "$" , "0" , "0" , "|" ]
[ "4" , "=" , "2" , "$" , "2" , "=" , "4" ]
...
```

## Algorithms

### 1. Brute Force
- Exhaustively explores all possible bridge configurations
- Only runs on small grids (≤ 9x9) due to exponential complexity
- Guaranteed to find a solution if one exists

### 2. Backtracking
- Depth-first search with pruning
- Eliminates invalid configurations early
- More efficient than brute force for larger puzzles

### 3. A* Search
- Heuristic-based search algorithm
- Uses informed search to find optimal solutions
- Balances solution quality and search efficiency

### 4. PySAT
- Converts the puzzle to a SAT (Boolean satisfiability) problem
- Uses constraint programming techniques
- Often the fastest for complex puzzles

## Results

The program generates:
- **Per-test comparison tables**: Shows execution time, result status, and correctness for each algorithm
- **Final summary report**: Overview of best performing algorithm for each test case
- **Output files**: Detailed solutions saved for each algorithm

## Algorithm Selection

The system automatically selects the best algorithm based on:
1. **Correctness**: Algorithms with correct solutions are preferred
2. **Speed**: Among correct solutions, the fastest is selected
3. **Priority**: PySAT > AStar > Backtracking > BruteForce (for ties)

## Notes

- Brute Force is automatically skipped for grids larger than 9x9
- Algorithms that exceed the timeout are marked as "TIMEOUT"
- Solutions are verified against expected results in the `Solutions/` directory when available
- All outputs are saved automatically for later review

## Authors

- 23120039
- 23120108
- 23120145

## License

This project is part of a university course assignment (CSAI Project 2).
