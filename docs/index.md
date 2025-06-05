# pCloud SDK for Python

[![PyPI version](https://badge.fury.io/py/pcloud-sdk-python.svg)](https://badge.fury.io/py/pcloud-sdk-python)
[![Python versions](https://img.shields.io/pypi/pyversions/pcloud-sdk-python.svg)](https://pypi.org/project/pcloud-sdk-python/)
[![Tests](https://github.com/koffiisen/pcloud-sdk-python/workflows/Tests/badge.svg)](https://github.com/koffiisen/pcloud-sdk-python/actions)
[![Coverage](https://codecov.io/gh/koffiisen/pcloud-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/koffiisen/pcloud-sdk-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Python SDK for the pCloud API with automatic token management and real-time progress tracking.

## ð Quick Start

```python
from pcloud_sdk import PCloudSDK

# Simple login with automatic token management (RECOMMENDED)
sdk 💾PCloudSDK()  # Defaults: EU server, direct auth, token manager enabled
sdk.login("your_email@example.com", "your_password")

# Immediate usage
user_info 💾sdk.user.get_info()
print(f"Welcome, {user_info['email']}!")

# Upload a file with progress tracking
result 💾sdk.file.upload("./local_file.pdf", folder_id=0)
print(f"File uploaded: {result['metadata'][0]['name']}")

# Download a file
sdk.file.download(file_id=12345, path="./downloads/")
```

## ✅¨ Key Features

- **ð Automatic Token Management** - Never worry about token expiration again
- **ð Real-time Progress Tracking** - Built-in progress bars and custom callbacks
- **ð Multi-region Support** - US and EU server support with auto-detection
- **ð¡ï¸ Type Safety** - Full type hints for better IDE support
- **✅¡ Modern Architecture** - Clean, Pythonic API design
- **ð§ª Comprehensive Testing** - 95%+ test coverage with integration tests
- **ð Rich Documentation** - Detailed guides, examples, and API reference

## ð¯ Perfect For

- **File Management Applications** - Upload, download, organize files in pCloud
- **Backup Solutions** - Automated backup scripts with progress monitoring
- **Data Migration Tools** - Move data to/from pCloud with reliable error handling
- **Cloud Integration** - Integrate pCloud into existing Python applications

## ð Why This SDK?

| Feature | pCloud SDK | Other Solutions |
|---------|------------|-----------------|
| Token Management | ✅ Automatic | ✅ Manual |
| Progress Tracking | ✅ Built-in | ✅ Custom implementation |
| Type Safety | ✅ Full type hints | ✅ Limited |
| Error Handling | ✅ Comprehensive | ✅ Basic |
| Documentation | ✅ Extensive | ✅ Minimal |
| Testing | ✅ 95%+ coverage | ✅ Limited |

## ð Documentation Structure

- **[Installation](INSTALLATION.md)** - Get up and running quickly
- **[Authentication](AUTHENTICATION.md)** - Login methods and token management
- **[Examples](EXAMPLES.md)** - Common use cases and code samples
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Progress Callbacks](PROGRESS_CALLBACKS.md)** - Track upload/download progress
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Development](DEV.md)** - Contributing and development setup

## ð¤ Contributing

We welcome contributions! Please see our [Development Guide](DEV.md) for details on:

- Setting up the development environment
- Running tests and linting
- Submitting pull requests
- Reporting issues

## ð License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/koffiisen/pcloud-sdk-python/blob/main/LICENSE) file for details.

## ð Links

- **[GitHub Repository](https://github.com/koffiisen/pcloud-sdk-python)**
- **[PyPI Package](https://pypi.org/project/pcloud-sdk-python/)**
- **[Issue Tracker](https://github.com/koffiisen/pcloud-sdk-python/issues)**
- **[Changelog](https://github.com/koffiisen/pcloud-sdk-python/blob/main/CHANGELOG.md)**