#!/usr/bin/env python3
"""
pCloud SDK Progress Tracking Examples
====================================

This example demonstrates all the different progress tracking options available
in the pCloud SDK. Progress tracking is essential for providing user feedback
during file transfers, especially for large files.

The SDK provides 4 built-in progress trackers:
1. SimpleProgressBar - Clean progress bar with speed and ETA
2. DetailedProgress - Detailed logging with checkpoints
3. MinimalProgress - Just milestone percentages
4. SilentProgress - Silent with CSV logging

This example shows:
- All 4 built-in progress trackers in action
- Custom progress callbacks
- Progress tracking for both upload and download
- Silent logging and CSV export
- Performance monitoring
"""

import csv
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from pcloud_sdk import PCloudException, PCloudSDK
from pcloud_sdk.progress_utils import (
    DetailedProgress,
    MinimalProgress,
    SilentProgress,
    SimpleProgressBar,
    create_detailed_progress,
    create_minimal_progress,
    create_progress_bar,
    create_silent_progress,
)


class CustomProgressTracker:
    """Custom progress tracker with advanced statistics"""

    def __init__(self, name: str = "Custom Progress"):
        self.name = name
        self.start_time = None
        self.last_update = 0
        self.speed_samples = []
        self.max_speed = 0
        self.min_speed = float("inf")

    def __call__(
        self,
        bytes_transferred: int,
        total_bytes: int,
        percentage: float,
        speed: float,
        **kwargs,
    ):
        """Advanced progress tracking with statistics"""

        if self.start_time is None:
            self.start_time = time.time()
            operation = kwargs.get("operation", "transfer")
            filename = kwargs.get("filename", "file")
            print(f"\n📊 {self.name} - Starting {operation}: {filename}")
            print(f"   📏 Size: {total_bytes:,} bytes ({total_bytes/1024/1024:.1f} MB)")

        # Update speed statistics
        if speed > 0:
            self.speed_samples.append(speed)
            self.max_speed = max(self.max_speed, speed)
            if speed < self.min_speed:
                self.min_speed = speed

        # Throttle updates
        now = time.time()
        if now - self.last_update < 0.5 and percentage < 100:
            return
        self.last_update = now

        # Calculate statistics
        elapsed = now - self.start_time
        avg_speed = (
            sum(self.speed_samples) / len(self.speed_samples)
            if self.speed_samples
            else 0
        )

        # Display progress with statistics
        status = kwargs.get("status", "progress")

        if status == "completed":
            print(f"\n✅ {self.name} - Transfer completed!")
            print(f"   ⏱️  Total time: {elapsed:.1f}s")
            print(f"   📈 Average speed: {avg_speed/1024/1024:.1f} MB/s")
            print(f"   🚀 Max speed: {self.max_speed/1024/1024:.1f} MB/s")
            print(f"   🐌 Min speed: {self.min_speed/1024/1024:.1f} MB/s")
            print(f"   📊 Speed samples: {len(self.speed_samples)}")
        elif status == "error":
            error = kwargs.get("error", "Unknown error")
            print(f"\n❌ {self.name} - Error: {error}")
        else:
            # Regular progress update
            bar_width = 30
            filled = int(bar_width * percentage / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(
                f"\r   [{bar}] {percentage:5.1f}% "
                f"({bytes_transferred:,}/{total_bytes:,}) "
                f"📶 {speed/1024/1024:5.1f}MB/s "
                f"📊 Avg:{avg_speed/1024/1024:4.1f}MB/s",
                end="",
                flush=True,
            )


def create_test_files(temp_dir: str) -> List[str]:
    """Create test files of different sizes"""
    test_files = []

    # Small text file (1KB)
    small_file = os.path.join(temp_dir, "small_test.txt")
    with open(small_file, "w") as f:
        f.write("Small test file content. " * 50)  # ~1KB
    test_files.append(small_file)

    # Medium text file (100KB)
    medium_file = os.path.join(temp_dir, "medium_test.txt")
    with open(medium_file, "w") as f:
        content = "Medium test file content. " * 4000  # ~100KB
        f.write(content)
    test_files.append(medium_file)

    # Large binary file (1MB)
    large_file = os.path.join(temp_dir, "large_test.bin")
    with open(large_file, "wb") as f:
        # Write 1MB of random-like data
        for i in range(1024):
            chunk = bytes([(i + j) % 256 for j in range(1024)])
            f.write(chunk)
    test_files.append(large_file)

    return test_files


def demonstrate_simple_progress_bar(sdk: PCloudSDK, test_file: str):
    """Demonstrate SimpleProgressBar"""
    print("\n" + "=" * 60)
    print("1️⃣ SIMPLE PROGRESS BAR DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • Clean visual progress bar")
    print("   • Real-time speed display")
    print("   • ETA calculation")
    print("   • File size information")

    # Create progress bar
    progress_bar = create_progress_bar(
        "Simple Upload", width=40, show_speed=True, show_eta=True
    )

    try:
        print(f"\n📤 Uploading {os.path.basename(test_file)} with SimpleProgressBar...")
        result = sdk.file.upload(test_file, folder_id=0, progress_callback=progress_bar)
        file_id = result.get("metadata", [{}])[0].get("fileid")

        if file_id:
            print(f"\n📥 Downloading file with SimpleProgressBar...")
            download_dir = tempfile.mkdtemp()
            progress_bar_dl = create_progress_bar("Simple Download", width=40)
            sdk.file.download(
                file_id, destination=download_dir, progress_callback=progress_bar_dl
            )

            # Cleanup
            sdk.file.delete(file_id)
            import shutil

            shutil.rmtree(download_dir)

    except PCloudException as e:
        print(f"❌ Error: {e}")


def demonstrate_detailed_progress(sdk: PCloudSDK, test_file: str):
    """Demonstrate DetailedProgress"""
    print("\n" + "=" * 60)
    print("2️⃣ DETAILED PROGRESS DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • Comprehensive logging")
    print("   • Checkpoint recording")
    print("   • File logging option")
    print("   • Performance statistics")

    # Create detailed progress with log file
    log_file = "detailed_progress.log"
    detailed_progress = create_detailed_progress(log_file=log_file)

    try:
        print(f"\n📤 Uploading {os.path.basename(test_file)} with DetailedProgress...")
        result = sdk.file.upload(
            test_file, folder_id=0, progress_callback=detailed_progress
        )
        file_id = result.get("metadata", [{}])[0].get("fileid")

        if file_id:
            # Cleanup
            sdk.file.delete(file_id)

        print(f"\n📄 Progress log saved to: {log_file}")
        if os.path.exists(log_file):
            print("📄 Log file contents (last 5 lines):")
            with open(log_file, "r") as f:
                lines = f.readlines()
                for line in lines[-5:]:
                    print(f"   {line.strip()}")

    except PCloudException as e:
        print(f"❌ Error: {e}")


def demonstrate_minimal_progress(sdk: PCloudSDK, test_file: str):
    """Demonstrate MinimalProgress"""
    print("\n" + "=" * 60)
    print("3️⃣ MINIMAL PROGRESS DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • Milestone notifications only")
    print("   • Minimal output")
    print("   • Perfect for automation")
    print("   • Clean and simple")

    # Create minimal progress
    minimal_progress = create_minimal_progress()

    try:
        print(f"\n📤 Uploading {os.path.basename(test_file)} with MinimalProgress...")
        result = sdk.file.upload(
            test_file, folder_id=0, progress_callback=minimal_progress
        )
        file_id = result.get("metadata", [{}])[0].get("fileid")

        if file_id:
            # Cleanup
            sdk.file.delete(file_id)

    except PCloudException as e:
        print(f"❌ Error: {e}")


def demonstrate_silent_progress(sdk: PCloudSDK, test_file: str):
    """Demonstrate SilentProgress"""
    print("\n" + "=" * 60)
    print("4️⃣ SILENT PROGRESS DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • No console output")
    print("   • CSV logging")
    print("   • Perfect for batch operations")
    print("   • Data analysis ready")

    # Create silent progress with CSV logging
    csv_file = "silent_progress.csv"
    silent_progress = create_silent_progress(csv_file)

    try:
        print(f"\n📤 Uploading {os.path.basename(test_file)} with SilentProgress...")
        print("   (No progress output - check CSV file)")

        result = sdk.file.upload(
            test_file, folder_id=0, progress_callback=silent_progress
        )
        file_id = result.get("metadata", [{}])[0].get("fileid")

        if file_id:
            # Cleanup
            sdk.file.delete(file_id)

        print(f"\n📊 Progress data saved to: {csv_file}")
        if os.path.exists(csv_file):
            print("📊 CSV file contents (first 5 rows):")
            with open(csv_file, "r") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i < 5:
                        print(f"   {','.join(row)}")
                    else:
                        break

    except PCloudException as e:
        print(f"❌ Error: {e}")


def demonstrate_custom_progress(sdk: PCloudSDK, test_file: str):
    """Demonstrate custom progress tracker"""
    print("\n" + "=" * 60)
    print("5️⃣ CUSTOM PROGRESS DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • Custom progress logic")
    print("   • Advanced statistics")
    print("   • Speed analysis")
    print("   • Fully customizable")

    # Create custom progress tracker
    custom_progress = CustomProgressTracker("Advanced Tracker")

    try:
        print(
            f"\n📤 Uploading {os.path.basename(test_file)} with CustomProgressTracker..."
        )
        result = sdk.file.upload(
            test_file, folder_id=0, progress_callback=custom_progress
        )
        file_id = result.get("metadata", [{}])[0].get("fileid")

        if file_id:
            # Cleanup
            sdk.file.delete(file_id)

    except PCloudException as e:
        print(f"❌ Error: {e}")


def batch_progress_demonstration(sdk: PCloudSDK, test_files: List[str]):
    """Demonstrate progress tracking for batch operations"""
    print("\n" + "=" * 60)
    print("6️⃣ BATCH PROGRESS DEMONSTRATION")
    print("=" * 60)

    print("📋 Features:")
    print("   • Multiple file progress tracking")
    print("   • Batch operation statistics")
    print("   • Overall progress calculation")

    # Batch progress tracker
    class BatchProgressTracker:
        def __init__(self, total_files: int):
            self.total_files = total_files
            self.current_file = 0
            self.completed_files = 0

        def create_file_callback(self, filename: str):
            def callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
                status = kwargs.get("status", "progress")
                if status == "starting":
                    self.current_file += 1
                    print(
                        f"\n📁 File {self.current_file}/{self.total_files}: {filename}"
                    )
                elif status == "completed":
                    self.completed_files += 1
                    overall_progress = (self.completed_files / self.total_files) * 100
                    print(f"   ✅ Completed ({overall_progress:.1f}% overall)")
                elif percentage % 25 == 0 and percentage > 0:
                    print(f"   📊 {percentage:.0f}%...", end="", flush=True)

            return callback

    batch_tracker = BatchProgressTracker(len(test_files))
    uploaded_files = []

    try:
        print(f"\n📤 Batch uploading {len(test_files)} files...")

        for test_file in test_files:
            filename = os.path.basename(test_file)
            callback = batch_tracker.create_file_callback(filename)

            result = sdk.file.upload(test_file, folder_id=0, progress_callback=callback)
            file_id = result.get("metadata", [{}])[0].get("fileid")
            if file_id:
                uploaded_files.append(file_id)

        print(f"\n🎉 Batch upload completed: {len(uploaded_files)} files uploaded")

        # Cleanup
        print("\n🧹 Cleaning up uploaded files...")
        for file_id in uploaded_files:
            try:
                sdk.file.delete(file_id)
            except:
                pass
        print("✅ Cleanup completed")

    except PCloudException as e:
        print(f"❌ Error during batch operation: {e}")


def analyze_csv_logs():
    """Analyze CSV logs from silent progress"""
    print("\n" + "=" * 60)
    print("7️⃣ CSV LOG ANALYSIS")
    print("=" * 60)

    csv_file = "silent_progress.csv"
    if not os.path.exists(csv_file):
        print(f"❌ CSV file {csv_file} not found. Run silent progress demo first.")
        return

    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("📊 CSV file is empty")
            return

        print(f"📊 Analyzing {len(rows)} progress records...")

        # Calculate statistics
        speeds = [float(row["speed_mbps"]) for row in rows if row["speed_mbps"]]
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            max_speed = max(speeds)
            min_speed = min(speeds)

            print(f"   📈 Average speed: {avg_speed:.2f} MB/s")
            print(f"   🚀 Maximum speed: {max_speed:.2f} MB/s")
            print(f"   🐌 Minimum speed: {min_speed:.2f} MB/s")

        # Show transfer timeline
        print(f"   ⏱️  Transfer timeline:")
        for i, row in enumerate(rows[-5:]):  # Last 5 records
            timestamp = row["timestamp"].split("T")[1][:8]  # Extract time
            print(f"      {timestamp}: {row['percentage']}% - {row['speed_mbps']} MB/s")

    except Exception as e:
        print(f"❌ Error analyzing CSV: {e}")


def main():
    """Main demonstration function"""
    print("🚀 pCloud SDK Progress Tracking Examples")
    print("=" * 45)

    # Setup
    print("\n🔧 Setup...")

    # Get credentials
    email = os.environ.get("PCLOUD_EMAIL")
    password = os.environ.get("PCLOUD_PASSWORD")

    if not email or not password:
        print("📧 Environment variables not found")
        email = input("Enter pCloud email: ").strip()
        password = input("Enter pCloud password: ").strip()

        if not email or not password:
            print("❌ Email and password required")
            return

    # Initialize SDK
    try:
        sdk = PCloudSDK()
        sdk.login(email, password)
        print("✅ Connected to pCloud")

        # Create test files
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Creating test files in {temp_dir}...")
        test_files = create_test_files(temp_dir)

        for i, test_file in enumerate(test_files, 1):
            size = os.path.getsize(test_file)
            print(f"   {i}. {os.path.basename(test_file)} ({size:,} bytes)")

        # Run demonstrations
        print("\n🎬 Starting progress tracking demonstrations...")

        # Use medium file for most demos (good balance of speed and visibility)
        demo_file = test_files[1]  # medium_test.txt

        demonstrate_simple_progress_bar(sdk, demo_file)
        demonstrate_detailed_progress(sdk, demo_file)
        demonstrate_minimal_progress(sdk, demo_file)
        demonstrate_silent_progress(sdk, demo_file)
        demonstrate_custom_progress(sdk, demo_file)

        # Use all files for batch demo
        batch_progress_demonstration(sdk, test_files)

        # Analyze logs
        analyze_csv_logs()

        print("\n🎉 All progress tracking demonstrations completed!")
        print("\n💡 Key takeaways:")
        print("   • SimpleProgressBar: Best for interactive applications")
        print("   • DetailedProgress: Best for debugging and detailed logging")
        print("   • MinimalProgress: Best for scripts and automation")
        print("   • SilentProgress: Best for batch operations and analysis")
        print("   • Custom callbacks: Best for specialized requirements")

    except PCloudException as e:
        print(f"❌ pCloud error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Cleanup
        try:
            import shutil

            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temporary files")
        except:
            pass


if __name__ == "__main__":
    main()
