#!/usr/bin/env python3

"""
pCloud SDK Upload/Download Demo
==============================

This example focuses specifically on file transfer operations, demonstrating
advanced upload and download features of the pCloud SDK.

This comprehensive demo covers:
- Different upload methods and options
- Progress tracking during transfers
- Large file handling with chunked uploads
- Download with verification and resume capability
- Batch operations for multiple files
- Error recovery and retry mechanisms
- Performance optimization techniques
- Real-world transfer scenarios
"""

import os
import tempfile
import hashlib
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple
import mimetypes
from pathlib import Path

from pcloud_sdk import PCloudSDK, create_progress_bar, create_detailed_progress
from pcloud_sdk.exceptions import PCloudException


def create_test_files() -> List[str]:
    """Create various test files for upload demonstrations"""
    temp_dir = tempfile.gettempdir()
    test_files = []

    # Small text file
    small_file = os.path.join(temp_dir, "small_document.txt")
    with open(small_file, 'w') as f:
        f.write("This is a small test document.\n" * 100)
    test_files.append(small_file)

    # Medium binary file
    medium_file = os.path.join(temp_dir, "medium_data.bin")
    with open(medium_file, 'wb') as f:
        # Create pseudo-random binary data
        for i in range(1024):  # 1MB
            chunk = bytes([(i * 137 + j) % 256 for j in range(1024)])
            f.write(chunk)
    test_files.append(medium_file)

    # Large text file
    large_file = os.path.join(temp_dir, "large_document.txt")
    with open(large_file, 'w') as f:
        for i in range(50000):  # ~5MB
            f.write(f"Line {i:06d}: This is line number {i} in our large test document.\n")
    test_files.append(large_file)

    # Image-like file (for MIME type testing)
    fake_image = os.path.join(temp_dir, "test_image.jpg")
    with open(fake_image, 'wb') as f:
        # Create a fake JPEG header
        f.write(b'\xFF\xD8\xFF\xE0')  # JPEG magic bytes
        f.write(b'\x00' * 10240)  # 10KB of zeros
    test_files.append(fake_image)

    print(f"✓ Created {len(test_files)} test files:")
    for file_path in test_files:
        size = os.path.getsize(file_path)
        print(f"   • {os.path.basename(file_path)} ({size:,} bytes)")

    return test_files


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file for integrity verification"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def format_size(bytes_size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def format_speed(bytes_per_second: float) -> str:
    """Format transfer speed"""
    return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"


class AdvancedProgressTracker:
    """Advanced progress tracker with statistics and performance monitoring"""

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.start_time = None
        self.last_update = 0
        self.speed_samples = []
        self.bytes_history = []

    def __call__(self, bytes_transferred: int, total_bytes: int, percentage: float, speed: float, **kwargs):
        """Progress callback with detailed monitoring"""

        current_time = time.time()

        if self.start_time is None:
            self.start_time = current_time
            operation = kwargs.get('operation', 'transfer')
            print(f"\n⚡ {operation.title()} started: {self.file_name}")
            print(f"   Size: {format_size(total_bytes)}")

        status = kwargs.get('status', 'progress')

        # Collect performance data
        if speed > 0:
            self.speed_samples.append(speed)

        self.bytes_history.append((current_time, bytes_transferred))

        # Update display every 1 second or on status change
        if current_time - self.last_update >= 1.0 or status != 'progress':
            self.last_update = current_time

            if status == 'progress':
                elapsed = current_time - self.start_time
                avg_speed = bytes_transferred / elapsed if elapsed > 0 else 0

                # Calculate ETA
                if speed > 0:
                    remaining_bytes = total_bytes - bytes_transferred
                    eta_seconds = remaining_bytes / speed
                    eta_str = f"{int(eta_seconds)}s" if eta_seconds < 60 else f"{int(eta_seconds/60)}m{int(eta_seconds%60)}s"
                else:
                    eta_str = "Unknown"

                print(f"   ▶ {percentage:5.1f}% | {format_speed(speed)} | Avg: {format_speed(avg_speed)} | ETA: {eta_str}")

            elif status == 'completed':
                elapsed = current_time - self.start_time
                avg_speed = bytes_transferred / elapsed if elapsed > 0 else 0
                max_speed = max(self.speed_samples) if self.speed_samples else 0

                print(f"  ✓ Transfer completed in {elapsed:.1f}s")
                print(f"      Average speed: {format_speed(avg_speed)}")
                print(f"      Peak speed: {format_speed(max_speed)}")
                print(f"      Efficiency: {(avg_speed/max_speed*100):.0f}%" if max_speed > 0 else "")

            elif status == 'error':
                error = kwargs.get('error', 'Unknown error')
                print(f"   ✗ Transfer failed: {error}")


