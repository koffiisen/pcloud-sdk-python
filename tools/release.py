#!/usr/bin/env python3

"""
Release tool for pCloud SDK Python
Automates version bumping, building, and publishing to PyPI
"""

import re
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional


def run_command(cmd: str, description: str) -> bool:
    """Run a shell command"""
    print(f"= {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f" {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"L {description} failed: {e.stderr}")
        return False


def get_current_version() -> str:
    """Get current version from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")


def bump_version(current: str, bump_type: str) -> str:
    """Bump version number"""
    major, minor, patch = map(int, current.split('.'))
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def update_version_files(new_version: str) -> bool:
    """Update version in all relevant files"""
    files_to_update = [
        ("pyproject.toml", r'version = "[^"]+"', f'version = "{new_version}"'),
        ("pcloud_sdk/__init__.py", r'__version__ = "[^"]+"', f'__version__ = "{new_version}"'),
    ]
    
    for file_path, pattern, replacement in files_to_update:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            new_content = re.sub(pattern, replacement, content)
            path.write_text(new_content)
            print(f" Updated version in {file_path}")
    
    return True


def check_working_directory() -> bool:
    """Check if working directory is clean"""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        print("L Working directory is not clean. Please commit or stash changes first.")
        return False
    return True


def run_tests() -> bool:
    """Run test suite"""
    print(">� Running tests...")
    result = subprocess.run(["python", "-m", "pytest", "tests/", "-x"], capture_output=True)
    if result.returncode != 0:
        print("L Tests failed!")
        return False
    print(" All tests passed")
    return True


def run_lint() -> bool:
    """Run linting checks"""
    return run_command("python tools/lint.py", "Running linting checks")


def build_package() -> bool:
    """Build the package"""
    # Clean previous builds
    run_command("rm -rf build/ dist/ *.egg-info/", "Cleaning previous builds")
    
    # Build the package
    return run_command("python -m build", "Building package")


def publish_to_pypi(test: bool = True) -> bool:
    """Publish to PyPI"""
    if test:
        cmd = "python -m twine upload --repository testpypi dist/*"
        description = "Uploading to Test PyPI"
    else:
        cmd = "python -m twine upload dist/*"
        description = "Uploading to PyPI"
    
    return run_command(cmd, description)


def create_git_tag(version: str) -> bool:
    """Create git tag for release"""
    return run_command(f"git tag -a v{version} -m 'Release v{version}'", 
                      f"Creating git tag v{version}")


def main():
    """Main release process"""
    print("=� pCloud SDK Python Release Tool")
    print("=" * 40)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python tools/release.py <major|minor|patch> [--test-only]")
        print("\nOptions:")
        print("  major    - Bump major version (x.0.0)")
        print("  minor    - Bump minor version (x.y.0)")
        print("  patch    - Bump patch version (x.y.z)")
        print("  --test-only - Only upload to Test PyPI")
        return 1
    
    bump_type = sys.argv[1]
    test_only = "--test-only" in sys.argv
    
    if bump_type not in ["major", "minor", "patch"]:
        print("L Invalid bump type. Use: major, minor, or patch")
        return 1
    
    # Get current version
    try:
        current_version = get_current_version()
        new_version = bump_version(current_version, bump_type)
        print(f"=� Version: {current_version} � {new_version}")
    except Exception as e:
        print(f"L Error getting/bumping version: {e}")
        return 1
    
    # Pre-release checks
    print("\n=
 Pre-release checks...")
    
    if not check_working_directory():
        return 1
    
    if not run_tests():
        print("=� Fix tests before releasing")
        return 1
    
    if not run_lint():
        print("=� Fix linting issues before releasing")
        return 1
    
    # Update version
    print(f"\n=� Updating version to {new_version}...")
    if not update_version_files(new_version):
        return 1
    
    # Build package
    print("\n=� Building package...")
    if not build_package():
        return 1
    
    # Commit version change
    print("\n=� Committing version change...")
    run_command(f"git add .", "Staging changes")
    run_command(f"git commit -m 'Bump version to {new_version}'", "Committing version bump")
    
    # Create tag
    if not create_git_tag(new_version):
        return 1
    
    # Publish package
    print(f"\n< Publishing to {'Test ' if test_only else ''}PyPI...")
    if not publish_to_pypi(test=test_only):
        print("L Publishing failed")
        return 1
    
    print(f"\n<� Release {new_version} completed successfully!")
    
    if test_only:
        print(f"\n=� Test release published. To publish to production PyPI:")
        print(f"   python tools/release.py {bump_type}")
    else:
        print(f"\n=� Don't forget to:")
        print(f"   git push origin main")
        print(f"   git push origin v{new_version}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())