#!/usr/bin/env python3
"""Project Metrics Summary Script.

Provides a concise overview of project statistics including:
- Source code metrics (files, SLOC, complexity)
- Test code metrics (coverage, test counts)
- Code quality metrics (duplication, risk analysis)

Architecture:
1. Data gathering phase - collect all metrics into data structures
2. Report generation phase - format and display results
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET  # noqa: S405


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    BOLD = "\033[1m"
    CYAN = "\033[0;36m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


@dataclass
class SourceMetrics:
    """Source code metrics."""

    total_files: int = 0
    max_lines: int = 0
    avg_lines: int = 0
    total_sloc: int = 0
    avg_code_paths: float = 0.0
    max_code_paths: int = 0
    duplication_score: str = "N/A"
    top_imports: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class TestMetrics:
    """Test code metrics."""

    total_test_files: int = 0
    total_sloc: int = 0
    unit_tests: int = 0
    functional_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0
    regression_tests: int = 0
    untested_files: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class ComplexityMetrics:
    """Complexity metrics."""

    top5_complex: list[tuple[str, int]] = field(default_factory=list)
    total_paths: int = 0
    avg_paths: float = 0.0
    max_paths: int = 0
    files_high_cc: int = 0
    all_complexities: dict[str, int] = field(default_factory=dict)


@dataclass
class CoverageMetrics:
    """Coverage metrics."""

    overall_coverage: str = "N/A"
    coverage_distribution: dict[str, int] = field(default_factory=dict)
    test_results: str = ""


@dataclass
class RiskMetrics:
    """Risk analysis metrics."""

    high_risk_files: list[tuple[str, int, float, float]] = field(default_factory=list)


@dataclass
class ProjectMetrics:
    """Complete project metrics."""

    source: SourceMetrics = field(default_factory=SourceMetrics)
    tests: TestMetrics = field(default_factory=TestMetrics)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    coverage: CoverageMetrics = field(default_factory=CoverageMetrics)
    risk: RiskMetrics = field(default_factory=RiskMetrics)


def output(message: str) -> None:
    print(message)  # noqa: T201

def run_command(cmd: list[str], message: str = "") -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result."""
    if not message:
        message = f"Running: {' '.join(cmd)}..."
    output(f"{Colors.CYAN}{message}{Colors.NC}")
    return subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603


# ============================================================================
# DATA GATHERING PHASE
# ============================================================================


def gather_complexity_metrics() -> ComplexityMetrics:
    """Gather complexity metrics using radon."""
    metrics = ComplexityMetrics()

    try:
        result = run_command(["uv", "run", "radon", "cc", "src/", "-a", "-j"])
        if result.returncode != 0:
            return metrics

        data = json.loads(result.stdout)

        # Calculate metrics
        file_complexities = []
        file_code_paths = []
        total_code_paths = 0

        for filepath, blocks in data.items():
            if not blocks:
                continue
            max_complexity = max(block.get("complexity", 0) for block in blocks)
            file_complexities.append((filepath, max_complexity))

            file_total = sum(block.get("complexity", 0) for block in blocks)
            file_code_paths.append(file_total)
            total_code_paths += file_total

        file_complexities.sort(key=lambda x: x[1], reverse=True)

        avg_paths_per_file = total_code_paths / len(file_code_paths) if file_code_paths else 0
        max_paths_in_file = max(file_code_paths) if file_code_paths else 0

        result_high = run_command(["uv", "run", "radon", "cc", "src/", "-n", "B", "-s"])
        files_high_cc = len([line for line in result_high.stdout.split("\n") if line and not line.startswith(" ")])

        metrics.top5_complex = file_complexities[:5]
        metrics.total_paths = total_code_paths
        metrics.avg_paths = avg_paths_per_file
        metrics.max_paths = max_paths_in_file
        metrics.files_high_cc = files_high_cc
        metrics.all_complexities = dict(file_complexities)

    except Exception as e:
        output(f"{Colors.YELLOW}Error calculating complexity: {e}{Colors.NC}")

    return metrics


