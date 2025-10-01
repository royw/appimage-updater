#!/usr/bin/env bash
# Project Metrics Summary Script
# Provides a concise overview of project statistics

set -e

# Colors for output
BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}=== Project Metrics Summary ===${NC}\n"

# === Calculate Complexity First (needed for Source Code metrics) ===
if command -v radon &> /dev/null; then
    complexity_output=$(uv run python3 << 'EOF'
import subprocess
import json
import sys

try:
    # Get complexity in JSON format
    result = subprocess.run(
        ['radon', 'cc', 'src/', '-a', '-j'],
        capture_output=True,
        text=True,
        check=True
    )
    
    data = json.loads(result.stdout)
    
    # Calculate maximum complexity per file and total code paths
    file_complexities = []
    file_code_paths = []
    total_code_paths = 0
    
    for filepath, blocks in data.items():
        if not blocks:
            continue
        # Get the maximum complexity for this file
        max_complexity = max(block.get('complexity', 0) for block in blocks)
        file_complexities.append((filepath, max_complexity))
        
        # Sum all complexities for this file
        file_total = sum(block.get('complexity', 0) for block in blocks)
        file_code_paths.append(file_total)
        total_code_paths += file_total
    
    # Sort by maximum complexity descending
    file_complexities.sort(key=lambda x: x[1], reverse=True)
    
    # Calculate stats
    avg_paths_per_file = total_code_paths / len(file_code_paths) if file_code_paths else 0
    max_paths_in_file = max(file_code_paths) if file_code_paths else 0
    
    # Print top 5
    print("TOP5_START")
    for filepath, max_cc in file_complexities[:5]:
        print(f"{filepath}|{max_cc}")
    print("TOP5_END")
    
    # Print stats
    print(f"TOTAL_PATHS:{total_code_paths}")
    print(f"AVG_PATHS:{avg_paths_per_file:.1f}")
    print(f"MAX_PATHS:{max_paths_in_file}")
        
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
EOF
)
    # Extract metrics
    total_code_paths=$(echo "$complexity_output" | grep "TOTAL_PATHS:" | cut -d: -f2)
    avg_paths_per_file=$(echo "$complexity_output" | grep "AVG_PATHS:" | cut -d: -f2)
    max_paths_in_file=$(echo "$complexity_output" | grep "MAX_PATHS:" | cut -d: -f2)
    files_high_cc=$(radon cc src/ -n B -s 2>/dev/null | grep -E "^[^ ]" | wc -l || echo "0")
else
    total_code_paths="N/A"
    avg_paths_per_file="N/A"
    max_paths_in_file="N/A"
    files_high_cc="N/A"
fi

# === Source Code Metrics ===
echo -e "${BOLD}${GREEN}Source Code (src/)${NC}"

# Total files
total_src_files=$(find src/ -name "*.py" -type f | wc -l)
echo "  Total files: $total_src_files"

# Lines per file statistics
max_lines=$(find src/ -name "*.py" -type f -exec wc -l {} \; | awk '{print $1}' | sort -rn | head -1)
avg_lines=$(find src/ -name "*.py" -type f -exec wc -l {} \; | awk '{sum+=$1; count++} END {printf "%.0f", sum/count}')
echo "  Maximum lines in a file: $max_lines"
echo "  Average lines per file: $avg_lines"

# SLOC (Source Lines of Code) - excluding blank lines and comments
if command -v sloccount &> /dev/null; then
    sloc=$(sloccount src/ 2>/dev/null | grep "^python:" | awk '{print $2}' || echo "N/A")
    echo "  Total SLOC: $sloc"
else
    # Fallback: count non-empty, non-comment lines
    sloc=$(find src/ -name "*.py" -type f -exec grep -v '^\s*#' {} \; | grep -v '^\s*$' | wc -l)
    echo "  Total SLOC (approx): $sloc"
fi

# Code paths metrics
echo "  Average code paths per file: $avg_paths_per_file"
echo "  Maximum code paths in a file: $max_paths_in_file"

# === Test Code Metrics ===
echo -e "\n${BOLD}${GREEN}Test Code (tests/)${NC}"

# Total test files
total_test_files=$(find tests/ -name "test_*.py" -type f | wc -l)
echo "  Total test files: $total_test_files"

# Test SLOC
if command -v sloccount &> /dev/null; then
    test_sloc=$(sloccount tests/ 2>/dev/null | grep "^python:" | awk '{print $2}' || echo "N/A")
    echo "  Total SLOC: $test_sloc"
else
    test_sloc=$(find tests/ -name "*.py" -type f -exec grep -v '^\s*#' {} \; | grep -v '^\s*$' | wc -l)
    echo "  Total SLOC (approx): $test_sloc"
fi

# Count test functions by type
unit_tests=$(grep -r "def test_" tests/unit 2>/dev/null | wc -l || echo "0")
functional_tests=$(grep -r "def test_" tests/functional 2>/dev/null | wc -l || echo "0")
integration_tests=$(grep -r "def test_" tests/integration 2>/dev/null | wc -l || echo "0")
e2e_tests=$(grep -r "def test_" tests/e2e 2>/dev/null | wc -l || echo "0")
regression_tests=$(grep -r "def test_" tests/regression 2>/dev/null | wc -l || echo "0")