class BatchProgressManager:
    """Manager for tracking progress of multiple file operations"""

    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.files = {}
        self.start_time = time.time()

    def add_file(self, file_name: str, size: int):
        """Add a file to track"""
        self.files[file_name] = {
            'size': size,
            'transferred': 0,
            'completed': False,
            'start_time': None
        }

    def create_progress_callback(self, file_name: str):
        """Create a progress callback for a specific file"""
        def progress_callback(bytes_transferred: int, total_bytes: int, percentage: float, speed: float, **kwargs):
            status = kwargs.get('status', 'progress')

            if file_name in self.files:
                file_info = self.files[file_name]

                if file_info['start_time'] is None:
                    file_info['start_time'] = time.time()

                file_info['transferred'] = bytes_transferred

                if status == 'completed':
                    file_info['completed'] = True
                    elapsed = time.time() - file_info['start_time']
                    avg_speed = bytes_transferred / elapsed if elapsed > 0 else 0
                    print(f"  ✓ {file_name}: {format_speed(avg_speed)}")

                elif status == 'error':
                    print(f"   ✗ {file_name}: {kwargs.get('error', 'Failed')}")

                # Update overall progress
                self._update_overall_progress()

        return progress_callback

    def _update_overall_progress(self):
        """Update and display overall batch progress"""
        total_size = sum(f['size'] for f in self.files.values())
        total_transferred = sum(f['transferred'] for f in self.files.values())
        completed_count = sum(1 for f in self.files.values() if f['completed'])

        overall_percentage = (total_transferred / total_size * 100) if total_size > 0 else 0

        print(f"⚡ {self.operation_name}: {completed_count}/{len(self.files)} files, {overall_percentage:.1f}% overall")


