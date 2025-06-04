#!/usr/bin/env python3
"""
Linting and code quality tools for pCloud SDK
Runs flake8, black, isort, and mypy checks
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful"""
    print(f"🔍 {description}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"⚠️ {description} skipped - tool not installed")
        return True  # Don't fail if tool is not available


def main():
    """Run all linting tools"""
    print("🧹 Running code quality checks for pCloud SDK")
    print("=" * 50)

    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["cd", str(project_root)], shell=True)

    success = True

    # List of checks to run
    checks = [
        # Black formatting check
        (["python", "-m", "black", "--check", "--diff", "pcloud_sdk", "tests", "examples", "tools"],
         "Black code formatting"),

        # isort import sorting check
        (["python", "-m", "isort", "--check-only", "--diff", "pcloud_sdk", "tests", "examples", "tools"],
         "isort import sorting"),

        # Flake8 linting
        (["python", "-m", "flake8", "pcloud_sdk", "tests", "examples", "tools"],
         "Flake8 linting"),

        # MyPy type checking
        (["python", "-m", "mypy", "pcloud_sdk"],
         "MyPy type checking"),
    ]

    for cmd, description in checks:
        if not run_command(cmd, description):
            success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 All checks passed!")
        return 0
    else:
        print("❌ Some checks failed")
        print("\n💡 To auto-fix formatting issues, run:")
        print("   python -m black pcloud_sdk tests examples tools")
        print("   python -m isort pcloud_sdk tests examples tools")
        return 1


if __name__ == "__main__":
    sys.exit(main())