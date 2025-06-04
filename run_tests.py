#!/usr/bin/env python3
"""
Comprehensive test runner for pCloud SDK Python
Provides different test execution modes and reporting options
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def run_unit_tests():
    """Run fast unit tests only"""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "not integration and not slow and not real_api",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "Unit tests")


def run_integration_tests():
    """Run integration tests (may require credentials)"""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "integration",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "Integration tests")


def run_all_tests():
    """Run all tests including slow ones"""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "All tests")


def run_coverage_tests():
    """Run tests with coverage reporting"""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=pcloud_sdk",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=80",
        "-v"
    ]
    return run_command(cmd, "Coverage tests")


def run_performance_tests():
    """Run performance/benchmark tests"""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "performance",
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, "Performance tests")


def run_specific_test_file(test_file):
    """Run a specific test file"""
    if not test_file.startswith("tests/"):
        test_file = f"tests/{test_file}"
    
    if not test_file.endswith(".py"):
        test_file += ".py"
    
    cmd = [
        "python", "-m", "pytest",
        test_file,
        "-v",
        "--tb=short"
    ]
    return run_command(cmd, f"Test file: {test_file}")


def run_specific_test_function(test_path):
    """Run a specific test function (e.g., tests/test_auth.py::TestClass::test_method)"""
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "-v",
        "--tb=long"
    ]
    return run_command(cmd, f"Specific test: {test_path}")


def run_lint_checks():
    """Run code quality checks"""
    print("\n🔍 Running code quality checks...")
    
    checks = [
        (["python", "-m", "flake8", "pcloud_sdk/", "tests/"], "Flake8 linting"),
        (["python", "-m", "pylint", "pcloud_sdk/"], "Pylint analysis"),
        (["python", "-m", "mypy", "pcloud_sdk/"], "MyPy type checking"),
    ]
    
    results = []
    for cmd, description in checks:
        try:
            result = run_command(cmd, description)
            results.append(result)
        except Exception:
            print(f"⚠️ {description} not available (package not installed)")
            results.append(None)
    
    return all(r for r in results if r is not None)


def check_dependencies():
    """Check if required test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-cov", 
        "responses",
        "pytest-mock"
    ]
    
    optional_packages = [
        "pytest-benchmark",
        "pytest-xdist",
        "flake8",
        "pylint",
        "mypy"
    ]
    
    print("\n📦 Checking dependencies...")
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (required)")
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} (optional)")
        except ImportError:
            print(f"⚠️ {package} (optional)")
            missing_optional.append(package)
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install " + " ".join(missing_required))
        return False
    
    if missing_optional:
        print(f"\n⚠️ Missing optional packages: {', '.join(missing_optional)}")
        print("Install with: pip install " + " ".join(missing_optional))
    
    return True


def run_test_discovery():
    """Discover and list all tests"""
    cmd = [
        "python", "-m", "pytest",
        "--collect-only",
        "-q"
    ]
    return run_command(cmd, "Test discovery")


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="pCloud SDK Python Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run unit tests
  python run_tests.py --all              # Run all tests
  python run_tests.py --coverage         # Run with coverage
  python run_tests.py --integration      # Run integration tests
  python run_tests.py --performance      # Run performance tests
  python run_tests.py --file auth        # Run authentication tests
  python run_tests.py --function tests/test_auth.py::TestDirectAuth::test_login
  python run_tests.py --lint             # Run code quality checks
  python run_tests.py --check-deps       # Check dependencies
  python run_tests.py --discover         # Discover all tests
        """
    )
    
    parser.add_argument(
        "--all", action="store_true",
        help="Run all tests including slow ones"
    )
    parser.add_argument(
        "--integration", action="store_true",
        help="Run integration tests"
    )
    parser.add_argument(
        "--coverage", action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--performance", action="store_true",
        help="Run performance/benchmark tests"
    )
    parser.add_argument(
        "--file", type=str,
        help="Run specific test file (e.g., 'auth' for test_authentication.py)"
    )
    parser.add_argument(
        "--function", type=str,
        help="Run specific test function (e.g., 'tests/test_auth.py::TestClass::test_method')"
    )
    parser.add_argument(
        "--lint", action="store_true",
        help="Run code quality checks"
    )
    parser.add_argument(
        "--check-deps", action="store_true",
        help="Check test dependencies"
    )
    parser.add_argument(
        "--discover", action="store_true",
        help="Discover and list all tests"
    )
    parser.add_argument(
        "--real-api", action="store_true",
        help="Include real API tests (requires credentials)"
    )
    
    args = parser.parse_args()
    
    # Check dependencies first
    if args.check_deps:
        success = check_dependencies()
        sys.exit(0 if success else 1)
    
    if not check_dependencies():
        print("❌ Cannot proceed without required dependencies")
        sys.exit(1)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"🧪 pCloud SDK Python Test Runner")
    print(f"Working directory: {os.getcwd()}")
    
    success = True
    
    if args.discover:
        success = run_test_discovery()
    elif args.lint:
        success = run_lint_checks()
    elif args.function:
        success = run_specific_test_function(args.function)
    elif args.file:
        success = run_specific_test_file(args.file)
    elif args.all:
        success = run_all_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.coverage:
        success = run_coverage_tests()
    elif args.performance:
        success = run_performance_tests()
    else:
        # Default: run unit tests
        success = run_unit_tests()
    
    # Summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("- Review coverage report: htmlcov/index.html")
        print("- Run integration tests: python run_tests.py --integration")
        print("- Run performance tests: python run_tests.py --performance")
    else:
        print("❌ Some tests failed!")
        print("\nTroubleshooting:")
        print("- Check test output above for details")
        print("- Run with -v for verbose output")
        print("- Run specific failing tests with --function")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()