echo "  Test breakdown:"
echo "    Unit: $unit_tests"
echo "    Functional: $functional_tests"
echo "    Integration: $integration_tests"
echo "    E2E: $e2e_tests"
echo "    Regression: $regression_tests"

# === Complexity Metrics ===
echo -e "\n${BOLD}${GREEN}Cyclomatic Complexity${NC}"

if command -v radon &> /dev/null; then
    # Parse output (already calculated above)
    echo "  Top 5 most complex files:"
    echo "$complexity_output" | sed -n '/TOP5_START/,/TOP5_END/p' | grep -v "TOP5" | while IFS='|' read -r filepath max_cc; do
        printf "    %-60s (max: %s)\n" "$filepath" "$max_cc"
    done
    
    echo "  Files with complexity > 5: $files_high_cc"
    echo "  Total code paths: $total_code_paths"
else
    echo "  ${YELLOW}radon not installed - skipping complexity analysis${NC}"
fi

# === Code Coverage ===
echo -e "\n${BOLD}${GREEN}Code Coverage${NC}"

if [ -f "coverage.xml" ]; then
    # Parse coverage from coverage.xml
    total_coverage=$(python3 -c "
import xml.etree.ElementTree as ET
try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    line_rate = float(root.attrib.get('line-rate', 0))
    print(f'{line_rate * 100:.1f}%')
except:
    print('N/A')
")
    echo "  Overall coverage: $total_coverage"
    
    # Coverage distribution
    echo "  Coverage distribution:"
    uv run python3 << 'EOF'
import xml.etree.ElementTree as ET
from collections import defaultdict

try:
    tree = ET.parse('coverage.xml')
    root = tree.getroot()
    
    # Count files by coverage range
    ranges = defaultdict(int)
    
    for package in root.findall('.//package'):
        for cls in package.findall('.//class'):
            filename = cls.attrib.get('filename', '')
            # Skip if no filename or if it's a test file
            if not filename or '__pycache__' in filename:
                continue
                
            line_rate = float(cls.attrib.get('line-rate', 0))
            coverage_pct = int(line_rate * 100)
            
            # Determine range
            if coverage_pct == 100:
                range_key = '100%'
            elif coverage_pct >= 90:
                range_key = '90-99%'
            elif coverage_pct >= 80:
                range_key = '80-89%'
            elif coverage_pct >= 70:
                range_key = '70-79%'
            elif coverage_pct >= 60:
                range_key = '60-69%'
            elif coverage_pct >= 50:
                range_key = '50-59%'
            elif coverage_pct >= 40:
                range_key = '40-49%'
            elif coverage_pct >= 30:
                range_key = '30-39%'
            elif coverage_pct >= 20:
                range_key = '20-29%'
            elif coverage_pct >= 10:
                range_key = '10-19%'
            else:
                range_key = '0-9%'
            
            ranges[range_key] += 1
    
    # Print in order
    order = ['100%', '90-99%', '80-89%', '70-79%', '60-69%', '50-59%', 
             '40-49%', '30-39%', '20-29%', '10-19%', '0-9%']
    
    for range_key in order:
        if range_key in ranges:
            count = ranges[range_key]
            print(f"    {range_key:8s}: {count:3d} files")
            
except Exception as e:
    print(f"    Error parsing coverage: {e}")
EOF

elif [ -f "htmlcov/index.html" ]; then
    # Fallback: try to extract from HTML coverage report
    total_coverage=$(grep -oP 'pc_cov">\K[0-9]+%' htmlcov/index.html | head -1 || echo "N/A")
    echo "  Overall coverage: $total_coverage"
    echo "  ${YELLOW}(Run 'task test:coverage' for detailed coverage distribution)${NC}"
else
    echo "  ${YELLOW}No coverage data found - run 'task test:coverage' first${NC}"
fi

# === Summary ===
echo -e "\n${BOLD}${CYAN}=== Summary ===${NC}"

# Count total number of tests
total_tests=$((unit_tests + functional_tests + integration_tests + e2e_tests + regression_tests))

echo "  Source files: $total_src_files | Test files: $total_test_files | Tests: $total_tests"

# Calculate test-to-code-path ratio
if [ "$total_code_paths" != "N/A" ] && [ -n "$total_code_paths" ]; then
    test_path_ratio=$(echo "scale=2; $total_tests / $total_code_paths" | bc 2>/dev/null || echo "N/A")
    echo "  Code paths: $total_code_paths"
    echo "  Test/Path ratio: $test_path_ratio (${total_tests} tests / ${total_code_paths} code paths)"
else
    echo "  Test/Path ratio: N/A (radon required)"
fi

if [ -f "coverage.xml" ]; then
    echo "  Coverage: $total_coverage"
fi

echo ""