def gather_source_metrics(complexity: ComplexityMetrics) -> SourceMetrics:
    """Gather source code metrics."""
    metrics = SourceMetrics()

    py_files = list(Path("src").rglob("*.py"))
    metrics.total_files = len(py_files)

    # Lines per file statistics
    line_counts = [len(f.read_text().splitlines()) for f in py_files]
    metrics.max_lines = max(line_counts) if line_counts else 0
    metrics.avg_lines = sum(line_counts) // len(line_counts) if line_counts else 0

    # SLOC calculation
    for f in py_files:
        lines = f.read_text().splitlines()
        metrics.total_sloc += sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

    # Code paths from complexity
    metrics.avg_code_paths = complexity.avg_paths
    metrics.max_code_paths = complexity.max_paths

    # Duplication score
    # noinspection PyBroadException
    try:
        result = run_command(["uv", "run", "pylint", "--disable=all", "--enable=duplicate-code", "src/"])
        for line in result.stdout.split("\n"):
            if "Your code has been rated at" in line:
                metrics.duplication_score = line.split("Your code has been rated at")[1].split("/")[0].strip() + "/10"
                break
    except Exception as e:
        # Duplication score is optional, continue without it
        output(f"{Colors.YELLOW}Could not calculate duplication score: {e}{Colors.NC}")

    # Top imports
    import_counts = []
    for f in py_files:
        content = f.read_text()
        count = sum(1 for line in content.splitlines() if line.startswith(("import ", "from ")))
        import_counts.append((str(f), count))
    import_counts.sort(key=lambda x: x[1], reverse=True)
    metrics.top_imports = import_counts[:5]

    return metrics


def gather_test_metrics() -> TestMetrics:
    """Gather test code metrics."""
    metrics = TestMetrics()

    test_files = list(Path("tests").rglob("test_*.py"))
    metrics.total_test_files = len(test_files)

    # Test SLOC
    for f in test_files:
        lines = f.read_text().splitlines()
        metrics.total_sloc += sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

    # Count test functions by type
    _count_test_functions_by_type(metrics)

    # Find untested files
    _find_untested_files(metrics)

    return metrics


def _count_test_functions_by_type(metrics: TestMetrics) -> None:
    """Count test functions by test type."""
    for test_type, attr_name in [
        ("unit", "unit_tests"),
        ("functional", "functional_tests"),
        ("integration", "integration_tests"),
        ("e2e", "e2e_tests"),
        ("regression", "regression_tests"),
    ]:
        test_dir = Path("tests") / test_type
        if test_dir.exists():
            count = 0
            for f in test_dir.rglob("test_*.py"):
                content = f.read_text()
                count += sum(1 for line in content.splitlines() if line.strip().startswith("def test_"))
            setattr(metrics, attr_name, count)


def _find_untested_files(metrics: TestMetrics) -> None:
    """Find source files without corresponding tests."""
    src_files_with_sloc: dict[str, int] = {}
    for src_file in Path("src").rglob("*.py"):
        if "__pycache__" in str(src_file):
            continue
        lines = src_file.read_text().splitlines()
        sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
        if sloc > 20:
            src_files_with_sloc[str(src_file)] = sloc

    tested_modules = set()
    for test_file in Path("tests").rglob("test_*.py"):
        content = test_file.read_text()
        imports = re.findall(r"from appimage_updater\.(\S+) import", content)
        imports += re.findall(r"import appimage_updater\.(\S+)", content)
        for imp in imports:
            module_path = imp.replace(".", "/")
            tested_modules.add(f"src/appimage_updater/{module_path}.py")

    untested: list[tuple[str, int]] = []
    excluded_files: list[str] = ["__init__.py", "__main__.py", "_version.py"]
    for source_file, sloc in src_files_with_sloc.items():
        normalized: str = str(source_file).replace("\\", "/")
        if normalized not in tested_modules and not any(x in normalized for x in excluded_files):
            untested.append((normalized, sloc))

    untested.sort(key=lambda x: x[1], reverse=True)
    metrics.untested_files = untested[:10]


def gather_coverage_metrics() -> CoverageMetrics:
    """Gather coverage metrics by running pytest."""
    metrics = CoverageMetrics()

    result = run_command([
        "uv", "run", "pytest",
        "--timeout", "30",
        "tests/unit", "tests/functional", "tests/integration", "tests/e2e",
        "--cov=src/appimage_updater",
        "--cov-report=xml",
        "--cov-report=html:htmlcov",
        "--quiet", "--no-header", "--tb=no",
    ])

    # Extract test results
    _extract_test_results(result, metrics)

    if not Path("coverage.xml").exists():
        return metrics

    _parse_coverage_xml(metrics)

    return metrics


def _extract_test_results(result: subprocess.CompletedProcess[str], metrics: CoverageMetrics) -> None:
    """Extract test results from pytest output."""
    for line in result.stdout.split("\n"):
        if "passed" in line or "failed" in line or "xfailed" in line:
            metrics.test_results = line.strip()
            break


