#!/usr/bin/env python3
"""Run backend unit tests and enforce a coverage gate using stdlib trace."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

TARGET_MODULES = [
    "backend/main.py",
    "backend/taskbar.py",
    "backend/campus_calendar.py",
    "backend/db_helpers.py",
    "backend/uf_schedule.py",
]


def run_coverage(fail_under: float) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    coverage_dir = repo_root / ".tracecov"
    coverage_dir.mkdir(exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "trace",
        "--count",
        "--summary",
        "-C",
        str(coverage_dir),
        "--module",
        "unittest",
        "discover",
        "-s",
        "backend/tests",
        "-p",
        "test_*.py",
    ]

    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
    stdout_lines = result.stdout.splitlines()
    summary_header_index = next((index for index, line in enumerate(stdout_lines) if line.strip().startswith("lines")), None)

    if summary_header_index is None:
        pre_summary_lines = stdout_lines
    else:
        pre_summary_lines = stdout_lines[:summary_header_index]

    if pre_summary_lines:
        print("\n".join(pre_summary_lines))
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    if result.returncode != 0:
        return result.returncode

    summary_pattern = re.compile(r"^\s*(\d+)\s+([\d.]+)%\s+\S+\s+\((.+)\)$")
    wanted = {(repo_root / module).resolve(): module for module in TARGET_MODULES}
    discovered: dict[Path, tuple[int, float]] = {}

    for line in stdout_lines:
        match = summary_pattern.match(line)
        if not match:
            continue

        lines_ran = int(match.group(1))
        coverage_percent = float(match.group(2))
        module_path = Path(match.group(3)).resolve()

        if module_path in wanted:
            discovered[module_path] = (lines_ran, coverage_percent)

    missing = [path for path in wanted if path not in discovered]
    if missing:
        print("Coverage parsing failed for modules:")
        for path in missing:
            print(f"- {path}")
        return 3

    print("\nCoverage by module (trace summary):")
    weighted_lines = 0
    weighted_coverage = 0.0

    for absolute_path, relative_path in sorted((path, wanted[path]) for path in wanted):
        lines_ran, coverage_percent = discovered[absolute_path]
        weighted_lines += lines_ran
        weighted_coverage += lines_ran * coverage_percent
        print(f"{relative_path}: {coverage_percent:.2f}% ({lines_ran} traced lines)")

    overall = weighted_coverage / weighted_lines if weighted_lines else 100.0
    print(f"\nOverall weighted coverage: {overall:.2f}%")

    if overall < fail_under:
        print(f"Coverage gate failed: required >= {fail_under:.2f}%")
        return 2

    print(f"Coverage gate passed: required >= {fail_under:.2f}%")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run unit tests with stdlib trace coverage gate")
    parser.add_argument("--fail-under", type=float, default=95.0, help="Minimum required coverage percentage")
    args = parser.parse_args()
    return run_coverage(args.fail_under)


if __name__ == "__main__":
    raise SystemExit(main())
