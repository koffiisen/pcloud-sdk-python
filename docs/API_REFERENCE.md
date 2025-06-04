# API Reference

Complete API reference for the pCloud SDK Python v2.0.

## Table of Contents

- [PCloudSDK Class](#pcloudsdk-class)
- [Authentication Methods](#authentication-methods)
- [User Operations](#user-operations)
- [Folder Operations](#folder-operations)
- [File Operations](#file-operations)
- [Progress Utilities](#progress-utilities)
- [Core Classes](#core-classes)
- [Configuration](#configuration)
- [Exception Handling](#exception-handling)

## PCloudSDK Class

The main SDK class that provides a convenient wrapper around all pCloud operations with integrated token management.

### Constructor

```python
PCloudSDK(
    app_key: str = "",
    app_secret: str = "",
    access_token: str = "",
    location_id: int = 2,
    auth_type: str = "direct",
    token_manager: bool = True,
    token_file: str = ".pcloud_credentials"
)
```

**Parameters:**
- `app_key` (str): Your pCloud app key (Client ID) - optional for direct login
- `app_secret` (str): Your pCloud app secret (Client Secret) - optional for direct login
- `access_token` (str): Access token (optional, can be set later)
- `location_id` (int): Server location (1=US, 2=EU) - default EU
- `auth_type` (str): Authentication type ("oauth2" or "direct") - default direct
- `token_manager` (bool): Enable automatic token management (default True)
- `token_file` (str): File to store credentials (default .pcloud_credentials)

**Example:**
```python
from pcloud_sdk import PCloudSDK

# Default configuration (recommended)
sdk = PCloudSDK()

# Custom configuration
sdk = PCloudSDK(
    location_id=1,  # US servers
    token_file=".my_credentials",
    auth_type="oauth2"
)
```

### Properties

#### `user`
Returns a `User` instance for user operations.

```python
user: User
```

#### `folder`
Returns a `Folder` instance for folder operations.

```python
folder: Folder
```

#### `file`
Returns a `File` instance for file operations.

```python
file: File
```

## Authentication Methods

### `login()`

Login with email/password or use saved credentials.

```python
login(
    email: str = "",
    password: str = "",
    location_id: int = 2,
    force_login: bool = False
) -> Dict[str, Any]
```

**Parameters:**
- `email` (str): pCloud email (optional if credentials are saved)
- `password` (str): pCloud password (optional if credentials are saved)
- `location_id` (int): Server location (1=US, 2=EU)
- `force_login` (bool): Force new login even if credentials exist

**Returns:**
- `Dict[str, Any]`: Login information including access_token, locationid, email, etc.

**Example:**
```python
# First time login
login_info = sdk.login("user@example.com", "password")

# Subsequent logins (uses saved token)
login_info = sdk.login()

# Force new login
login_info = sdk.login("user@example.com", "password", force_login=True)
```

### `get_auth_url()`

Get OAuth2 authorization URL.

```python
get_auth_url(redirect_uri: str = "") -> str
```

**Parameters:**
- `redirect_uri` (str): Redirect URI for OAuth2 callback

**Returns:**
- `str`: Authorization URL

**Example:**
```python
auth_url = sdk.get_auth_url("http://localhost:8000/callback")
print(f"Visit: {auth_url}")
```

### `authenticate()`

Exchange authorization code for access token.

```python
authenticate(code: str, location_id: int = 2) -> Dict[str, Any]
```

**Parameters:**
- `code` (str): Authorization code from OAuth2 callback
- `location_id` (int): Server location

**Returns:**
- `Dict[str, Any]`: Token information

**Example:**
```python
token_info = sdk.authenticate("authorization_code_from_callback")
```

### `set_access_token()`

Set access token directly.

```python
set_access_token(access_token: str, auth_type: str = "direct")
```

**Parameters:**
- `access_token` (str): Access token
- `auth_type` (str): Authentication type ("direct" or "oauth2")

### `is_authenticated()`

Check if SDK is authenticated.

```python
is_authenticated() -> bool
```

**Returns:**
- `bool`: True if authenticated

### `logout()`

Logout and clear credentials.

```python
logout()
```

### Token Management Methods

#### `clear_saved_credentials()`

Clear saved credentials file.

```python
clear_saved_credentials()
```

#### `get_saved_email()`

Get the email from saved credentials.

```python
get_saved_email() -> Optional[str]
```

#### `get_credentials_info()`

Get information about current credentials.

```python
get_credentials_info() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Credentials information including email, age, location, etc.

## User Operations

Access via `sdk.user` property.

### `get_user_info()`

Get complete user information.

```python
get_user_info() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Complete user information

**Example:**
```python
user_info = sdk.user.get_user_info()
print(f"Email: {user_info['email']}")
print(f"User ID: {user_info['userid']}")
```

### `get_user_id()`

Get user ID.

```python
get_user_id() -> int
```

**Returns:**
- `int`: User ID

### `get_user_email()`

Get user email.

```python
get_user_email() -> str
```

**Returns:**
- `str`: User email

### `get_used_quota()`

Get used quota in bytes.

```python
get_used_quota() -> int
```

**Returns:**
- `int`: Used quota in bytes

### `get_quota()`

Get total quota in bytes.

```python
get_quota() -> int
```

**Returns:**
- `int`: Total quota in bytes

### `get_public_link_quota()`

Get public link quota.

```python
get_public_link_quota() -> int
```

**Returns:**
- `int`: Public link quota

## Folder Operations

Access via `sdk.folder` property.

### `get_metadata()`

Get folder metadata.

```python
get_metadata(
    folder_id: Optional[int] = None,
    path: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `folder_id` (Optional[int]): Folder ID
- `path` (Optional[str]): Folder path

**Returns:**
- `Dict[str, Any]`: Folder metadata

### `list_root()`

List root folder contents.

```python
list_root() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Root folder contents and metadata

**Example:**
```python
root = sdk.folder.list_root()
contents = root['contents']
for item in contents:
    if item.get('isfolder'):
        print(f"=Á {item['name']}/")
    else:
        print(f"=Ä {item['name']} ({item['size']} bytes)")
```

### `get_content()`

Get folder content.

```python
get_content(
    folder_id: Optional[int] = None,
    path: Optional[str] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `folder_id` (Optional[int]): Folder ID
- `path` (Optional[str]): Folder path

**Returns:**
- `List[Dict[str, Any]]`: List of folder contents

### `create()`

Create new folder.

```python
create(name: str, parent: int = 0) -> Union[int, Dict[str, Any]]
```

**Parameters:**
- `name` (str): Folder name
- `parent` (int): Parent folder ID (0 = root)

**Returns:**
- `Union[int, Dict[str, Any]]`: Folder ID or response dict

**Example:**
```python
folder_id = sdk.folder.create("My New Folder", parent=0)
print(f"Created folder with ID: {folder_id}")
```

### `rename()`

Rename folder.

```python
rename(folder_id: int, name: str) -> Union[int, Dict[str, Any]]
```

**Parameters:**
- `folder_id` (int): Folder ID
- `name` (str): New name

**Returns:**
- `Union[int, Dict[str, Any]]`: Folder ID or response dict

### `move()`

Move folder to another parent.

```python
move(folder_id: int, new_parent: int) -> Union[int, Dict[str, Any]]
```

**Parameters:**
- `folder_id` (int): Folder ID to move
- `new_parent` (int): New parent folder ID

**Returns:**
- `Union[int, Dict[str, Any]]`: Folder ID or response dict

### `delete()`

Delete folder.

```python
delete(folder_id: int) -> Dict[str, Any]
```

**Parameters:**
- `folder_id` (int): Folder ID

**Returns:**
- `Dict[str, Any]`: Deletion result

### `delete_recursive()`

Delete folder recursively.

```python
delete_recursive(folder_id: int) -> Dict[str, Any]
```

**Parameters:**
- `folder_id` (int): Folder ID

**Returns:**
- `Dict[str, Any]`: Deletion result

## File Operations

Access via `sdk.file` property.

### `upload()`

Upload file to pCloud.

```python
upload(
    file_path: str,
    folder_id: int = 0,
    filename: Optional[str] = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]
```

**Parameters:**
- `file_path` (str): Local file path
- `folder_id` (int): Destination folder ID (0 = root)
- `filename` (Optional[str]): Custom filename (optional)
- `progress_callback` (Optional[callable]): Progress callback function

**Returns:**
- `Dict[str, Any]`: Upload result with file metadata

**Example:**
```python
def progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    print(f"Upload: {percentage:.1f}% ({speed/1024/1024:.1f} MB/s)")

result = sdk.file.upload(
    "/path/to/file.txt",
    folder_id=0,
    progress_callback=progress
)
file_id = result['metadata'][0]['fileid']
```

### `download()`

Download file from pCloud.

```python
download(
    file_id: int,
    destination: str = "",
    progress_callback: Optional[callable] = None
) -> bool
```

**Parameters:**
- `file_id` (int): File ID
- `destination` (str): Download destination directory
- `progress_callback` (Optional[callable]): Progress callback function

**Returns:**
- `bool`: True if successful

**Example:**
```python
success = sdk.file.download(
    file_id=123456,
    destination="./downloads/",
    progress_callback=progress
)
```

### `get_link()`

Get download link for file.

```python
get_link(file_id: int) -> str
```

**Parameters:**
- `file_id` (int): File ID

**Returns:**
- `str`: Download URL

### `get_info()`

Get file information.

```python
get_info(file_id: int) -> Dict[str, Any]
```

**Parameters:**
- `file_id` (int): File ID

**Returns:**
- `Dict[str, Any]`: File information including checksum

### `rename()`

Rename file.

```python
rename(file_id: int, name: str) -> Dict[str, Any]
```

**Parameters:**
- `file_id` (int): File ID
- `name` (str): New filename

**Returns:**
- `Dict[str, Any]`: Operation result

### `move()`

Move file to another folder.

```python
move(file_id: int, folder_id: int) -> Dict[str, Any]
```

**Parameters:**
- `file_id` (int): File ID
- `folder_id` (int): Destination folder ID

**Returns:**
- `Dict[str, Any]`: Operation result

### `copy()`

Copy file to another folder.

```python
copy(file_id: int, folder_id: int) -> Dict[str, Any]
```

**Parameters:**
- `file_id` (int): File ID
- `folder_id` (int): Destination folder ID

**Returns:**
- `Dict[str, Any]`: Operation result

### `delete()`

Delete file.

```python
delete(file_id: int) -> Dict[str, Any]
```

**Parameters:**
- `file_id` (int): File ID

**Returns:**
- `Dict[str, Any]`: Deletion result

## Progress Utilities

Built-in progress tracking utilities for upload and download operations.

### Factory Functions

#### `create_progress_bar()`

Create a simple progress bar.

```python
create_progress_bar(
    title: str = "Transfer",
    width: int = 50,
    show_speed: bool = True,
    show_eta: bool = True
) -> SimpleProgressBar
```

**Parameters:**
- `title` (str): Progress bar title
- `width` (int): Progress bar width in characters
- `show_speed` (bool): Show transfer speed
- `show_eta` (bool): Show estimated time remaining

#### `create_detailed_progress()`

Create detailed progress tracker with logging.

```python
create_detailed_progress(log_file: Optional[str] = None) -> DetailedProgress
```

**Parameters:**
- `log_file` (Optional[str]): Optional log file path

#### `create_minimal_progress()`

Create minimal progress tracker (milestones only).

```python
create_minimal_progress() -> MinimalProgress
```

#### `create_silent_progress()`

Create silent progress tracker (CSV logging only).

```python
create_silent_progress(log_file: str) -> SilentProgress
```

**Parameters:**
- `log_file` (str): CSV log file path

### Progress Callback Interface

All progress callbacks receive these parameters:

```python
def progress_callback(
    bytes_transferred: int,
    total_bytes: int,
    percentage: float,
    speed: float,
    **kwargs
):
    """
    Args:
        bytes_transferred: Bytes transferred so far
        total_bytes: Total bytes to transfer
        percentage: Transfer percentage (0-100)
        speed: Transfer speed in bytes per second
        **kwargs: Additional information:
            - operation: "upload" or "download"
            - filename: File name
            - status: "starting", "progress", "saving", "completed", "error"
            - error: Error message (if status="error")
    """
    pass
```

## Core Classes

Advanced users can use core classes directly.

### App Class

Main application configuration class.

```python
from pcloud_sdk import App

app = App()
app.set_app_key("client_id")
app.set_app_secret("client_secret")
app.set_access_token("token")
app.set_location_id(2)
```

#### Methods:
- `set_app_key(app_key: str)`
- `set_app_secret(app_secret: str)`
- `set_access_token(access_token: str, auth_type: str = "oauth2")`
- `set_location_id(location_id: Union[str, int])`
- `get_authorize_code_url() -> str`
- `get_token_from_code(code: str, location_id: Union[str, int]) -> Dict[str, Any]`
- `login_with_credentials(email: str, password: str, location_id: Union[str, int] = 1) -> Dict[str, Any]`

### Request Class

HTTP request handler.

```python
from pcloud_sdk import Request

request = Request(app)
response = request.get("userinfo")
```

### Response Class

HTTP response wrapper.

```python
from pcloud_sdk import Response

response = Response(raw_response)
data = response.json()
```

## Configuration

### Server Locations

```python
# EU servers (default)
sdk = PCloudSDK(location_id=2)

# US servers
sdk = PCloudSDK(location_id=1)
```

### Timeouts

```python
# Set request timeout (seconds)
app = App()
app.set_curl_execution_timeout(1800)  # 30 minutes
```

### File Upload Chunk Size

```python
from pcloud_sdk.config import Config

# Default is 10MB chunks
Config.FILE_PART_SIZE = 5 * 1024 * 1024  # 5MB chunks
```

## Exception Handling

### PCloudException

Main exception class for pCloud SDK errors.

```python
from pcloud_sdk import PCloudException

try:
    result = sdk.file.upload("nonexistent.txt")
except PCloudException as e:
    print(f"pCloud error: {e}")
    print(f"Error code: {e.code}")
except Exception as e:
    print(f"General error: {e}")
```

**Attributes:**
- `message` (str): Error message
- `code` (int): Error code (default: 5000)

### Common Error Codes

- `1000`: Authentication failed
- `2000`: File not found
- `2001`: Folder not found
- `2003`: Access denied
- `2005`: Folder already exists
- `2008`: File name too long
- `2009`: File or folder name is invalid
- `5000`: General error (default)

### Error Handling Best Practices

```python
import logging
from pcloud_sdk import PCloudSDK, PCloudException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_upload(file_path: str) -> bool:
    """Upload with comprehensive error handling"""
    try:
        sdk = PCloudSDK()
        sdk.login()  # May raise authentication error
        
        result = sdk.file.upload(file_path)
        logger.info(f"Upload successful: {file_path}")
        return True
        
    except PCloudException as e:
        if e.code == 1000:
            logger.error("Authentication failed - check credentials")
        elif e.code == 2000:
            logger.error(f"File not found: {file_path}")
        else:
            logger.error(f"pCloud error {e.code}: {e}")
        return False
        
    except FileNotFoundError:
        logger.error(f"Local file not found: {file_path}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
```

## Rate Limiting

The pCloud API has rate limits. The SDK includes automatic retry logic for rate-limited requests:

```python
# Automatic retry with exponential backoff
# No additional configuration needed
result = sdk.file.upload("large_file.zip")
```

## Thread Safety

The SDK is not thread-safe. For concurrent operations, create separate SDK instances:

```python
import threading
from pcloud_sdk import PCloudSDK

def worker_thread(file_path: str):
    # Create separate SDK instance per thread
    sdk = PCloudSDK()
    sdk.login("user@example.com", "password")
    sdk.file.upload(file_path)

# Start multiple threads
threads = []
for file_path in file_list:
    thread = threading.Thread(target=worker_thread, args=(file_path,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()
```

This completes the API reference. For more examples, see the [Examples Guide](EXAMPLES.md).