def _parse_coverage_xml(metrics: CoverageMetrics) -> None:
    """Parse coverage.xml file for coverage metrics."""
    try:
        tree = ET.parse("coverage.xml")  # noqa: S314
        root = tree.getroot()
        line_rate = float(root.attrib.get("line-rate", 0))
        metrics.overall_coverage = f"{line_rate * 100:.1f}%"

        # Coverage distribution
        _calculate_coverage_distribution(root, metrics)

    except Exception as e:
        output(f"{Colors.YELLOW}Error parsing coverage: {e}{Colors.NC}")


def _calculate_coverage_distribution(root: ET.Element, metrics: CoverageMetrics) -> None:
    """Calculate coverage distribution across files."""
    ranges: dict[str, int] = defaultdict(int)
    for package in root.findall(".//package"):
        for cls in package.findall(".//class"):
            filename = cls.attrib.get("filename", "")
            if not filename or "__pycache__" in filename:
                continue

            line_rate = float(cls.attrib.get("line-rate", 0))
            coverage_pct = int(line_rate * 100)
            range_key = _get_coverage_range(coverage_pct)
            ranges[range_key] += 1

    metrics.coverage_distribution = dict(ranges)


def _get_coverage_range(coverage_pct: int) -> str:
    """Get coverage range bucket for a given percentage."""
    ranges = [
        (100, "100%"),
        (90, "90-99%"),
        (80, "80-89%"),
        (70, "70-79%"),
        (60, "60-69%"),
        (50, "50-59%"),
        (40, "40-49%"),
        (30, "30-39%"),
        (20, "20-29%"),
        (10, "10-19%"),
    ]
    for threshold, label in ranges:
        if coverage_pct >= threshold:
            return label
    return "0-9%"


def gather_risk_metrics(complexity: ComplexityMetrics) -> RiskMetrics:
    """Gather risk analysis metrics."""
    metrics = RiskMetrics()

    if not Path("coverage.xml").exists() or not complexity.all_complexities:
        return metrics

    try:
        tree = ET.parse("coverage.xml")  # noqa: S314
        root = tree.getroot()

        file_coverage = {}
        for package in root.findall(".//package"):
            package_name = package.attrib.get("name", "")
            for cls in package.findall(".//class"):
                filename = cls.attrib.get("filename", "")
                if not filename or "__pycache__" in filename:
                    continue

                if package_name and package_name != ".":
                    full_path = f"src/appimage_updater/{package_name}/{filename}"
                else:
                    full_path = f"src/appimage_updater/{filename}"

                line_rate = float(cls.attrib.get("line-rate", 0))
                file_coverage[full_path] = line_rate * 100

        # Calculate risk scores
        ratios = []
        for filepath, comp in complexity.all_complexities.items():
            normalized = filepath.replace("\\", "/")
            if not normalized.startswith("src/"):
                normalized = f"src/appimage_updater/{normalized}"

            coverage = file_coverage.get(normalized, 0)
            risk_score = comp * (100 - coverage) / 100
            ratios.append((normalized, comp, coverage, risk_score))

        ratios.sort(key=lambda x: x[3], reverse=True)
        metrics.high_risk_files = ratios[:5]

    except Exception as e:
        output(f"{Colors.YELLOW}Error calculating risk: {e}{Colors.NC}")

    return metrics


def gather_all_metrics() -> ProjectMetrics:
    """Gather all project metrics."""
    metrics = ProjectMetrics()

    # Order matters - complexity needed for other metrics
    metrics.complexity = gather_complexity_metrics()
    metrics.source = gather_source_metrics(metrics.complexity)
    metrics.tests = gather_test_metrics()
    metrics.coverage = gather_coverage_metrics()
    metrics.risk = gather_risk_metrics(metrics.complexity)

    return metrics


# ============================================================================
# REPORT GENERATION PHASE
# ============================================================================


def output_header(text: str) -> None:
    """output a colored header."""
    output(f"\n{Colors.BOLD}{Colors.GREEN}{text}{Colors.NC}")


def output_section_header(text: str) -> None:
    """output a colored section header."""
    output(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.NC}\n")


def report_source_metrics(metrics: SourceMetrics) -> None:
    """Display source code metrics."""
    output_header("Source Code (src/)")
    output(f"  Total files: {metrics.total_files}")
    output(f"  Maximum lines in a file: {metrics.max_lines}")
    output(f"  Average lines per file: {metrics.avg_lines}")
    output(f"  Total SLOC: {metrics.total_sloc}")
    output(f"  Average code paths per file: {metrics.avg_code_paths:.1f}")
    output(f"  Maximum code paths in a file: {metrics.max_code_paths}")
    output(f"  Code duplication score: {metrics.duplication_score}")
    output("  Top 5 files with most imports:")
    for filepath, count in metrics.top_imports:
        output(f"    {filepath:60s} ({count} imports)")


