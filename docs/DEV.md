# pCloud SDK Python - Developer Guide

This guide provides comprehensive instructions for developers who want to contribute to or work with the pCloud SDK Python project locally.

## ð Table of Contents

- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Development Environment](#development-environment)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

## ð§ Prerequisites

Before starting development, ensure you have the following installed:

- **Python 3.7+** (3.8+ recommended)
- **Git** for version control
- **pip** and **virtualenv** (or **conda**)
- **make** (optional, for convenience commands)

### Verify Installation

```bash
python --version  # Should be 3.7+
git --version
pip --version
```

## ð Project Setup

### 1. Clone the Repository

```bash
git clone https://github.com/koffiisen/pcloud-sdk-python.git
cd pcloud-sdk-python
```

### 2. Create Virtual Environment

Using `venv` (recommended):

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Using `conda`:

```bash
conda create -n pcloud-sdk python=3.8
conda activate pcloud-sdk
```

### 3. Install Development Dependencies

```bash
# Install the package in editable mode with dev dependencies
pip install -e ".[dev,test]"

# Or install all requirements manually
pip install -r requirements/dev.txt
pip install -r requirements/test.txt
pip install -e .
```

### 4. Verify Installation

```bash
python -c "import pcloud_sdk; print(f'pCloud SDK v{pcloud_sdk.__version__} installed successfully')"
```

## ð» Development Environment

### IDE Configuration

#### VS Code
Recommended extensions:
- Python
- Pylance
- Black Formatter
- autoDocstring
- GitLens

Example `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm
- Configure Python interpreter to use your virtual environment
- Enable Black as formatter
- Configure Flake8 as linter
- Set pytest as test runner

### Environment Variables

Create a `.env` file for development (never commit this):

```bash
# Optional: For integration tests
PCLOUD_EMAIL=your-dev-email@example.com
PCLOUD_PASSWORD=your-dev-password

# Development settings
PYTHONPATH=.
PYTHONDONTWRITEBYTECODE=1
```

## ð§ª Running Tests

The project uses **pytest** for testing with **tox** for multi-environment testing.

### Quick Test Run

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pcloud_sdk --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run tests with specific markers
pytest -m "not integration"  # Skip integration tests
pytest -m "slow"             # Run only slow tests
```

### Using Tox (Recommended)

Tox runs tests across multiple Python versions and environments:

```bash
# Install tox
pip install tox

# Run all environments
tox

# Run specific environment
tox -e py38                 # Python 3.8
tox -e py39                 # Python 3.9
tox -e py310                # Python 3.10
tox -e py311                # Python 3.11
tox -e py312                # Python 3.12

# Run linting only
tox -e lint

# Run type checking only
tox -e mypy

# Run coverage report
tox -e coverage
```

### Test Categories

```bash
# Unit tests (fast, no external dependencies)
pytest tests/ -m "not integration"

# Integration tests (require pCloud credentials)
pytest tests/ -m "integration"

# Performance tests
pytest tests/ -m "slow"
```

### Test Configuration

The project uses `pytest.ini` for configuration:

```ini
[tool:pytest]
minversion 💾6.0
addopts 💾-ra -q --strict-markers --strict-config
testpaths 💾tests
python_files 💾test_*.py
python_classes 💾Test*
python_functions 💾test_*
markers =
    integration: Integration tests requiring real API calls
    slow: Slow tests that take more than 5 seconds
```

## ð Code Quality

### Linting with Flake8

```bash
# Run flake8 manually
flake8 pcloud_sdk/ tests/ examples/

# Using the project's lint tool
python tools/lint.py

# Check specific files
flake8 pcloud_sdk/core.py
```

### Code Formatting with Black

```bash
# Format all code
black pcloud_sdk/ tests/ examples/ tools/

# Check formatting without applying
black --check pcloud_sdk/

# Format specific files
black pcloud_sdk/core.py
```

### Import Sorting with isort

```bash
# Sort all imports
isort pcloud_sdk/ tests/ examples/ tools/

# Check import sorting
isort --check-only pcloud_sdk/

# Show diff without applying
isort --diff pcloud_sdk/
```

### Type Checking with MyPy

```bash
# Run type checking
mypy pcloud_sdk/

# Check specific module
mypy pcloud_sdk/core.py

# Generate type coverage report
mypy --html-report mypy-report pcloud_sdk/
```

### Pre-commit Hooks

Install pre-commit hooks to automatically check code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black
pre-commit run flake8
```

### All Quality Checks

Run all quality checks at once:

```bash
# Using tox (recommended)
tox -e lint

# Manual approach
python tools/lint.py
black --check pcloud_sdk/ tests/
isort --check-only pcloud_sdk/ tests/
mypy pcloud_sdk/
flake8 pcloud_sdk/ tests/
```

## ð Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/new-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Development Cycle

```bash
# Make changes to code
# Add tests for new functionality
pytest tests/                    # Run tests
python tools/lint.py            # Check code quality
black pcloud_sdk/ tests/        # Format code
```

### 3. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
# or
git commit -m "fix: resolve issue with specific component"
```

### 4. Pre-merge Checks

```bash
# Run full test suite
tox

# Or run essential checks
pytest --cov=pcloud_sdk
python tools/lint.py
mypy pcloud_sdk/
```

### 5. Push and Create PR

```bash
git push origin feature/new-feature-name
# Create Pull Request via GitHub/GitLab
```

## ð Project Structure

```
pcloud-sdk-python/
✅✅✅ docs/                      # Documentation
✅   ✅✅✅ API_REFERENCE.md       # API reference
✅   ✅✅✅ EXAMPLES.md           # Usage examples
✅   ✅✅✅ DEV.md                # This file
✅✅✅ examples/                  # Example scripts
✅   ✅✅✅ basic_usage.py        # Basic SDK usage
✅   ✅✅✅ oauth2_example.py     # OAuth2 authentication
✅   ✅✅✅ progress_examples.py  # Progress tracking
✅✅✅ pcloud_sdk/               # Main package
✅   ✅✅✅ __init__.py          # Package initialization
✅   ✅✅✅ core.py              # Core SDK functionality
✅   ✅✅✅ file_operations.py   # File operations
✅   ✅✅✅ folder_operations.py # Folder operations
✅   ✅✅✅ user_operations.py   # User operations
✅   ✅✅✅ request.py           # HTTP request handling
✅   ✅✅✅ response.py          # Response processing
✅   ✅✅✅ exceptions.py        # Custom exceptions
✅   ✅✅✅ config.py           # Configuration management
✅   ✅✅✅ progress_utils.py    # Progress tracking utilities
✅✅✅ tests/                    # Test suite
✅   ✅✅✅ test_core.py         # Core functionality tests
✅   ✅✅✅ test_file_operations.py
✅   ✅✅✅ test_folder_operations.py
✅   ✅✅✅ test_authentication.py
✅   ✅✅✅ test_integration.py  # Integration tests
✅✅✅ tools/                    # Development tools
✅   ✅✅✅ lint.py              # Linting script
✅   ✅✅✅ test_runner.py       # Test runner
✅   ✅✅✅ benchmark.py         # Performance benchmarks
✅   ✅✅✅ release.py           # Release automation
✅✅✅ requirements/             # Dependencies
✅   ✅✅✅ base.txt             # Core dependencies
✅   ✅✅✅ dev.txt              # Development dependencies
✅   ✅✅✅ test.txt             # Test dependencies
✅✅✅ pyproject.toml           # Project configuration
✅✅✅ tox.ini                  # Tox configuration
✅✅✅ pytest.ini              # Pytest configuration
✅✅✅ README.md               # Project overview
```

## ð¦ Release Process

### Automated Release via GitHub Actions

Pushing a git tag prefixed with 'v' (e.g., `v1.0.0`, `v1.2.3`) to the repository triggers an automated release workflow. This workflow performs the following steps:

- **Runs tests**: Ensures code quality and functionality.
- **Builds the package**: Creates the distributable package files.
- **Publishes to TestPyPI**: Uploads the package to the Test Python Package Index for pre-production testing.
- **Publishes to PyPI**: Uploads the package to the official Python Package Index, making it available to users.
- **Creates a GitHub Release**: Generates a release entry on GitHub, based on the tag, including release notes and assets.

This automated process relies on the following secrets being configured in the GitHub repository settings:
- `PYPI_API_TOKEN`: For publishing to the official PyPI.
- `TEST_PYPI_API_TOKEN`: For publishing to TestPyPI.

### Development Release (Test PyPI)

```bash
# Run release tool for patch version
python tools/release.py patch --test-only

# For minor or major versions
python tools/release.py minor --test-only
python tools/release.py major --test-only
```

### Production Release

The `tools/release.py` script can assist with version bumping and tagging locally. For example:
```bash
# Bump patch version and create tag
python tools/release.py patch
```
Once a `v*` tag (e.g., `v1.0.1`) is pushed to the repository (e.g., `git push origin v1.0.1`), the automated GitHub Actions workflow handles the PyPI publication and GitHub Release creation.

### Manual Release Steps

The following manual steps can be used as a fallback or for special release scenarios if the automated GitHub Actions workflow is not used:

1. **Update Version**:
   ```bash
   # Update version in pyproject.toml and __init__.py
   ```

2. **Run Tests**:
   ```bash
   tox
   ```

3. **Build Package**:
   ```bash
   python -m build
   ```

4. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

## ð ï¸ Development Tools

### Custom Scripts

The `tools/` directory contains helpful development scripts:

```bash
# Run comprehensive linting
python tools/lint.py

# Run performance benchmarks
python tools/benchmark.py

# Custom test runner with options
python tools/test_runner.py --coverage --integration
```

### Debugging

#### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from pcloud_sdk import PCloudSDK
sdk 💾PCloudSDK(debug=True)
```

#### Use pdb for Debugging

```python
import pdb; pdb.set_trace()  # Set breakpoint
```

#### Profile Performance

```python
import cProfile
import pstats

# Profile your code
pr 💾cProfile.Profile()
pr.enable()
# Your code here
pr.disable()

# Analyze results
stats 💾pstats.Stats(pr)
stats.sort_stats('tottime')
stats.print_stats(10)
```

## ð Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Test Failures

```bash
# Clear pytest cache
pytest --cache-clear

# Run tests in verbose mode
pytest -v

# Run specific failing test
pytest tests/test_specific.py::test_function -v
```

#### Linting Issues

```bash
# Auto-fix common issues
black pcloud_sdk/ tests/
isort pcloud_sdk/ tests/

# See specific flake8 errors
flake8 --show-source pcloud_sdk/
```

#### Tox Issues

```bash
# Recreate tox environments
tox --recreate

# Clear tox cache
rm -rf .tox/
```

### Environment Issues

#### Virtual Environment Problems

```bash
# Recreate virtual environment
deactivate
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,test]"
```

#### Dependency Conflicts

```bash
# Check for conflicts
pip check

# Show dependency tree
pip install pipdeptree
pipdeptree
```

### Performance Issues

#### Memory Usage

```bash
# Monitor memory usage
python -c "
import tracemalloc
tracemalloc.start()
# Your code here
current, peak 💾tracemalloc.get_traced_memory()
print(f'Current: {current / 1024 / 1024:.1f} MB')
print(f'Peak: {peak / 1024 / 1024:.1f} MB')
"
```

#### Network Issues

```bash
# Test network connectivity
python -c "
import requests
try:
    r 💾requests.get('https://api.pcloud.com/userinfo', timeout=5)
    print(f'pCloud API accessible: {r.status_code}')
except Exception as e:
    print(f'Network issue: {e}')
"
```

## ð Getting Help

- **Documentation**: Check `/docs` directory
- **Issues**: Open GitHub issues for bugs
- **Discussions**: Use GitHub discussions for questions
- **Code Review**: Request reviews on pull requests

## ð¤ Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation if needed
7. Submit a pull request

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(file_ops): add progress callback support

Add progress tracking capabilities to upload and download operations.
Includes real-time speed calculation and ETA estimation.

Closes #42
```

---

Happy coding! ð If you encounter any issues or have questions, please don't hesitate to open an issue or start a discussion.