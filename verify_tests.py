#!/usr/bin/env python3
"""
Quick verification script to check if the test setup is working correctly
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required")
        return False

    print("✅ Python version compatible")
    return True


def check_test_files():
    """Check if all test files exist"""
    print("\n📁 Checking test files...")

    expected_files = [
        "tests/__init__.py",
        "tests/test_authentication.py",
        "tests/test_file_operations.py",
        "tests/test_folder_operations.py",
        "tests/test_progress_callbacks.py",
        "tests/test_token_manager.py",
        "tests/test_integration.py"
    ]

    missing_files = []
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        return False

    print("✅ All test files present")
    return True


def check_imports():
    """Check if SDK modules can be imported"""
    print("\n📦 Checking SDK imports...")

    modules_to_test = [
        "pcloud_sdk",
        "pcloud_sdk.core",
        "pcloud_sdk.file_operations",
        "pcloud_sdk.folder_operations",
        "pcloud_sdk.progress_utils",
        "pcloud_sdk.exceptions"
    ]

    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"❌ Failed imports: {failed_imports}")
        return False

    print("✅ All SDK modules importable")
    return True


def check_test_dependencies():
    """Check if test dependencies are available"""
    print("\n🔧 Checking test dependencies...")

    dependencies = [
        "pytest",
        "responses",
        "requests"
    ]

    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing_deps.append(dep)

    if missing_deps:
        print(f"❌ Missing dependencies: {missing_deps}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False

    print("✅ All test dependencies available")
    return True


def run_basic_test():
    """Run a basic test to verify pytest works"""
    print("\n🧪 Running basic test...")

    try:
        # Run just one simple test to verify setup
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/test_authentication.py::TestDirectAuthentication::test_missing_credentials",
            "-v"
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ Basic test passed")
            return True
        else:
            print("❌ Basic test failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        return False


def count_tests():
    """Count total number of tests"""
    print("\n📊 Counting tests...")

    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "--collect-only", "-q"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            lines = result.stdout.split('\n')
            # Look for summary line like "collected 150 items"
            for line in lines:
                if "collected" in line and "items" in line:
                    print(f"✅ {line.strip()}")
                    return True

            # If no summary found, count test files
            test_count = len([line for line in lines if "::test_" in line])
            print(f"✅ Found approximately {test_count} tests")
            return True
        else:
            print("❌ Could not collect tests")
            return False

    except Exception as e:
        print(f"❌ Error counting tests: {e}")
        return False


def main():
    """Main verification function"""
    print("🔍 pCloud SDK Test Setup Verification")
    print("="*50)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")

    checks = [
        ("Python Version", check_python_version),
        ("Test Files", check_test_files),
        ("SDK Imports", check_imports),
        ("Test Dependencies", check_test_dependencies),
        ("Basic Test", run_basic_test),
        ("Test Count", count_tests)
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results.append(False)

    # Summary
    print(f"\n{'='*50}")
    print("📋 VERIFICATION SUMMARY")
    print(f"{'='*50}")

    passed = sum(results)
    total = len(results)

    for i, (check_name, _) in enumerate(checks):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"{check_name:20} {status}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 All checks passed! Test setup is ready.")
        print("\nNext steps:")
        print("- Run tests: python run_tests.py")
        print("- Run with coverage: python run_tests.py --coverage")
        print("- Run specific tests: python run_tests.py --file auth")
        return True
    else:
        print(f"\n❌ {total - passed} checks failed. Please fix issues above.")
        print("\nCommon solutions:")
        print("- Install missing dependencies: pip install -r requirements/test.txt")
        print("- Check Python path includes the project directory")
        print("- Verify all test files are present")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)