def report_test_metrics(metrics: TestMetrics) -> None:
    """Display test code metrics."""
    output_header("Test Code (tests/)")
    output(f"  Total test files: {metrics.total_test_files}")
    output(f"  Total SLOC: {metrics.total_sloc}")
    output("  Test breakdown:")
    output(f"    Unit: {metrics.unit_tests}")
    output(f"    Functional: {metrics.functional_tests}")
    output(f"    Integration: {metrics.integration_tests}")
    output(f"    E2E: {metrics.e2e_tests}")
    output(f"    Regression: {metrics.regression_tests}")
    output("  Source files (SLOC > 20) without tests:")
    if metrics.untested_files:
        for filepath, sloc in metrics.untested_files:
            output(f"    {filepath:60s} (SLOC: {sloc})")
    else:
        output("    None - all significant files have tests!")


def report_risk_metrics(metrics: RiskMetrics) -> None:
    """Display risk analysis metrics."""
    output("  Top 5 highest risk files (high complexity + low coverage):")
    if metrics.high_risk_files:
        for filepath, complexity, coverage, risk_score in metrics.high_risk_files:
            output(f"    {filepath:60s} (complexity: {complexity}, coverage: {coverage:.1f}%, risk: {risk_score:.1f})")
    else:
        output(f"    {Colors.YELLOW}N/A (requires coverage.xml and radon){Colors.NC}")


def report_complexity_metrics(metrics: ComplexityMetrics) -> None:
    """Display cyclomatic complexity metrics."""
    output_header("Cyclomatic Complexity")
    if metrics.top5_complex:
        output("  Top 5 most complex files:")
        for filepath, max_cc in metrics.top5_complex:
            output(f"    {filepath:60s} (max: {max_cc})")
        output(f"  Files with complexity > 5: {metrics.files_high_cc}")
        output(f"  Total code paths: {metrics.total_paths}")
    else:
        output(f"  {Colors.YELLOW}radon not installed - skipping complexity analysis{Colors.NC}")


def report_coverage_metrics(metrics: CoverageMetrics) -> None:
    """Display code coverage metrics."""
    output_header("Code Coverage")
    if metrics.test_results:
        output(f"  {metrics.test_results}")
    output(f"  Overall coverage: {metrics.overall_coverage}")

    if metrics.coverage_distribution:
        output("  Coverage distribution:")
        order = ["100%", "90-99%", "80-89%", "70-79%", "60-69%", "50-59%",
                 "40-49%", "30-39%", "20-29%", "10-19%", "0-9%"]
        for range_key in order:
            if range_key in metrics.coverage_distribution:
                count = metrics.coverage_distribution[range_key]
                output(f"    {range_key:8s}: {count:3d} files")


def report_summary(metrics: ProjectMetrics) -> None:
    """Display summary statistics."""
    output_section_header("=== Summary ===")

    total_tests = (
        metrics.tests.unit_tests +
        metrics.tests.functional_tests +
        metrics.tests.integration_tests +
        metrics.tests.e2e_tests +
        metrics.tests.regression_tests
    )

    output(f"  Source files: {metrics.source.total_files} | "
          f"Test files: {metrics.tests.total_test_files} | "
          f"Tests: {total_tests}")

    if metrics.complexity.total_paths:
        test_path_ratio = total_tests / metrics.complexity.total_paths
        output(f"  Code paths: {metrics.complexity.total_paths}")
        output(f"  Test/Path ratio: {test_path_ratio:.2f} "
              f"({total_tests} tests / {metrics.complexity.total_paths} code paths)")

    if metrics.coverage.overall_coverage != "N/A":
        output(f"  Coverage: {metrics.coverage.overall_coverage}")

    output("")


def generate_report(metrics: ProjectMetrics) -> None:
    """Generate and display the complete metrics report."""
    output_section_header("=== Project Metrics Summary ===")

    report_source_metrics(metrics.source)
    report_test_metrics(metrics.tests)
    report_risk_metrics(metrics.risk)
    report_complexity_metrics(metrics.complexity)
    report_coverage_metrics(metrics.coverage)
    report_summary(metrics)


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Main entry point for metrics script."""
    # Phase 1: Gather all data
    metrics = gather_all_metrics()

    # Phase 2: Generate report
    generate_report(metrics)


if __name__ == "__main__":
    main()
