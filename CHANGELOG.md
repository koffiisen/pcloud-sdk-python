# Changelog

All notable changes to the pCloud SDK for Python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-01-XX

### Added

#### = Token Management
- **Automatic token manager** with persistent storage
- Auto-save and auto-load of authentication tokens
- Token validation and automatic renewal
- Multi-account support with separate credential files
- Encrypted token storage for security

#### =� Progress Tracking
- **Real-time progress callbacks** for file uploads and downloads
- **4 ready-to-use progress trackers**:
  - `SimpleProgressBar`: Interactive progress bar with speed and ETA
  - `DetailedProgress`: Comprehensive logging with checkpoints
  - `MinimalProgress`: Milestone-based progress (25%, 50%, 75%, 100%)
  - `SilentProgress`: CSV logging for automation
- Custom progress callback support with full metrics
- Progress utilities module (`progress_utils.py`)

#### < Regional Optimization
- **EU servers as default** (`location_id=2`) for better European performance
- Automatic server preference saving in token manager
- Improved connection speed for European users

#### = Authentication Improvements
- **Direct authentication as default** (email/password)
- Simplified initialization: `PCloudSDK()` with optimal defaults
- OAuth2 flow still supported for third-party applications
- Automatic credential validation and refresh

#### =� Developer Tools
- **Professional CLI interface** (`pcloud-sdk` command)
- Comprehensive development tools:
  - `tools/lint.py`: Code quality checks (black, flake8, isort, mypy)
  - `tools/test_runner.py`: Advanced test runner with coverage
  - `tools/benchmark.py`: Performance testing and optimization
  - `tools/release.py`: Automated PyPI publishing
- Pre-commit hooks configuration
- GitHub Actions workflows for CI/CD
- Comprehensive test suite with pytest

#### =� Documentation
- Complete English documentation
- API reference with type hints
- Authentication guide with examples
- Progress callback documentation
- Troubleshooting guide
- Installation instructions
- Multiple usage examples

### Changed

#### � Performance & Reliability
- Optimized file upload/download with chunked transfers
- Enhanced error handling and retry logic
- Improved connection stability
- Better memory management for large files
- Automatic reconnection on token expiration

#### =' API Improvements
- Type hints throughout the codebase
- Better error messages and debugging information
- Consistent method naming and parameters
- Enhanced documentation strings
- Improved class structure and inheritance

#### =� Project Structure
- Modern `pyproject.toml` configuration
- Separated requirements files (base, dev, test)
- Professional packaging with proper metadata
- Comprehensive MANIFEST.in for package distribution
- MIT license for open source compliance

### Fixed
- Progress callback integration in file operations
- Token refresh mechanism reliability
- Large file upload stability
- Memory leaks in long-running operations
- Error handling edge cases
- Cross-platform compatibility issues

### Security
- Encrypted token storage
- No plaintext password storage
- Automatic token expiration (30 days)
- Secure credential file permissions
- Input validation and sanitization

### Documentation
- Complete English translation from French
- Professional README with badges and examples
- Comprehensive API documentation
- Usage examples for all features
- Migration guide from v1.0
- Troubleshooting and FAQ sections

### Developer Experience
- Zero-configuration setup for basic usage
- Automatic token management eliminates manual reconnection
- Rich progress feedback for better UX
- Professional CLI for power users
- Comprehensive development tools
- Modern Python packaging standards

## [1.0.0] - 2023-XX-XX

### Added
- Initial release of pCloud SDK for Python
- Basic authentication with OAuth2
- File and folder operations
- User management
- Direct email/password authentication
- Multi-region support (US/EU)
- Error handling with custom exceptions

### Features
- File upload and download
- Folder creation, deletion, and management
- User information retrieval
- Basic progress indicators
- Request retry mechanism
- Cross-platform compatibility

---

## Migration Guide

### Getting Started

Here's how to use the pCloud SDK for Python:

#### Basic usage:
```python
from pcloud_sdk import PCloudSDK

sdk = PCloudSDK("", "")  # Required empty strings
sdk.login("email@example.com", "password", location_id=2)
# Manual reconnection required
```

#### Recommended way:
```python
from pcloud_sdk import PCloudSDK

sdk = PCloudSDK()  # Zero configuration
sdk.login("email@example.com", "password")
# Automatic reconnection with token manager
```

#### New Features Usage:
```python
from pcloud_sdk import PCloudSDK
from pcloud_sdk.progress_utils import create_progress_bar

sdk = PCloudSDK()
sdk.login("email@example.com", "password")

# Upload with progress tracking
progress = create_progress_bar("Upload")
sdk.file.upload("file.txt", progress_callback=progress)

# Next time - instant connection!
sdk = PCloudSDK()
sdk.login()  # Uses saved token automatically
```

### Breaking Changes
- None! This is the initial release

### Deprecated Features
- None for initial release
- US servers as default (EU is now default, but US still supported)

### Recommended Updates
1. Remove empty strings from `PCloudSDK("", "")` � `PCloudSDK()`
2. Remove manual `location_id=2` parameter (now default)
3. Add progress callbacks for better user experience
4. Remove manual reconnection logic (now automatic)

---

## Support

- **Documentation**: [https://pcloud-sdk-python.readthedocs.io/](https://pcloud-sdk-python.readthedocs.io/)
- **Issues**: [https://github.com/pcloud/pcloud-sdk-python/issues](https://github.com/pcloud/pcloud-sdk-python/issues)
- **PyPI**: [https://pypi.org/project/pcloud-sdk/](https://pypi.org/project/pcloud-sdk/)
- **pCloud API**: [https://docs.pcloud.com/](https://docs.pcloud.com/)