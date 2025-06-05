# Usage Examples

Comprehensive examples for the pCloud SDK Python v2.0 covering basic operations, advanced usage patterns, progress tracking, and best practices.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Operations](#basic-operations)
- [File Management](#file-management)
- [Folder Management](#folder-management)
- [Progress Tracking](#progress-tracking)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Real-World Examples](#real-world-examples)

## Quick Start

### Simple File Upload

```python
from pcloud_sdk import PCloudSDK

# Initialize and login
sdk 💾PCloudSDK()
sdk.login("your_email@example.com", "your_password")

# Upload a file
result 💾sdk.file.upload("/path/to/your/file.txt")
print(f"File uploaded with ID: {result['metadata'][0]['fileid']}")
```

### With Progress Bar

```python
from pcloud_sdk import PCloudSDK
from pcloud_sdk.progress_utils import create_progress_bar

sdk 💾PCloudSDK()
sdk.login("your_email@example.com", "your_password")

# Create progress bar
progress 💾create_progress_bar("Uploading")

# Upload with progress tracking
result 💾sdk.file.upload(
    "/path/to/large_file.zip",
    progress_callback=progress
)
```

## Basic Operations

### Authentication and User Info

```python
from pcloud_sdk import PCloudSDK, PCloudException

def get_account_info():
    """Get and display account information"""
    try:
        # Initialize SDK with automatic token management
        sdk 💾PCloudSDK()
        
        # Login (uses saved token if available)
        login_info 💾sdk.login("user@example.com", "password")
        print(f" Connected as: {login_info['email']}")
        
        # Get detailed user information
        user_info 💾sdk.user.get_user_info()
        
        # Display account details
        print(f"\n=d Account Information:")
        print(f"   Email: {user_info['email']}")
        print(f"   User ID: {user_info['userid']}")
        print(f"   Total Quota: {user_info['quota'] / (1024**3):.1f} GB")
        print(f"   Used Quota: {user_info['usedquota'] / (1024**3):.1f} GB")
        print(f"   Free Space: {(user_info['quota'] - user_info['usedquota']) / (1024**3):.1f} GB")
        
        return sdk
        
    except PCloudException as e:
        print(f"L pCloud error: {e}")
        return None
    except Exception as e:
        print(f"L Unexpected error: {e}")
        return None

# Usage
sdk 💾get_account_info()
```

### List Files and Folders

```python
def explore_pcloud(sdk, folder_id=None, path="/"):
    """Explore pCloud folder contents"""
    try:
        if folder_id is None:
            # List root folder
            result 💾sdk.folder.list_root()
            contents 💾result['contents']
            print(f"\n📁 Root Folder Contents:")
        else:
            # List specific folder
            contents 💾sdk.folder.get_content(folder_id)
            print(f"\n📁 Folder {path} Contents:")
        
        folders 💾[item for item in contents if item.get('isfolder')]
        files 💾[item for item in contents if not item.get('isfolder')]
        
        # Display folders
        if folders:
            print("   Folders:")
            for folder in folders:
                print(f"     📁 {folder['name']}/")
        
        # Display files
        if files:
            print("   Files:")
            for file in files:
                size_mb 💾file['size'] / (1024 * 1024)
                print(f"     📁 {file['name']} ({size_mb:.1f} MB)")
        
        print(f"\n📁 Summary: {len(folders)} folders, {len(files)} files")
        return contents
        
    except PCloudException as e:
        print(f"L Error listing folder: {e}")
        return []

# Usage
if sdk:
    contents 💾explore_pcloud(sdk)
```

## File Management

### Upload Files with Different Methods

```python
import os
from pcloud_sdk.progress_utils import create_progress_bar, create_detailed_progress

def upload_examples(sdk):
    """Demonstrate different upload methods"""
    
    # Example 1: Simple upload
    print("1📂 Simple upload:")
    try:
        result 💾sdk.file.upload("document.pdf")
        file_id 💾result['metadata'][0]['fileid']
        print(f"    Uploaded with ID: {file_id}")
    except Exception as e:
        print(f"   L Upload failed: {e}")
    
    # Example 2: Upload to specific folder
    print("\n2📂 Upload to specific folder:")
    try:
        # Create a folder first
        folder_id 💾sdk.folder.create("My Documents")
        
        result 💾sdk.file.upload(
            "document.pdf",
            folder_id=folder_id,
            filename="renamed_document.pdf"
        )
        print(f"    Uploaded to folder {folder_id}")
    except Exception as e:
        print(f"   L Upload failed: {e}")
    
    # Example 3: Upload with progress bar
    print("\n3📂 Upload with progress tracking:")
    try:
        progress 💾create_progress_bar("Document Upload")
        result 💾sdk.file.upload(
            "large_file.zip",
            progress_callback=progress
        )
        print("    Upload completed")
    except Exception as e:
        print(f"   L Upload failed: {e}")
    
    # Example 4: Upload with detailed logging
    print("\n4📂 Upload with detailed logging:")
    try:
        detailed_progress 💾create_detailed_progress("upload.log")
        result 💾sdk.file.upload(
            "data.csv",
            progress_callback=detailed_progress
        )
        print("    Upload completed with logging")
    except Exception as e:
        print(f"   L Upload failed: {e}")

# Usage
if sdk:
    upload_examples(sdk)
```

### Download Files

```python
import tempfile
import os

def download_examples(sdk):
    """Demonstrate different download methods"""
    
    # Get a file to download (use first file found)
    root_contents 💾sdk.folder.list_root()['contents']
    files 💾[item for item in root_contents if not item.get('isfolder')]
    
    if not files:
        print("L No files found to download")
        return
    
    file_to_download 💾files[0]
    file_id 💾file_to_download['fileid']
    filename 💾file_to_download['name']
    
    print(f"=📥 Downloading: {filename}")
    
    # Example 1: Simple download
    print("1📂 Simple download:")
    try:
        temp_dir 💾tempfile.mkdtemp()
        success 💾sdk.file.download(file_id, temp_dir)
        if success:
            downloaded_file 💾os.path.join(temp_dir, filename)
            if os.path.exists(downloaded_file):
                size 💾os.path.getsize(downloaded_file)
                print(f"    Downloaded to: {downloaded_file} ({size} bytes)")
        else:
            print("   L Download failed")
    except Exception as e:
        print(f"   L Download error: {e}")
    
    # Example 2: Download with progress
    print("\n2📂 Download with progress:")
    try:
        progress 💾create_progress_bar("Download")
        temp_dir 💾tempfile.mkdtemp()
        success 💾sdk.file.download(
            file_id,
            temp_dir,
            progress_callback=progress
        )
        if success:
            print("    Download completed")
    except Exception as e:
        print(f"   L Download error: {e}")
    
    # Example 3: Get download link
    print("\n3📂 Get download link:")
    try:
        download_link 💾sdk.file.get_link(file_id)
        print(f"   = Direct link: {download_link}")
    except Exception as e:
        print(f"   L Failed to get link: {e}")

# Usage
if sdk:
    download_examples(sdk)
```

### File Operations

```python
def file_operations_examples(sdk):
    """Demonstrate file operations: rename, move, copy, delete"""
    
    # Upload a test file first
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write("This is a test file for operations")
        test_file_path 💾tmp.name
    
    try:
        # Upload test file
        result 💾sdk.file.upload(test_file_path, filename="test_operations.txt")
        file_id 💾result['metadata'][0]['fileid']
        print(f"=📤 Test file uploaded with ID: {file_id}")
        
        # Example 1: Rename file
        print("\n1📂 Renaming file:")
        try:
            sdk.file.rename(file_id, "renamed_test_file.txt")
            print("    File renamed successfully")
        except Exception as e:
            print(f"   L Rename failed: {e}")
        
        # Example 2: Get file info
        print("\n2📂 Getting file info:")
        try:
            file_info 💾sdk.file.get_info(file_id)
            print(f"   📁 File info: {file_info}")
        except Exception as e:
            print(f"   L Failed to get info: {e}")
        
        # Example 3: Create folder and move file
        print("\n3📂 Moving file to folder:")
        try:
            folder_id 💾sdk.folder.create("Test Folder")
            sdk.file.move(file_id, folder_id)
            print(f"    File moved to folder {folder_id}")
        except Exception as e:
            print(f"   L Move failed: {e}")
        
        # Example 4: Copy file
        print("\n4📂 Copying file:")
        try:
            copy_result 💾sdk.file.copy(file_id, 0)  # Copy to root
            print("    File copied successfully")
        except Exception as e:
            print(f"   L Copy failed: {e}")
        
        # Example 5: Delete file (cleanup)
        print("\n5📂 Deleting files:")
        try:
            sdk.file.delete(file_id)
            print("    Original file deleted")
            
            # Delete the folder too
            sdk.folder.delete(folder_id)
            print("    Test folder deleted")
        except Exception as e:
            print(f"   L Delete failed: {e}")
            
    finally:
        # Clean up local test file
        try:
            os.unlink(test_file_path)
        except:
            pass

# Usage
if sdk:
    file_operations_examples(sdk)
```

## Folder Management

### Create and Organize Folders

```python
def folder_management_examples(sdk):
    """Demonstrate folder management operations"""
    
    # Example 1: Create folder structure
    print("1📂 Creating folder structure:")
    try:
        # Create main folder
        projects_folder 💾sdk.folder.create("My Projects")
        print(f"   📁 Created 'My Projects' folder (ID: {projects_folder})")
        
        # Create subfolders
        web_folder 💾sdk.folder.create("Web Development", parent=projects_folder)
        mobile_folder 💾sdk.folder.create("Mobile Apps", parent=projects_folder)
        docs_folder 💾sdk.folder.create("Documentation", parent=projects_folder)
        
        print(f"   📁 Created subfolders:")
        print(f"      - Web Development (ID: {web_folder})")
        print(f"      - Mobile Apps (ID: {mobile_folder})")
        print(f"      - Documentation (ID: {docs_folder})")
        
    except Exception as e:
        print(f"   L Folder creation failed: {e}")
        return
    
    # Example 2: List folder contents
    print("\n2📂 Listing folder contents:")
    try:
        contents 💾sdk.folder.get_content(projects_folder)
        print(f"   📁 'My Projects' contains {len(contents)} items:")
        for item in contents:
            if item.get('isfolder'):
                print(f"      📁 {item['name']}/")
    except Exception as e:
        print(f"   L Failed to list contents: {e}")
    
    # Example 3: Rename folder
    print("\n3📂 Renaming folder:")
    try:
        sdk.folder.rename(docs_folder, "Project Documentation")
        print("    Renamed 'Documentation' to 'Project Documentation'")
    except Exception as e:
        print(f"   L Rename failed: {e}")
    
    # Example 4: Move folder
    print("\n4📂 Moving folder:")
    try:
        archive_folder 💾sdk.folder.create("Archive")
        sdk.folder.move(mobile_folder, archive_folder)
        print(f"    Moved 'Mobile Apps' to 'Archive' folder")
    except Exception as e:
        print(f"   L Move failed: {e}")
    
    # Example 5: Cleanup (delete folders)
    print("\n5📂 Cleaning up:")
    try:
        sdk.folder.delete_recursive(projects_folder)
        sdk.folder.delete_recursive(archive_folder)
        print("    Cleaned up test folders")
    except Exception as e:
        print(f"   L Cleanup failed: {e}")

# Usage
if sdk:
    folder_management_examples(sdk)
```

## Progress Tracking

### Different Progress Styles

```python
import time
import tempfile
import os
from pcloud_sdk.progress_utils import (
    create_progress_bar, create_detailed_progress,
    create_minimal_progress, create_silent_progress
)

def progress_tracking_examples(sdk):
    """Demonstrate different progress tracking styles"""
    
    # Create a test file for upload
    test_file 💾tempfile.NamedTemporaryFile(mode='wb', suffix='.dat', delete=False)
    test_data 💾b'0' * (5 * 1024 * 1024)  # 5MB test file
    test_file.write(test_data)
    test_file.close()
    
    try:
        # Example 1: Simple progress bar
        print("1📂 Simple Progress Bar:")
        progress_bar 💾create_progress_bar("Upload Test", width=40)
        result 💾sdk.file.upload(test_file.name, filename="test1.dat", progress_callback=progress_bar)
        file_id_1 💾result['metadata'][0]['fileid']
        
        # Example 2: Detailed progress with logging
        print("\n2📂 Detailed Progress with Logging:")
        detailed_progress 💾create_detailed_progress("upload_detailed.log")
        result 💾sdk.file.upload(test_file.name, filename="test2.dat", progress_callback=detailed_progress)
        file_id_2 💾result['metadata'][0]['fileid']
        
        # Example 3: Minimal progress (milestones only)
        print("\n3📂 Minimal Progress:")
        minimal_progress 💾create_minimal_progress()
        result 💾sdk.file.upload(test_file.name, filename="test3.dat", progress_callback=minimal_progress)
        file_id_3 💾result['metadata'][0]['fileid']
        
        # Example 4: Silent progress (CSV logging only)
        print("\n4📂 Silent Progress (check silent_log.csv):")
        silent_progress 💾create_silent_progress("silent_log.csv")
        result 💾sdk.file.upload(test_file.name, filename="test4.dat", progress_callback=silent_progress)
        file_id_4 💾result['metadata'][0]['fileid']
        
        # Example 5: Custom progress callback
        print("\n5📂 Custom Progress Callback:")
        def custom_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            """Custom progress callback with emojis"""
            operation 💾kwargs.get('operation', 'transfer')
            filename 💾kwargs.get('filename', 'file')
            status 💾kwargs.get('status', 'progress')
            
            if status =💾"starting":
                print(f"🚀 Starting {operation} of {filename}")
            elif status =💾"completed":
                elapsed 💾kwargs.get('elapsed', 0)
                print(f" {operation.title()} completed in {elapsed:.1f}s")
            elif int(percentage) % 25 =💾0:  # Every 25%
                speed_mb 💾speed / (1024 * 1024)
                print(f"📁 {operation.title()}: {percentage:.0f}% at {speed_mb:.1f} MB/s")
        
        result 💾sdk.file.upload(test_file.name, filename="test5.dat", progress_callback=custom_progress)
        file_id_5 💾result['metadata'][0]['fileid']
        
        # Cleanup uploaded files
        print("\n🧹 Cleaning up test files...")
        for file_id in [file_id_1, file_id_2, file_id_3, file_id_4, file_id_5]:
            try:
                sdk.file.delete(file_id)
            except:
                pass
        
    finally:
        # Clean up local test file
        try:
            os.unlink(test_file.name)
        except:
            pass

# Usage
if sdk:
    progress_tracking_examples(sdk)
```

### Download Progress Examples

```python
def download_progress_examples(sdk):
    """Demonstrate progress tracking for downloads"""
    
    # First, upload a file to download
    test_file 💾tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False)
    test_data 💾b'A' * (3 * 1024 * 1024)  # 3MB test file
    test_file.write(test_data)
    test_file.close()
    
    try:
        # Upload file
        print("=📤 Uploading test file for download...")
        result 💾sdk.file.upload(test_file.name, filename="download_test.zip")
        file_id 💾result['metadata'][0]['fileid']
        
        # Download with different progress styles
        download_dir 💾tempfile.mkdtemp()
        
        print("\n=📥 Download with Progress Bar:")
        progress_bar 💾create_progress_bar("Download", show_eta=True)
        success 💾sdk.file.download(file_id, download_dir, progress_callback=progress_bar)
        
        if success:
            print(" Download completed successfully")
        
        # Cleanup
        sdk.file.delete(file_id)
        import shutil
        shutil.rmtree(download_dir)
        
    finally:
        try:
            os.unlink(test_file.name)
        except:
            pass

# Usage
if sdk:
    download_progress_examples(sdk)
```

## Advanced Usage Patterns

### Batch Operations

```python
import os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_upload_example(sdk, folder_path):
    """Upload multiple files from a folder"""
    
    print(f"📁 Batch uploading from: {folder_path}")
    
    # Get all files in folder
    file_patterns 💾['*.txt', '*.pdf', '*.doc', '*.docx', '*.jpg', '*.png']
    files_to_upload 💾[]
    
    for pattern in file_patterns:
        files_to_upload.extend(glob.glob(os.path.join(folder_path, pattern)))
    
    if not files_to_upload:
        print("L No files found to upload")
        return
    
    print(f"📁 Found {len(files_to_upload)} files to upload")
    
    # Create a folder for batch upload
    try:
        batch_folder_id 💾sdk.folder.create("Batch Upload")
        print(f"📁 Created batch folder (ID: {batch_folder_id})")
    except Exception as e:
        print(f"L Failed to create folder: {e}")
        return
    
    # Upload files one by one with progress
    uploaded_files 💾[]
    failed_files 💾[]
    
    for i, file_path in enumerate(files_to_upload, 1):
        filename 💾os.path.basename(file_path)
        print(f"\n=📤 [{i}/{len(files_to_upload)}] Uploading: {filename}")
        
        try:
            # Simple progress for batch uploads
            def batch_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
                if percentage % 20 =💾0:  # Every 20%
                    print(f"   📁 {percentage:.0f}%...")
            
            result 💾sdk.file.upload(
                file_path,
                folder_id=batch_folder_id,
                progress_callback=batch_progress
            )
            
            file_id 💾result['metadata'][0]['fileid']
            uploaded_files.append((filename, file_id))
            print(f"    Uploaded successfully (ID: {file_id})")
            
        except Exception as e:
            failed_files.append((filename, str(e)))
            print(f"   L Upload failed: {e}")
    
    # Summary
    print(f"\n📁 Batch Upload Summary:")
    print(f"    Successful: {len(uploaded_files)}")
    print(f"   L Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nL Failed files:")
        for filename, error in failed_files:
            print(f"   - {filename}: {error}")
    
    return batch_folder_id, uploaded_files

def batch_download_example(sdk, folder_id, download_dir):
    """Download all files from a folder"""
    
    print(f"=📥 Batch downloading from folder ID: {folder_id}")
    
    try:
        # Get folder contents
        contents 💾sdk.folder.get_content(folder_id)
        files 💾[item for item in contents if not item.get('isfolder')]
        
        if not files:
            print("L No files found in folder")
            return
        
        print(f"📁 Found {len(files)} files to download")
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        downloaded_files 💾[]
        failed_files 💾[]
        
        for i, file_item in enumerate(files, 1):
            file_id 💾file_item['fileid']
            filename 💾file_item['name']
            
            print(f"\n=📥 [{i}/{len(files)}] Downloading: {filename}")
            
            try:
                success 💾sdk.file.download(file_id, download_dir)
                if success:
                    downloaded_files.append(filename)
                    print(f"    Downloaded successfully")
                else:
                    failed_files.append((filename, "Download returned False"))
                    print(f"   L Download failed")
                    
            except Exception as e:
                failed_files.append((filename, str(e)))
                print(f"   L Download failed: {e}")
        
        # Summary
        print(f"\n📁 Batch Download Summary:")
        print(f"    Successful: {len(downloaded_files)}")
        print(f"   L Failed: {len(failed_files)}")
        
        return downloaded_files
        
    except Exception as e:
        print(f"L Batch download failed: {e}")
        return []

# Usage examples
if sdk:
    # Example folder path (adjust as needed)
    # folder_id, uploaded 💾batch_upload_example(sdk, "/path/to/your/files")
    
    # Download example
    # downloads 💾batch_download_example(sdk, folder_id, "./downloads")
    pass
```

### Synchronization Example

```python
import os
import hashlib

def sync_folder_to_pcloud(sdk, local_folder, remote_folder_id=0):
    """Synchronize local folder with pCloud folder"""
    
    print(f"= Synchronizing {local_folder} with pCloud...")
    
    # Get local files
    local_files 💾{}
    for root, dirs, files in os.walk(local_folder):
        for file in files:
            file_path 💾os.path.join(root, file)
            rel_path 💾os.path.relpath(file_path, local_folder)
            
            # Calculate file hash for comparison
            with open(file_path, 'rb') as f:
                file_hash 💾hashlib.md5(f.read()).hexdigest()
            
            local_files[rel_path] 💾{
                'path': file_path,
                'size': os.path.getsize(file_path),
                'hash': file_hash,
                'mtime': os.path.getmtime(file_path)
            }
    
    # Get remote files
    remote_files 💾{}
    try:
        contents 💾sdk.folder.get_content(remote_folder_id)
        for item in contents:
            if not item.get('isfolder'):
                remote_files[item['name']] 💾{
                    'id': item['fileid'],
                    'size': item['size']
                }
    except Exception as e:
        print(f"L Failed to get remote files: {e}")
        return
    
    # Compare and sync
    to_upload 💾[]
    to_update 💾[]
    
    for rel_path, local_info in local_files.items():
        filename 💾os.path.basename(rel_path)
        
        if filename not in remote_files:
            # File doesn't exist remotely
            to_upload.append((rel_path, local_info))
        else:
            remote_info 💾remote_files[filename]
            if local_info['size'] !💾remote_info['size']:
                # File size differs, needs update
                to_update.append((rel_path, local_info, remote_info))
    
    print(f"📁 Sync Analysis:")
    print(f"   =📤 Files to upload: {len(to_upload)}")
    print(f"   = Files to update: {len(to_update)}")
    
    # Upload new files
    for rel_path, local_info in to_upload:
        try:
            print(f"=📤 Uploading: {rel_path}")
            result 💾sdk.file.upload(
                local_info['path'],
                folder_id=remote_folder_id,
                filename=os.path.basename(rel_path)
            )
            print(f"    Uploaded successfully")
        except Exception as e:
            print(f"   L Upload failed: {e}")
    
    # Update existing files
    for rel_path, local_info, remote_info in to_update:
        try:
            print(f"= Updating: {rel_path}")
            # Delete old file
            sdk.file.delete(remote_info['id'])
            # Upload new version
            result 💾sdk.file.upload(
                local_info['path'],
                folder_id=remote_folder_id,
                filename=os.path.basename(rel_path)
            )
            print(f"    Updated successfully")
        except Exception as e:
            print(f"   L Update failed: {e}")
    
    print(" Synchronization completed")

# Usage
if sdk:
    # sync_folder_to_pcloud(sdk, "/path/to/local/folder")
    pass
```

## Error Handling

### Comprehensive Error Handling

```python
import logging
from pcloud_sdk import PCloudException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger 💾logging.getLogger(__name__)

def robust_file_operations(sdk):
    """Demonstrate robust error handling for file operations"""
    
    def safe_upload(file_path, max_retries=3):
        """Upload with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                print(f"=📤 Upload attempt {attempt + 1}/{max_retries}: {file_path}")
                
                # Check if file exists
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Local file not found: {file_path}")
                
                # Check file size
                file_size 💾os.path.getsize(file_path)
                if file_size =💾0:
                    raise ValueError("Cannot upload empty file")
                
                # Attempt upload
                result 💾sdk.file.upload(file_path)
                print(f"    Upload successful")
                return result
                
            except PCloudException as e:
                error_msg 💾str(e).lower()
                
                if "authentication" in error_msg or "token" in error_msg:
                    print(f"   = Authentication error: {e}")
                    # Try to re-authenticate
                    try:
                        sdk.login()
                        continue  # Retry with new token
                    except Exception as auth_e:
                        print(f"   L Re-authentication failed: {auth_e}")
                        break
                
                elif "quota" in error_msg or "storage" in error_msg:
                    print(f"   =⚠ Storage quota exceeded: {e}")
                    break  # Don't retry for quota issues
                
                elif "network" in error_msg or "connection" in error_msg:
                    if attempt ⏱max_retries - 1:
                        wait_time 💾2 ** attempt
                        print(f"   < Network error, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"   L Network error, max retries reached: {e}")
                        break
                
                else:
                    print(f"   L pCloud error: {e}")
                    if attempt ⏱max_retries - 1:
                        time.sleep(1)
                        continue
                    break
                    
            except FileNotFoundError as e:
                print(f"   L File error: {e}")
                break  # Don't retry for file not found
                
            except Exception as e:
                print(f"   L Unexpected error: {e}")
                if attempt ⏱max_retries - 1:
                    time.sleep(1)
                    continue
                break
        
        print(f"   L Upload failed after {max_retries} attempts")
        return None
    
    def safe_download(file_id, destination, max_retries=3):
        """Download with retry logic and error handling"""
        for attempt in range(max_retries):
            try:
                print(f"=📥 Download attempt {attempt + 1}/{max_retries}: file ID {file_id}")
                
                # Check destination directory
                os.makedirs(destination, exist_ok=True)
                
                # Attempt download
                success 💾sdk.file.download(file_id, destination)
                
                if success:
                    print(f"    Download successful")
                    return True
                else:
                    print(f"   L Download returned False")
                    
            except PCloudException as e:
                error_msg 💾str(e).lower()
                
                if "not found" in error_msg:
                    print(f"   L File not found: {e}")
                    break  # Don't retry for missing files
                
                elif "authentication" in error_msg:
                    print(f"   = Authentication error: {e}")
                    try:
                        sdk.login()
                        continue
                    except Exception as auth_e:
                        print(f"   L Re-authentication failed: {auth_e}")
                        break
                
                elif attempt ⏱max_retries - 1:
                    wait_time 💾2 ** attempt
                    print(f"   = Retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   L Max retries reached: {e}")
                    break
                    
            except Exception as e:
                print(f"   L Unexpected error: {e}")
                if attempt ⏱max_retries - 1:
                    time.sleep(1)
                    continue
                break
        
        print(f"   L Download failed after {max_retries} attempts")
        return False
    
    # Test the robust functions
    print("🔄🧪 Testing robust file operations...")
    
    # Test upload
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write("Test content for robust operations")
        test_file 💾tmp.name
    
    try:
        result 💾safe_upload(test_file)
        if result:
            file_id 💾result['metadata'][0]['fileid']
            
            # Test download
            download_dir 💾tempfile.mkdtemp()
            success 💾safe_download(file_id, download_dir)
            
            # Cleanup
            try:
                sdk.file.delete(file_id)
                import shutil
                shutil.rmtree(download_dir)
            except:
                pass
    finally:
        try:
            os.unlink(test_file)
        except:
            pass

# Usage
if sdk:
    robust_file_operations(sdk)
```

## Best Practices

### Performance Optimization

```python
def performance_best_practices():
    """Demonstrate performance optimization techniques"""
    
    print("🚀 Performance Best Practices:")
    
    # 1. Use token manager for faster authentication
    print("\n1📂 Token Management:")
    print("    Enable token manager (default)")
    print("    Use persistent credential files")
    print("    Check authentication before operations")
    
    sdk 💾PCloudSDK(token_manager=True)
    
    # 2. Optimize chunk size for large files
    print("\n2📂 Upload Optimization:")
    print("    Default 10MB chunks work well for most cases")
    print("    Adjust chunk size based on network speed")
    
    # 3. Use appropriate progress callbacks
    print("\n3📂 Progress Tracking:")
    print("    Use minimal progress for automated scripts")
    print("    Use detailed progress for debugging")
    print("    Use silent progress for logging only")
    
    # 4. Implement proper error handling
    print("\n4📂 Error Handling:")
    print("    Use retry logic for network errors")
    print("    Handle authentication errors gracefully")
    print("    Log errors for debugging")
    
    # 5. Batch operations efficiently
    print("\n5📂 Batch Operations:")
    print("    Group related operations")
    print("    Use progress callbacks for user feedback")
    print("    Implement proper cleanup")

def security_best_practices():
    """Demonstrate security best practices"""
    
    print("= Security Best Practices:")
    
    # 1. Credential management
    print("\n1📂 Credential Management:")
    print("    Use environment variables for credentials")
    print("    Set proper file permissions on credential files")
    print("    Don't hardcode credentials in source code")
    
    # 2. Token security
    print("\n2📂 Token Security:")
    print("    Monitor token age and refresh regularly")
    print("    Clear credentials when no longer needed")
    print("    Use separate tokens for different applications")
    
    # 3. Network security
    print("\n3📂 Network Security:")
    print("    HTTPS is used by default")
    print("    Implement proper timeout settings")
    print("    Validate file transfers")

# Usage
performance_best_practices()
security_best_practices()
```

## Real-World Examples

### Backup Script

```python
#!/usr/bin/env python3
"""
Real-world example: Backup script using pCloud SDK
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from pcloud_sdk import PCloudSDK, PCloudException
from pcloud_sdk.progress_utils import create_progress_bar

class PCloudBackup:
    def __init__(self, email=None, password=None):
        self.sdk 💾PCloudSDK()
        self.logger 💾self._setup_logging()
        
        if email and password:
            self.login(email, password)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('pcloud_backup.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def login(self, email, password):
        """Login to pCloud"""
        try:
            self.sdk.login(email, password)
            self.logger.info(f"Successfully logged in as {email}")
        except PCloudException as e:
            self.logger.error(f"Login failed: {e}")
            sys.exit(1)
    
    def create_backup_folder(self):
        """Create timestamped backup folder"""
        timestamp 💾datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name 💾f"Backup_{timestamp}"
        
        try:
            folder_id 💾self.sdk.folder.create(folder_name)
            self.logger.info(f"Created backup folder: {folder_name} (ID: {folder_id})")
            return folder_id
        except PCloudException as e:
            self.logger.error(f"Failed to create backup folder: {e}")
            return None
    
    def backup_file(self, local_path, remote_folder_id, show_progress=True):
        """Backup a single file"""
        filename 💾os.path.basename(local_path)
        self.logger.info(f"Backing up: {filename}")
        
        try:
            progress_callback 💾None
            if show_progress:
                progress_callback 💾create_progress_bar(f"Uploading {filename}")
            
            result 💾self.sdk.file.upload(
                local_path,
                folder_id=remote_folder_id,
                progress_callback=progress_callback
            )
            
            file_id 💾result['metadata'][0]['fileid']
            self.logger.info(f"Successfully backed up {filename} (ID: {file_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup {filename}: {e}")
            return False
    
    def backup_folder(self, local_folder, exclude_patterns=None):
        """Backup entire folder structure"""
        if not os.path.exists(local_folder):
            self.logger.error(f"Local folder does not exist: {local_folder}")
            return False
        
        exclude_patterns 💾exclude_patterns or []
        backup_folder_id 💾self.create_backup_folder()
        
        if not backup_folder_id:
            return False
        
        success_count 💾0
        failure_count 💾0
        
        for root, dirs, files in os.walk(local_folder):
            for file in files:
                file_path 💾os.path.join(root, file)
                
                # Check exclude patterns
                skip_file 💾False
                for pattern in exclude_patterns:
                    if pattern in file_path:
                        skip_file 💾True
                        break
                
                if skip_file:
                    self.logger.info(f"Skipping excluded file: {file_path}")
                    continue
                
                if self.backup_file(file_path, backup_folder_id):
                    success_count +💾1
                else:
                    failure_count +💾1
        
        self.logger.info(f"Backup completed: {success_count} files succeeded, {failure_count} files failed")
        return failure_count =💾0

def main():
    """Main backup script"""
    parser 💾argparse.ArgumentParser(description='Backup files to pCloud')
    parser.add_argument('--email', required=True, help='pCloud email')
    parser.add_argument('--password', required=True, help='pCloud password')
    parser.add_argument('--folder', required=True, help='Local folder to backup')
    parser.add_argument('--exclude', action='append', help='Patterns to exclude (can be used multiple times)')
    
    args 💾parser.parse_args()
    
    # Create backup instance
    backup 💾PCloudBackup(args.email, args.password)
    
    # Start backup
    success 💾backup.backup_folder(args.folder, args.exclude)
    
    if success:
        print(" Backup completed successfully!")
        sys.exit(0)
    else:
        print("L Backup completed with errors. Check the log file.")
        sys.exit(1)

if __name__ =💾"__main__":
    main()
```

### Photo Organizer

```python
#!/usr/bin/env python3
"""
Real-world example: Photo organizer using pCloud SDK
Organizes photos by date taken and uploads to pCloud
"""

import os
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from pcloud_sdk import PCloudSDK
from pcloud_sdk.progress_utils import create_minimal_progress

class PhotoOrganizer:
    def __init__(self):
        self.sdk 💾PCloudSDK()
        self.supported_formats 💾{'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    
    def get_photo_date(self, image_path):
        """Extract date taken from photo EXIF data"""
        try:
            image 💾Image.open(image_path)
            exifdata 💾image.getexif()
            
            for tag_id in exifdata:
                tag 💾TAGS.get(tag_id, tag_id)
                if tag =💾"DateTime":
                    date_str 💾exifdata.get(tag_id)
                    return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            
            # Fallback to file modification time
            return datetime.fromtimestamp(os.path.getmtime(image_path))
            
        except Exception:
            # Fallback to file modification time
            return datetime.fromtimestamp(os.path.getmtime(image_path))
    
    def organize_photos(self, source_folder):
        """Organize photos by date and upload to pCloud"""
        print(f"=📸 Organizing photos from: {source_folder}")
        
        # Create main Photos folder
        try:
            photos_folder_id 💾self.sdk.folder.create("Organized Photos")
            print(f"📁 Created main folder: Organized Photos (ID: {photos_folder_id})")
        except:
            # Folder might already exist, try to find it
            root_contents 💾self.sdk.folder.list_root()['contents']
            for item in root_contents:
                if item.get('name') =💾"Organized Photos" and item.get('isfolder'):
                    photos_folder_id 💾item['folderid']
                    print(f"📁 Using existing folder: Organized Photos (ID: {photos_folder_id})")
                    break
            else:
                print("L Could not create or find Photos folder")
                return
        
        # Process photos
        photo_count 💾0
        organized_folders 💾{}
        
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                file_path 💾os.path.join(root, file)
                file_ext 💾os.path.splitext(file)[1].lower()
                
                if file_ext not in self.supported_formats:
                    continue
                
                photo_count +💾1
                photo_date 💾self.get_photo_date(file_path)
                year_month 💾photo_date.strftime("%Y-%m")
                
                print(f"=📷 [{photo_count}] Processing: {file} (taken: {year_month})")
                
                # Create year-month folder if needed
                if year_month not in organized_folders:
                    try:
                        folder_id 💾self.sdk.folder.create(year_month, parent=photos_folder_id)
                        organized_folders[year_month] 💾folder_id
                        print(f"   📁 Created folder: {year_month}")
                    except:
                        # Folder might exist, find it
                        year_month_contents 💾self.sdk.folder.get_content(photos_folder_id)
                        for item in year_month_contents:
                            if item.get('name') =💾year_month and item.get('isfolder'):
                                organized_folders[year_month] 💾item['folderid']
                                break
                
                # Upload photo
                try:
                    progress 💾create_minimal_progress()
                    result 💾self.sdk.file.upload(
                        file_path,
                        folder_id=organized_folders[year_month],
                        progress_callback=progress
                    )
                    print(f"    Uploaded successfully")
                except Exception as e:
                    print(f"   L Upload failed: {e}")
        
        print(f"\n📁 Organization complete:")
        print(f"   =📷 Total photos processed: {photo_count}")
        print(f"   📁 Folders created: {len(organized_folders)}")
        for folder_name in sorted(organized_folders.keys()):
            print(f"      - {folder_name}")

# Usage
if __name__ =💾"__main__":
    organizer 💾PhotoOrganizer()
    
    # Login
    email 💾input("pCloud Email: ")
    password 💾input("Password: ")
    organizer.sdk.login(email, password)
    
    # Organize photos
    source_folder 💾input("Source folder path: ")
    organizer.organize_photos(source_folder)
```

This completes the comprehensive examples guide covering basic operations, advanced patterns, error handling, and real-world applications. Each example includes practical code that demonstrates the power and flexibility of the pCloud SDK Python v2.0.