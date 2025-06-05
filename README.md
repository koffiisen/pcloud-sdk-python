# pCloud SDK for Python

[![PyPI version](https://badge.fury.io/py/pcloud-sdk-python.svg)](https://badge.fury.io/py/pcloud-sdk-python)
[![Python versions](https://img.shields.io/pypi/pyversions/pcloud-sdk-python.svg)](https://pypi.org/project/pcloud-sdk-python/)
[![Tests](https://github.com/koffiisen/pcloud-sdk-python/workflows/Tests/badge.svg)](https://github.com/koffiisen/pcloud-sdk-python/actions)
[![Coverage](https://codecov.io/gh/koffiisen/pcloud-sdk-python/branch/main/graph/badge.svg)](https://codecov.io/gh/koffiisen/pcloud-sdk-python)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Python SDK for the pCloud API with automatic token management and real-time progress tracking.

## 🚀 Quick Start

```python
from pcloud_sdk import PCloudSDK

# Simple login with automatic token management (RECOMMENDED)
sdk = PCloudSDK()  # Defaults: EU server, direct auth, token manager enabled
sdk.login("your_email@example.com", "your_password")

# Immediate usage
print(f"Connected: {sdk.user.get_user_email()}")

# Upload with real-time progress
def progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    print(f"📤 {percentage:.1f}% ({speed/1024/1024:.1f} MB/s)")

sdk.file.upload("/path/to/file.txt", progress_callback=progress)

# Next time: instant connection thanks to token manager! 🚀
```

## 📊 Real-time Progress Tracking

The SDK includes a comprehensive callback system for tracking upload and download progress:

```python
from pcloud_sdk.progress_utils import create_progress_bar, create_detailed_progress

# Interactive progress bar
progress_bar = create_progress_bar("My Upload")
sdk.file.upload("file.txt", progress_callback=progress_bar)
# [████████████████████████████████████████] 100.0% (15.2/15.2MB) 2.1MB/s

# Detailed progress with logging
detailed = create_detailed_progress(log_file="transfers.log")
sdk.file.download(file_id, "./downloads/", progress_callback=detailed)

# Custom callback
def my_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    if percentage % 25 == 0:  # Every 25%
        print(f"🎯 {kwargs['operation']}: {percentage:.0f}% complete")

sdk.file.upload("large_file.zip", progress_callback=my_callback)
```

## 🛠️ Installation

```bash
pip install pcloud-sdk-python
```

The SDK only requires the `requests` library as an external dependency.

## ✨ Key Features

🔑 **Integrated Token Manager** - No more manual reconnection!  
🇪🇺 **EU Server by Default** - Optimized for European users  
🔐 **Direct Authentication by Default** - Simpler to use  
💾 **Automatic Credential Saving** - Persistent sessions  
📊 **Real-time Progress Callbacks** - Track uploads/downloads  
🎨 **Ready-to-use Progress Trackers** - 4 different display styles  

## 🏁 Getting Started

### 1. Create a pCloud Application (Optional for direct login)

1. Go to [pCloud Developer Console](https://docs.pcloud.com/my_apps/)
2. Create a new application
3. Note your **Client ID** (App Key) and **Client Secret** (App Secret)
4. Configure your **Redirect URI**

**Note:** For direct login with email/password, you don't need to create an application.

### 2. Authentication - Three Methods Available

#### Method 1: Direct Login with Token Manager (Recommended)

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Simple initialization with optimal defaults
sdk = PCloudSDK()  # token_manager=True, location_id=2 (EU), auth_type="direct"

try:
    # First time: provide email/password
    login_info = sdk.login("your_email@example.com", "your_password")
    print(f"Connected: {login_info['email']}")
    
    # Next times: automatic instant connection!
    # sdk.login()  # No need for email/password, uses saved token
    
except PCloudException as e:
    print(f"Error: {e}")
```

#### Method 2: OAuth2 Flow (For third-party applications)

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Initialize with OAuth2
sdk = PCloudSDK(
    app_key="your_client_id",
    app_secret="your_client_secret",
    auth_type="oauth2"
)

# Step 1: Get authorization URL
auth_url = sdk.get_auth_url("http://localhost:8000/callback")
print(f"Visit this URL: {auth_url}")

# Step 2: Exchange code for token
try:
    token_info = sdk.authenticate("code_from_callback")
    print(f"Access token: {token_info['access_token']}")
except PCloudException as e:
    print(f"Authentication error: {e}")
```

#### Method 3: Existing Token

```python
sdk = PCloudSDK(
    access_token="your_existing_token",
    auth_type="direct",
    token_manager=False  # Optional: disable auto management
)
```

## 🔑 Automatic Token Management

The SDK includes an integrated token manager to avoid frequent reconnections.

### Automatic Features:

- ✅ **Automatic saving** of tokens after connection
- ✅ **Automatic loading** of saved tokens
- ✅ **Validity testing** before use
- ✅ **Transparent reconnection** if token expires
- ✅ **Multi-account management** with separate files

### Basic Usage:

```python
# First use
sdk = PCloudSDK()
sdk.login("email@example.com", "password")
# Token automatically saved to .pcloud_credentials

# Subsequent uses (same script later)
sdk = PCloudSDK()  
sdk.login()  # Instant connection with saved token!
```

### Advanced Configuration:

```python
# Custom credentials file
sdk = PCloudSDK(token_file=".my_pcloud_session")

# Force new connection
sdk.login("email", "password", force_login=True)

# Disable token manager completely
sdk = PCloudSDK(token_manager=False)

# Clean saved credentials
sdk.logout()  # Deletes file and disconnects

# Credentials information
info = sdk.get_credentials_info()
print(f"Connected for {info['age_days']:.1f} days")
```

### Security:

- 🔒 **Encrypted tokens** in credentials file
- ⏰ **Automatic expiration** after 30 days
- 🚫 **No passwords saved** (only tokens)
- 🧹 **Automatic cleanup** of invalid tokens

## 📖 Usage Examples

### User Information

```python
# Get user information
user_info = sdk.user.get_user_info()
print(f"Email: {sdk.user.get_user_email()}")
print(f"Used quota: {sdk.user.get_used_quota()} bytes")
print(f"Total quota: {sdk.user.get_quota()} bytes")
```

### Folder Management

```python
# List root folder contents
root_contents = sdk.folder.list_root()
print("Root contents:", root_contents)

# Create a new folder
folder_id = sdk.folder.create("My New Folder", parent=0)
print(f"Created folder ID: {folder_id}")

# List folder contents
contents = sdk.folder.get_content(folder_id)
print("Folder contents:", contents)

# Rename folder
sdk.folder.rename(folder_id, "New Name")

# Move folder
sdk.folder.move(folder_id, new_parent=0)

# Delete folder
sdk.folder.delete(folder_id)

# Recursive delete
sdk.folder.delete_recursive(folder_id)
```

### File Management

```python
# Upload a file
upload_result = sdk.file.upload(
    file_path="/path/to/file.txt",
    folder_id=0,  # 0 = root folder
    filename="uploaded_file.txt"  # optional
)
file_id = upload_result['metadata'][0]['fileid']
print(f"File uploaded with ID: {file_id}")

# Get file information
file_info = sdk.file.get_info(file_id)
print("File info:", file_info)

# Get download link
download_link = sdk.file.get_link(file_id)
print(f"Download link: {download_link}")

# Download a file
sdk.file.download(file_id, destination="/download/path/")

# Rename a file
sdk.file.rename(file_id, "new_name.txt")

# Move a file
sdk.file.move(file_id, folder_id=new_folder_id)

# Copy a file
sdk.file.copy(file_id, folder_id=destination_folder_id)

# Delete a file
delete_result = sdk.file.delete(file_id)
print("File deleted:", delete_result)
```

### Progress Tracking

```python
from pcloud_sdk.progress_utils import (
    create_progress_bar, create_detailed_progress,
    create_minimal_progress, create_silent_progress
)

# 1. Interactive progress bar
progress_bar = create_progress_bar("Upload Progress")
sdk.file.upload("file.txt", progress_callback=progress_bar)

# 2. Detailed progress with logging
detailed = create_detailed_progress(log_file="transfer.log")
sdk.file.download(file_id, "./downloads/", progress_callback=detailed)

# 3. Minimal progress (milestones only)
minimal = create_minimal_progress()
sdk.file.upload("file.txt", progress_callback=minimal)

# 4. Silent progress (CSV logging only)
silent = create_silent_progress("transfer.csv")
sdk.file.upload("file.txt", progress_callback=silent)

# 5. Custom callback
def custom_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    operation = kwargs.get('operation', 'transfer')
    filename = kwargs.get('filename', 'file')
    
    if percentage % 10 == 0:  # Every 10%
        print(f"{operation} {filename}: {percentage:.0f}% at {speed/1024/1024:.1f} MB/s")

sdk.file.upload("file.txt", progress_callback=custom_progress)
```

### Error Handling

```python
try:
    result = sdk.file.upload("/nonexistent/file.txt")
except PCloudException as e:
    print(f"pCloud error: {e}")
    print(f"Error code: {e.code}")
except Exception as e:
    print(f"General error: {e}")
```

## 🖥️ Command Line Interface

The SDK includes a powerful CLI:

```bash
# Login
pcloud-sdk-python login --email user@example.com

# Get account info
pcloud-sdk-python info

# List root folder
pcloud-sdk-python list

# Upload file with progress
pcloud-sdk-python upload --file /path/to/file.txt --folder-id 0

# Download file
pcloud-sdk-python download --file-id 123456 --destination ./downloads/

# Delete file
pcloud-sdk-python delete --file-id 123456

# Logout
pcloud-sdk-python logout
```

## 🌍 Server Locations

- `location_id=2`: EU servers (default) 🇪🇺
- `location_id=1`: US servers 🇺🇸

```python
# EU server (default)
sdk = PCloudSDK()  # location_id=2 by default

# Force US server
sdk = PCloudSDK(location_id=1)

# Token manager remembers your preferred server
```

## 🔧 Advanced Usage

### Direct Class Usage

```python
from pcloud_sdk import App, User, File, Folder

# Manual configuration
app = App()
app.set_app_key("your_client_id")
app.set_app_secret("your_client_secret")
app.set_access_token("your_token")
app.set_location_id(2)

# Use classes directly
user = User(app)
folder = Folder(app)
file_manager = File(app)
```

### Timeout Configuration

```python
# Configure request timeout (in seconds)
app.set_curl_execution_timeout(1800)  # 30 minutes
```

### Large File Uploads

The SDK automatically handles large file uploads in 10MB chunks:

```python
# Large file upload (automatically handled in chunks)
result = sdk.file.upload("/path/to/large_file.zip", folder_id=0)
```

## 🧪 Testing and Development

```bash
# Install development dependencies
pip install -r requirements/dev.txt

# Run tests
python tools/test_runner.py

# Run linting
python tools/lint.py

# Run benchmarks
python tools/benchmark.py

# Build package
python -m build
```

## 📋 Migration from v1.0

The SDK offers optimized defaults:

| Parameter | Previous Default | v1.0 Default | Reason |
|-----------|-------------|--------------|---------|
| `location_id` | 1 (US) | **2 (EU)** | Better latency for Europe |
| `auth_type` | "oauth2" | **"direct"** | Simpler to use |
| `token_manager` | Not available | **True** | Avoid reconnections |

### Migration Example:

```python
# v1.0 (old)
sdk = PCloudSDK("", "")
sdk.login("email", "password", location_id=2)

# v1.0 - Simple and optimized
sdk = PCloudSDK()  # All optimal defaults
sdk.login("email", "password")
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [PyPI Package](https://pypi.org/project/pcloud-sdk-python/)
- [Documentation](https://pcloud-sdk-python.readthedocs.io/)
- [GitHub Repository](https://github.com/koffiisen/pcloud-sdk-python)
- [pCloud API Documentation](https://docs.pcloud.com/)
- [Issue Tracker](https://github.com/koffiisen/pcloud-sdk-python/issues)

## ✨ Features

### ✅ Implemented
- OAuth2 and direct authentication (email/password)
- **Automatic token manager** 🆕
- **Real-time progress callbacks for upload/download** 🆕
- **Ready-to-use progress utilities** 🆕
- User management
- Folder management (create, delete, rename, move)
- File management (upload, download, delete, rename, move, copy)
- Chunked uploads for large files
- Automatic request retry
- Multi-region support (US/EU) with **EU default** 🆕
- Error handling
- **Automatic reconnection** 🆕
- **Persistent session storage** 🆕

### 🆕 Key Features
- **Integrated Token Manager**: No more manual reconnection!
- **Progress Callbacks**: Real-time transfer tracking
- **Progress Utilities**: Progress bars, logs, detailed displays
- **EU Server Default**: Optimized for European users
- **Direct Authentication Default**: Simpler to use
- **Auto-save Credentials**: Persistent sessions
- **Minimal Configuration**: `PCloudSDK()` is enough!

## 🔄 Differences from PHP SDK
- Uses `requests` instead of cURL
- Native Python exception handling
- Type hints for better documentation
- `PCloudSDK` wrapper class for simplicity
- **Automatic token manager** (not in PHP SDK)
- **Real-time progress callbacks** (not in PHP SDK)

## 📦 Dependencies

- Python 3.7+
- requests >= 2.25.0

---

*This SDK is a modern Python implementation inspired by the official pCloud PHP SDK, with additional features for better Python integration and user experience.*