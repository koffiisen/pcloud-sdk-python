#!/usr/bin/env python3
"""
Linting and code quality tools for pCloud SDK
Runs black and isort checks
"""

import subprocess
import sys
from pathlib import Path


def safe_print(text: str) -> None:
    """Print text with fallback for systems that don't support Unicode"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fall back to ASCII representation for Windows/other systems
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful"""
    safe_print(f"🔍 {description}...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        safe_print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"❌ {description} failed")
        if e.stdout:
            safe_print("STDOUT:" + e.stdout)
        if e.stderr:
            safe_print("STDERR:" + e.stderr)
        return False
    except FileNotFoundError:
        safe_print(f"⚠️ {description} skipped - tool not installed")
        return True  # Don't fail if tool is not available


def main():
    """Run all linting tools"""
    safe_print("🧹 Running code quality checks for pCloud SDK")
    safe_print("=" * 50)

    # Change to project root
    project_root = Path(__file__).parent.parent
    subprocess.run(["cd", str(project_root)], shell=True)

    success = True

    # List of checks to run
    checks = [
        # Black formatting check
        (
            [
                "python",
                "-m",
                "black",
                "--check",
                "--diff",
                "pcloud_sdk",
                "tests",
                "examples",
                "tools",
            ],
            "Black code formatting",
        ),
        # isort import sorting check
        (
            [
                "python",
                "-m",
                "isort",
                "--check-only",
                "--diff",
                "pcloud_sdk",
                "tests",
                "examples",
                "tools",
            ],
            "isort import sorting",
        ),
    ]

    for cmd, description in checks:
        if not run_command(cmd, description):
            success = False

    safe_print("\n" + "=" * 50)
    if success:
        safe_print("🎉 All checks passed!")
        return 0
    else:
        safe_print("❌ Some checks failed")
        safe_print("\n💡 To auto-fix formatting issues, run:")
        safe_print("   python -m black pcloud_sdk tests examples tools")
        safe_print("   python -m isort pcloud_sdk tests examples tools")
        return 1


if __name__ == "__main__":
    sys.exit(main())