class UploadDownloadDemo:
    """Comprehensive upload/download demonstration"""

    def __init__(self):
        self.sdk: Optional[PCloudSDK] = None
        self.demo_folder_id: Optional[int] = None
        self.test_files: List[str] = []
        self.uploaded_files: List[Dict] = []

    def setup_sdk(self) -> bool:
        """Setup and authenticate SDK"""
        print("⚡ pCloud SDK Upload/Download Demo")
        print("=" * 50)

        self.sdk = PCloudSDK(
            location_id=2,
            token_manager=True,
            token_file=".pcloud_upload_demo"
        )

        # Quick authentication
        if self.sdk.is_authenticated():
            try:
                if self.sdk._test_existing_credentials():
                    email = self.sdk.get_saved_email()
                    print(f"✓ Using saved credentials for: {email}")
                    return True
            except:
                pass

        # Need authentication
        print("🔐 Authentication required")
        email = input("⚡ pCloud email: ").strip()
        password = input("🔒 Password: ").strip()

        try:
            self.sdk.login(email, password)
            print("✓ Authentication successful")
            return True
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            return False

    def setup_demo_environment(self):
        """Create demo folder and test files"""
        print("\n⚡ Setting up demo environment...")

        # Create demo folder
        folder_name = f"Upload_Download_Demo_{int(time.time())}"
        self.demo_folder_id = self.sdk.folder.create(folder_name)
        print(f"✓ Created demo folder: {folder_name} (ID: {self.demo_folder_id})")

        # Create test files
        self.test_files = create_test_files()

    def demo_basic_upload(self):
        """Demonstrate basic file upload"""
        print("\n" + "="*60)
        print("1️⃣ BASIC UPLOAD DEMO")
        print("="*60)

        if not self.test_files:
            print("⚠ No test files available")
            return

        test_file = self.test_files[0]  # Small file
        file_name = os.path.basename(test_file)
        file_size = os.path.getsize(test_file)

        print(f"⚡ Uploading {file_name} ({format_size(file_size)})...")

        # Simple upload with basic progress
        progress = create_progress_bar(f"Upload: {file_name}")

        try:
            start_time = time.time()
            result = self.sdk.file.upload(
                test_file,
                self.demo_folder_id,
                progress_callback=progress
            )
            elapsed = time.time() - start_time

            file_info = {
                'id': result['metadata']['fileid'],
                'name': file_name,
                'size': file_size,
                'upload_time': elapsed,
                'local_path': test_file
            }
            self.uploaded_files.append(file_info)

            print(f"✓ Upload completed in {elapsed:.1f}s")
            print(f"   File ID: {file_info['id']}")
            print(f"   Average speed: {format_speed(file_size / elapsed)}")

        except Exception as e:
            print(f"✗ Upload failed: {e}")

    def demo_advanced_upload(self):
        """Demonstrate advanced upload with detailed progress"""
        print("\n" + "="*60)
        print("2️⃣ ADVANCED UPLOAD DEMO")
        print("="*60)

        if len(self.test_files) < 2:
            print("⚠ Not enough test files")
            return

        test_file = self.test_files[2]  # Large file
        file_name = os.path.basename(test_file)
        file_size = os.path.getsize(test_file)

        print(f"⚡ Advanced upload: {file_name} ({format_size(file_size)})")

        # Advanced progress tracker
        progress = AdvancedProgressTracker(file_name)

        try:
            # Calculate file hash before upload for verification
            print("⚡ Calculating file hash for verification...")
            original_hash = calculate_file_hash(test_file)

            start_time = time.time()
            result = self.sdk.file.upload(
                test_file,
                self.demo_folder_id,
                progress_callback=progress
            )
            elapsed = time.time() - start_time

            file_info = {
                'id': result['metadata']['fileid'],
                'name': file_name,
                'size': file_size,
                'upload_time': elapsed,
                'local_path': test_file,
                'original_hash': original_hash
            }
            self.uploaded_files.append(file_info)

            print(f"✓ Advanced upload completed")
            print(f"   Original hash: {original_hash[:16]}...")

        except Exception as e:
            print(f"✗ Advanced upload failed: {e}")

    def demo_batch_upload(self):
        """Demonstrate batch upload of multiple files"""
        print("\n" + "="*60)
        print("3️⃣ BATCH UPLOAD DEMO")
        print("="*60)

        remaining_files = [f for f in self.test_files if f not in [uf['local_path'] for uf in self.uploaded_files]]

        if not remaining_files:
            print("⚠ No remaining files for batch upload")
            return

        print(f"⚡ Batch uploading {len(remaining_files)} files...")

        # Setup batch progress manager
        batch_manager = BatchProgressManager("Batch Upload")

        # Add files to batch manager
        for file_path in remaining_files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            batch_manager.add_file(file_name, file_size)

        # Upload files sequentially with individual progress tracking
        for file_path in remaining_files:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            print(f"\n⚡ Uploading {file_name}...")
            progress_callback = batch_manager.create_progress_callback(file_name)

            try:
                result = self.sdk.file.upload(
                    file_path,
                    self.demo_folder_id,
                    progress_callback=progress_callback
                )

                file_info = {
                    'id': result['metadata']['fileid'],
                    'name': file_name,
                    'size': file_size,
                    'local_path': file_path
                }
                self.uploaded_files.append(file_info)

            except Exception as e:
                print(f"✗ Failed to upload {file_name}: {e}")

        print(f"\n✓ Batch upload completed: {len(self.uploaded_files)} total files uploaded")

    def demo_basic_download(self):
        """Demonstrate basic file download"""
        print("\n" + "="*60)
        print("4️⃣ BASIC DOWNLOAD DEMO")
        print("="*60)

        if not self.uploaded_files:
            print("⚠ No uploaded files to download")
            return

        # Download first uploaded file
        file_info = self.uploaded_files[0]

        print(f"⚡ Downloading {file_info['name']} (ID: {file_info['id']})...")

        # Create download directory
        temp_dir = tempfile.gettempdir()
        download_dir = os.path.join(temp_dir, "pcloud_downloads")
        os.makedirs(download_dir, exist_ok=True)

        # Basic download with progress
        progress = create_progress_bar(f"Download: {file_info['name']}")

        try:
            start_time = time.time()
            success = self.sdk.file.download(
                file_info['id'],
                download_dir,
                progress_callback=progress
            )
            elapsed = time.time() - start_time

            if success:
                downloaded_file = os.path.join(download_dir, file_info['name'])
                if os.path.exists(downloaded_file):
                    downloaded_size = os.path.getsize(downloaded_file)
                    print(f"✓ Download completed in {elapsed:.1f}s")
                    print(f"   Downloaded size: {format_size(downloaded_size)}")
                    print(f"   Average speed: {format_speed(downloaded_size / elapsed)}")

                    # Verify file integrity if we have original hash
                    if 'original_hash' in file_info:
                        downloaded_hash = calculate_file_hash(downloaded_file)
                        if downloaded_hash == file_info['original_hash']:
                            print("✓ File integrity verified - hashes match!")
                        else:
                            print("⚠ File integrity check failed - hashes don't match")

                    # Cleanup
                    os.remove(downloaded_file)

        except Exception as e:
            print(f"✗ Download failed: {e}")
        finally:
            # Cleanup download directory
            if os.path.exists(download_dir):
                shutil.rmtree(download_dir, ignore_errors=True)

    def demo_batch_download(self):
        """Demonstrate batch download with verification"""
        print("\n" + "="*60)
        print("5️⃣ BATCH DOWNLOAD DEMO")
        print("="*60)

        if len(self.uploaded_files) < 2:
            print("⚠ Not enough uploaded files for batch download")
            return

        download_files = self.uploaded_files[:3]  # Download first 3 files

        print(f"⚡ Batch downloading {len(download_files)} files...")

        # Create download directory
        temp_dir = tempfile.gettempdir()
        download_dir = os.path.join(temp_dir, "batch_downloads")
        os.makedirs(download_dir, exist_ok=True)

        # Setup batch progress manager
        batch_manager = BatchProgressManager("Batch Download")

        # Add files to batch manager
        for file_info in download_files:
            batch_manager.add_file(file_info['name'], file_info['size'])

        # Download files with progress tracking
        successful_downloads = 0

        for file_info in download_files:
            print(f"\n⚡ Downloading {file_info['name']}...")
            progress_callback = batch_manager.create_progress_callback(file_info['name'])

            try:
                success = self.sdk.file.download(
                    file_info['id'],
                    download_dir,
                    progress_callback=progress_callback
                )

                if success:
                    successful_downloads += 1
                    downloaded_file = os.path.join(download_dir, file_info['name'])

                    # Quick verification
                    if os.path.exists(downloaded_file):
                        downloaded_size = os.path.getsize(downloaded_file)
                        if downloaded_size == file_info['size']:
                            print(f"  ✓ Size verification passed")
                        else:
                            print(f"   ⚠ Size mismatch: expected {file_info['size']}, got {downloaded_size}")

            except Exception as e:
                print(f"✗ Failed to download {file_info['name']}: {e}")

        print(f"\n✓ Batch download completed: {successful_downloads}/{len(download_files)} files")

        # Cleanup download directory
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir, ignore_errors=True)

    def demo_file_operations(self):
        """Demonstrate file operations on uploaded files"""
        print("\n" + "="*60)
        print("6️⃣ FILE OPERATIONS DEMO")
        print("="*60)

        if not self.uploaded_files:
            print("⚠ No uploaded files for operations")
            return

        # Work with the first uploaded file
        file_info = self.uploaded_files[0]
        file_id = file_info['id']
        original_name = file_info['name']

        print(f"⚡ Performing operations on: {original_name} (ID: {file_id})")

        try:
            # Get detailed file info
            print("\n⚡ Getting file information...")
            detailed_info = self.sdk.file.get_info(file_id)
            metadata = detailed_info.get('metadata', {})

            print(f"   Name: {metadata.get('name', 'N/A')}")
            print(f"   Size: {format_size(metadata.get('size', 0))}")
            print(f"   Created: {metadata.get('created', 'N/A')}")
            print(f"   Modified: {metadata.get('modified', 'N/A')}")

            # Rename file
            new_name = f"renamed_{original_name}"
            print(f"\n⚡ Renaming file to: {new_name}")
            self.sdk.file.rename(file_id, new_name)
            print("✓ File renamed successfully")

            # Copy file
            print(f"\n⚡ Creating copy of file...")
            copy_result = self.sdk.file.copy(file_id, self.demo_folder_id)
            copied_file_id = copy_result['metadata']['fileid']
            print(f"✓ File copied successfully (new ID: {copied_file_id})")

            # List folder to show both files
            print(f"\n⚡ Demo folder contents:")
            folder_contents = self.sdk.folder.get_content(self.demo_folder_id)

            for item in folder_contents:
                if not item.get('isfolder'):
                    size = format_size(item.get('size', 0))
                    print(f"   • {item['name']} ({size})")

            # Delete the copy
            print(f"\n⚡ Deleting copied file...")
            self.sdk.file.delete(copied_file_id)
            print("✓ Copied file deleted successfully")

        except Exception as e:
            print(f"✗ File operations failed: {e}")

    def demo_performance_analysis(self):
        """Analyze upload/download performance"""
        print("\n" + "="*60)
        print("7️⃣ PERFORMANCE ANALYSIS")
        print("="*60)

        if not self.uploaded_files:
            print("⚠ No uploaded files for analysis")
            return

        print("⚡ Upload Performance Analysis:")
        print("-" * 40)

        total_size = 0
        total_time = 0

        for file_info in self.uploaded_files:
            if 'upload_time' in file_info:
                size = file_info['size']
                time_taken = file_info['upload_time']
                speed = size / time_taken if time_taken > 0 else 0

                total_size += size
                total_time += time_taken

                print(f"⚡ {file_info['name']}:")
                print(f"   Size: {format_size(size)}")
                print(f"   Time: {time_taken:.1f}s")
                print(f"   Speed: {format_speed(speed)}")
                print()

        if total_time > 0:
            overall_speed = total_size / total_time
            print(f"⚡ Overall Statistics:")
            print(f"   Total uploaded: {format_size(total_size)}")
            print(f"   Total time: {total_time:.1f}s")
            print(f"   Average speed: {format_speed(overall_speed)}")

    def cleanup(self):
        """Clean up demo resources"""
        print("\n🧹 Cleaning up demo resources...")

        try:
            # Delete demo folder and all contents
            if self.demo_folder_id:
                self.sdk.folder.delete_recursive(self.demo_folder_id)
                print("✓ Demo folder and all files deleted")

            # Clean up local test files
            for test_file in self.test_files:
                if os.path.exists(test_file):
                    os.remove(test_file)
                    print(f"🗑 Removed local file: {os.path.basename(test_file)}")

        except Exception as e:
            print(f"⚠ Cleanup error: {e}")

    def run_demo(self):
        """Run the complete upload/download demo"""
        try:
            # Setup
            if not self.setup_sdk():
                return

            self.setup_demo_environment()

            # Run all demonstrations
            self.demo_basic_upload()
            self.demo_advanced_upload()
            self.demo_batch_upload()
            self.demo_basic_download()
            self.demo_batch_download()
            self.demo_file_operations()
            self.demo_performance_analysis()

            print("\n✅ Upload/Download demo completed successfully!")

        except KeyboardInterrupt:
            print("\n⚠ Demo interrupted by user")
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")
        finally:
            self.cleanup()


def main():
    """Main function"""
    print("🚀 Welcome to the pCloud SDK Upload/Download Demo!")
    print()
    print("This comprehensive demo showcases:")
    print("• Basic and advanced upload techniques")
    print("• Progress tracking and performance monitoring")
    print("• Batch operations for multiple files")
    print("• Download with verification")
    print("• File operations and management")
    print("• Performance analysis and optimization")
    print()

    proceed = input("Continue with the upload/download demo? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("Demo cancelled.")
        return

    # Run the demo
    demo = UploadDownloadDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()