# Installation Guide

This guide covers different installation methods for the pCloud SDK Python package.

## Table of Contents

- [System Requirements](#system-requirements)
- [PyPI Installation](#pypi-installation)
- [Development Installation](#development-installation)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, Linux
- **Dependencies**: `requests 🔄💾2.25.0`

### Python Version Check

```bash
python --version
# or
python3 --version
```

If you don't have Python 3.7+, download it from [python.org](https://www.python.org/downloads/).

## PyPI Installation

### Basic Installation

Install the latest stable version from PyPI:

```bash
pip install pcloud-sdk-python
```

### Specific Version Installation

```bash
# Install specific version
pip install pcloud-sdk-python==2.0.0

# Install with version constraints
pip install "pcloud-sdk-python🔄=2.0.0,<3.0.0"
```

### Upgrade Installation

```bash
# Upgrade to latest version
pip install --upgrade pcloud-sdk-python

# Force reinstall
pip install --force-reinstall pcloud-sdk-python
```

## Development Installation

For contributing to the project or accessing the latest features:

### Clone from Git

```bash
# Clone the repository
git clone https://github.com/koffiisen/pcloud-sdk-python.git
cd pcloud-sdk-python

# Install in development mode
pip install -e .
```

### Install with Development Dependencies

```bash
# Install development dependencies
pip install -e .[dev]

# Or install from requirements files
pip install -r requirements/dev.txt
```

### Development Dependencies Include

- **Testing**: `pytest`, `pytest-cov`, `pytest-mock`
- **Linting**: `flake8`, `black`, `isort`
- **Documentation**: `sphinx`, `sphinx-rtd-theme`
- **Type checking**: `mypy`
- **Pre-commit hooks**: `pre-commit`

## Virtual Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv pcloud-env

# Activate (Linux/macOS)
source pcloud-env/bin/activate

# Activate (Windows)
pcloud-env\Scripts\activate

# Install pCloud SDK
pip install pcloud-sdk-python

# Deactivate when done
deactivate
```

### Using conda

```bash
# Create conda environment
conda create -n pcloud-env python=3.9

# Activate environment
conda activate pcloud-env

# Install pCloud SDK
pip install pcloud-sdk-python

# Deactivate when done
conda deactivate
```

### Using pipenv

```bash
# Create Pipfile and install
pipenv install pcloud-sdk-python

# Activate shell
pipenv shell

# Or run commands directly
pipenv run python your_script.py
```

## Installation Options

### Minimal Installation

For basic usage with minimal dependencies:

```bash
pip install pcloud-sdk-python
```

### Full Installation

For development with all optional dependencies:

```bash
pip install pcloud-sdk-python[dev,test,docs]
```

### Custom Requirements File

Create a `requirements.txt` file:

```txt
pcloud-sdk-python🔄=2.0.0
requests🔄=2.25.0
```

Install from file:

```bash
pip install -r requirements.txt
```

## Verification

### Quick Verification

```python
# Test import
import pcloud_sdk
print(f"pCloud SDK version: {pcloud_sdk.__version__}")

# Test basic functionality
from pcloud_sdk import PCloudSDK
sdk 💾PCloudSDK()
print(" pCloud SDK installed successfully!")
```

### Command Line Verification

```bash
# Check if CLI is available
pcloud-sdk-python --version

# Show help
pcloud-sdk-python --help
```

### Complete Test

```python
#!/usr/bin/env python3
"""
Installation verification script
"""
import sys

def test_installation():
    try:
        # Test imports
        import pcloud_sdk
        from pcloud_sdk import PCloudSDK, PCloudException
        from pcloud_sdk.progress_utils import create_progress_bar
        
        print(" All imports successful")
        print(f"=æ Version: {pcloud_sdk.__version__}")
        
        # Test basic initialization
        sdk 💾PCloudSDK()
        print(" SDK initialization successful")
        
        # Test progress utilities
        progress 💾create_progress_bar("Test")
        print(" Progress utilities working")
        
        print("\n< Installation verified successfully!")
        return True
        
    except ImportError as e:
        print(f"L Import error: {e}")
        return False
    except Exception as e:
        print(f"L Unexpected error: {e}")
        return False

if __name__ =💾"__main__":
    success 💾test_installation()
    sys.exit(0 if success else 1)
```

## Troubleshooting

### Common Installation Issues

#### Permission Errors

**Problem**: Permission denied during installation

**Solution**:
```bash
# Use --user flag
pip install --user pcloud-sdk-python

# Or use virtual environment (recommended)
python -m venv myenv
source myenv/bin/activate  # Linux/macOS
pip install pcloud-sdk-python
```

#### SSL Certificate Errors

**Problem**: SSL certificate verification failed

**Solution**:
```bash
# Upgrade pip and certificates
pip install --upgrade pip
pip install --upgrade certifi

# Install with trusted hosts (temporary)
pip install --trusted-host pypi.org --trusted-host pypi.python.org pcloud-sdk-python
```

#### Python Version Issues

**Problem**: Package not compatible with Python version

**Solution**:
```bash
# Check Python version
python --version

# Use specific Python version
python3.9 -m pip install pcloud-sdk-python

# Update Python if necessary
```

#### Network/Proxy Issues

**Problem**: Cannot connect to PyPI

**Solution**:
```bash
# Use proxy
pip install --proxy http://proxy.company.com:8080 pcloud-sdk-python

# Use different index
pip install -i https://pypi.org/simple/ pcloud-sdk-python

# Use offline installation
pip download pcloud-sdk-python
pip install pcloud-sdk-python*.whl --find-links .
```

### Dependency Conflicts

#### Requests Version Conflict

**Problem**: Conflicting requests library versions

**Solution**:
```bash
# Check current version
pip show requests

# Upgrade requests
pip install --upgrade requests

# Force specific version
pip install "requests🔄=2.25.0"
```

#### Virtual Environment Issues

**Problem**: Packages not found in virtual environment

**Solution**:
```bash
# Verify environment is activated
which python
which pip

# Reinstall in virtual environment
pip install --force-reinstall pcloud-sdk-python
```

### Environment-Specific Issues

#### Windows Issues

```batch
# Use Python Launcher
py -m pip install pcloud-sdk-python

# Check PATH
where python
where pip
```

#### macOS Issues

```bash
# Use python3 explicitly
python3 -m pip install pcloud-sdk-python

# Install via Homebrew Python
brew install python
pip3 install pcloud-sdk-python
```

#### Linux Issues

```bash
# Install system dependencies first
sudo apt-get update
sudo apt-get install python3-pip python3-dev

# Use distribution package manager
sudo apt-get install python3-requests

# Then install pCloud SDK
pip3 install pcloud-sdk-python
```

### Getting Help

If you encounter issues not covered here:

1. **Check GitHub Issues**: Search existing issues at [GitHub Issues](https://github.com/koffiisen/pcloud-sdk-python/issues)
2. **Create New Issue**: Include:
   - Python version (`python --version`)
   - Operating system
   - Full error message
   - Installation command used
3. **Check Dependencies**: Run `pip list` to show installed packages
4. **Enable Verbose Mode**: Use `pip install -v pcloud-sdk-python` for detailed output

### Development Environment Setup

For contributors and advanced users:

```bash
# Clone repository
git clone https://github.com/koffiisen/pcloud-sdk-python.git
cd pcloud-sdk-python

# Create virtual environment
python -m venv dev-env
source dev-env/bin/activate  # Linux/macOS
# or dev-env\Scripts\activate  # Windows

# Install in development mode with all dependencies
pip install -e .[dev,test,docs]

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
python -m pytest tests/

# Run linting
python tools/lint.py

# Build documentation
cd docs && make html
```

This completes your installation! Next, check out the [Authentication Guide](AUTHENTICATION.md) to get started with the SDK.