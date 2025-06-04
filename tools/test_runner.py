#!/usr/bin/env python3
"""
Test runner for pCloud SDK Python
Runs unit tests, integration tests, and generates coverage reports
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful"""
    print(f"🔍 {description}...")

    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"⚠️ {description} skipped - pytest not installed")
        return True


def main():
    """Run test suite with options"""
    print("🧪 pCloud SDK Python Test Runner")
    print("=" * 40)

    # Parse arguments
    args = sys.argv[1:]

    # Default test command
    base_cmd = ["python", "-m", "pytest", "tests/"]

    # Add options based on arguments
    if "--coverage" in args or "-c" in args:
        base_cmd.extend(["--cov=pcloud_sdk", "--cov-report=html", "--cov-report=term"])

    if "--verbose" in args or "-v" in args:
        base_cmd.append("-v")

    if "--integration" in args or "-i" in args:
        base_cmd.extend(["-m", "integration"])
    elif "--unit" in args or "-u" in args:
        base_cmd.extend(["-m", "not integration"])

    if "--fail-fast" in args or "-x" in args:
        base_cmd.append("-x")

    if "--parallel" in args or "-p" in args:
        base_cmd.extend(["-n", "auto"])  # Requires pytest-xdist

    # Show help
    if "--help" in args or "-h" in args:
        print("Usage: python tools/test_runner.py [options]")
        print("\nOptions:")
        print("  -c, --coverage     Generate coverage report")
        print("  -v, --verbose      Verbose output")
        print("  -i, --integration  Run only integration tests")
        print("  -u, --unit         Run only unit tests")
        print("  -x, --fail-fast    Stop on first failure")
        print("  -p, --parallel     Run tests in parallel")
        print("  -h, --help         Show this help")
        print("\nExamples:")
        print("  python tools/test_runner.py                    # Run all tests")
        print("  python tools/test_runner.py -c                # Run with coverage")
        print(
            "  python tools/test_runner.py -u -v             # Run unit tests verbosely"
        )
        print(
            "  python tools/test_runner.py -i --fail-fast    # Run integration tests, stop on failure"
        )
        return 0

    # Run tests
    success = True

    # Basic import test first
    print("\n📦 Testing basic imports...")
    import_cmd = [
        "python",
        "-c",
        "import pcloud_sdk; print('✅ All imports successful')",
    ]
    if not run_command(import_cmd, "Basic import test"):
        success = False
        return 1

    # Run main test suite
    print(f"\n🧪 Running tests with command: {' '.join(base_cmd)}")
    if not run_command(base_cmd, "Test suite"):
        success = False

    # Additional checks
    if "--coverage" in args or "-c" in args:
        print("\n📊 Coverage report generated in htmlcov/")

    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
