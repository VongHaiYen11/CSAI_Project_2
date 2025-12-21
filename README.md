# 🌉 Project 02: Hashiwokakero

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-success?style=for-the-badge)


*Introduction to Artificial Intelligence - Class 23TN*  
*Faculty of Information Technology - University of Science, VNU-HCM*

This is a project in the **Introduction to Artificial Intelligence** course at the Faculty of Information Technology, University of Science, Vietnam National University - Ho Chi Minh City. This project implements and compares multiple algorithms for solving **Hashiwokakero (Bridges)** puzzles, evaluating four different solving approaches: A* Search, and PySAT (SAT-based solving), Brute Force, Backtracking.


## 📑 Table of Contents

- [Overview](#overview)
- [Project Description](#project-description)
- [Project Structure](#project-structure)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [How to Use](#how-to-use)
- [Input Format](#input-format)
- [Output Format](#output-format)
- [Algorithms](#algorithms)
- [Results](#results)
- [Notes](#notes)
- [Authors](#authors)

## 📖 Overview

Hashiwokakero, also known as Bridges or Hashi, is a logic puzzle that challenges players to connect numbered islands with a specific number of bridges while following a set of simple rules. Published by Nikoli, this puzzle requires strategic thinking and careful planning to ensure all islands are interconnected without exceeding the allowed number of bridges per island. The game has gained popularity worldwide under different names, such as Ai-Ki-Ai in France, Denmark, the Netherlands, and Belgium. With its elegant design and logical depth, Hashiwokakero offers an engaging challenge for puzzle enthusiasts of all skill levels.

### Example Solved Puzzle
    2 ──── 1
    │
    4 ════ 3 ──── 1
    │
    3 ═══════════ 2

## <a id="project-description"></a> 📋 Project Description

This project presents a comprehensive Hashiwokakero puzzle solver that implements and compares multiple solving algorithms. The puzzle is played on a rectangular grid where some cells contain numbered islands (values from 1 to 8), representing the required number of bridge connections, while the remaining cells are empty. Our solver employs various algorithmic approaches, including Conjunctive Normal Form (CNF) logic, to automatically connect all islands by drawing bridges that satisfy the puzzle's constraints.

The bridges must follow certain criteria:

- They must begin and end at distinct islands, traveling in a straight line between them.
- They must not cross any other bridges or islands.
- They may only run perpendicularly.
- At most two bridges connect a pair of islands.
- The number of bridges connected to each island must match the number on that island.
- The bridges must connect the islands into a single connected group.

## <a id="project-structure"></a> 📁 Project Structure

```
23120039_23120108_23120145/
├── Docs/                     # Project documentation and reports
├── Source/
│   ├── Algorithms/
│   │   ├── astar.py          # A* search algorithm implementation
│   │   ├── backtracking.py   # Backtracking with pruning
│   │   ├── bruteforce.py     # Brute force exhaustive search
│   │   └── pysat.py          # SAT-based solving using PySAT
│   ├── Inputs/               # Test input files
│   │   ├── input-01.txt      # Test case 1
│   │   ├── input-02.txt      # Test case 2
│   │   ├── ...               # Test cases 3-10
│   ├── Outputs/              # Algorithm outputs organized by algorithm
│   │   ├── AStar/            # A* algorithm solutions
│   │   ├── Backtracking/     # Backtracking algorithm solutions
│   │   ├── BruteForce/       # Brute force algorithm solutions
│   │   └── PySAT/            # PySAT algorithm solutions
│   ├── Solutions/            # Expected solutions for verification
│   │   ├── solution-01.txt   # Expected solution for test 1
│   │   ├── solution-02.txt   # Expected solution for test 2
│   │   └── ...               # Expected solutions for tests 3-10
│   ├── Tables_and_Charts/    # Performance analysis and visualization
│   ├── main.py               # Main comparison script
│   ├── cnf.py                # CNF generation for SAT solving
│   ├── connectivity.py       # Connectivity checking utilities
│   ├── is_intersect.py       # Bridge intersection detection
│   ├── requirements.txt      # Python dependencies
│   └── README.txt            # Running instructions
└── README.md                 # Project documentation (this file)
```

## <a id="features"></a> ✨ Features

- **Multiple Algorithm Implementations**: Four different solving approaches
- **Performance Comparison**: Automated benchmarking and timing
- **Solution Verification**: Automatic correctness checking against expected solutions
- **Timeout Handling**: Configurable time limits for each algorithm
- **Comprehensive Reporting**: Detailed comparison tables and summaries

## <a id="requirements"></a> 📦 Requirements

- **Python** 3.7+
- **Required packages** (see `requirements.txt`):
  - `numpy >= 1.20.0`
  - `matplotlib`
  - `tabulate`
  - `pysat`
  - `python-sat[pblib]`

## <a id="installation"></a> 🚀 Installation

### Step 1: Navigate to Source Directory
```bash
cd 23120039_23120108_23120145/Source
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

## <a id="how-to-use"></a> 💻 How to Use

### Run a Single Test Case

Test all algorithms on a specific input file:
```bash
python main.py --test input-01.txt
```

*Note: `input-01.txt` is just an example. Replace it with any input file from the `Inputs/` directory (e.g., `input-02.txt`, `input-03.txt`, etc.).*

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

*Note: `120` is just an example (representing 120 seconds). You can specify any positive integer value. The default timeout is **300 seconds** if not specified.*

## <a id="input-format"></a> 📥 Input Format

Input files are located in the `Inputs/` directory. Each file contains a comma-separated grid where:

- `0` represents an empty cell (no island)
- Numbers `1-8` represent islands with the required number of bridge connections

**Example** (`input-01.txt`):
```
0,2,0,5,0,0,2
0,0,0,0,0,0,0
4,0,2,0,2,0,4
0,0,0,0,0,0,0
0,1,0,5,0,2,0
0,0,0,0,0,0,0
4,0,0,0,0,0,3
```

## <a id="output-format"></a> 📤 Output Format

Solutions are saved in the `Outputs/` directory, organized by algorithm. Each output file contains the solved puzzle grid where:

- **Numbers** represent islands
- **`-`** represents a horizontal bridge
- **`|`** represents a vertical bridge
- **`=`** represents a double horizontal bridge
- **`$`** represents a double vertical bridge
- **`0`** represents empty cells

**Output Location**: `Source/Outputs/{AlgorithmName}/output-{number}.txt`

**Example**: The solution for `input-01.txt` using the A* algorithm is saved at:
```
Source/Outputs/AStar/output-01.txt
```

## <a id="algorithms"></a> 🧮 Algorithms

### 1. Brute Force
- Exhaustively explores all possible bridge configurations
- Only runs on small grids (≤ 9x9) due to exponential complexity
- For grids larger than 9x9, the result will show "NO SOLUTION" with note "Size Limit"
- Guaranteed to find a solution if one exists (for grids ≤ 9x9)

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

## <a id="results"></a> 📊 Results

The program generates:

- **Per-test comparison tables**: Shows execution time, result status, and correctness for each algorithm
- **Final summary report**: Overview of best performing algorithm for each test case
- **Output files**: Detailed solutions saved for each algorithm
- **Performance charts**: Visual comparison of algorithm performance (PNG format)
- **Performance tables**: Detailed performance metrics per algorithm (TXT format)

All results are saved in the `Source/Tables_and_Charts/` directory:
- `table_{Algorithm}.txt` - Performance table for each algorithm
- `chart_{Algorithm}.png` - Performance chart for each algorithm
- `comparison_all_algorithms.png` - Overall comparison visualization
- `test_{number}_result.txt` - Detailed results for each test case
- `final_summary.txt` - Comprehensive performance summary

## <a id="notes"></a> 📝 Notes

- **Brute Force Size Limit**: For grids larger than 9x9, Brute Force is automatically skipped and will show "NO SOLUTION" with the note "Size Limit" in the results table
- **Timeout Handling**: Algorithms that exceed the timeout are marked as "NO SOLUTION" with the note "Time Limit"
- **Solution Verification**: Solutions are verified against expected results in the `Solutions/` directory when available
- **Automatic Saving**: All outputs are saved automatically for later review

## <a id="authors"></a> 👥 Authors

**Group 1 - Class 23TN**

| Member                    | Student ID |
|---------------------------|------------|
| Ung Dung Thanh Hạ         | 23120039   |
| Vòng Hải Yến              | 23120108   |
| Nguyễn Ngọc Duy Mỹ       | 23120145   |

**Instructors**
- Prof. Dr. Lê Hoài Bắc
- Mr. Nguyễn Thanh Tình

<div align="center">

*December 2025*  
*Group 1 | Class 23TN*  
*University of Science, VNU-HCM*

</div>