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

import os
import time
import tempfile
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any

from pcloud_sdk import PCloudSDK
from pcloud_sdk import (
    create_progress_bar, create_detailed_progress, 
    create_minimal_progress, create_silent_progress,
    SimpleProgressBar, DetailedProgress, MinimalProgress, SilentProgress
)
from pcloud_sdk.exceptions import PCloudException


def create_test_file(filename: str, size_mb: int) -> str:
    """Create a test file of specified size"""
    print(f"=Ý Creating test file: {filename} ({size_mb}MB)")
    
    # Create content that compresses poorly (more realistic for testing)
    import random
    import string
    
    chunk_size = 1024  # 1KB chunks
    chunks_per_mb = 1024
    total_chunks = size_mb * chunks_per_mb
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(total_chunks):
            # Create semi-random content (realistic file behavior)
            base_content = f"Line {i:06d}: " + ''.join(random.choices(string.ascii_letters + string.digits, k=50))
            content = base_content + '\n'
            f.write(content)
    
    actual_size = os.path.getsize(filename)
    print(f" Test file created: {actual_size:,} bytes")
    return filename


class CustomProgressTracker:
    """Example of a custom progress tracker with advanced features"""
    
    def __init__(self, name: str = "Custom Tracker"):
        self.name = name
        self.start_time = None
        self.last_update = 0
        self.speed_history = []
        self.max_speed = 0
        self.checkpoints = []
        
    def __call__(self, bytes_transferred: int, total_bytes: int, percentage: float, speed: float, **kwargs):
        """Custom progress callback with advanced statistics"""
        
        if self.start_time is None:
            self.start_time = time.time()
            filename = kwargs.get('filename', 'unknown')
            operation = kwargs.get('operation', 'transfer')
            print(f"\n<¯ {self.name}: {operation} of {filename}")
            print(f"   Total size: {total_bytes:,} bytes ({total_bytes/1024/1024:.1f}MB)")
        
        now = time.time()
        status = kwargs.get('status', 'progress')
        
        # Track speed history
        if speed > 0:
            self.speed_history.append(speed)
            if speed > self.max_speed:
                self.max_speed = speed
        
        # Store checkpoints for analysis
        self.checkpoints.append({
            'time': now,
            'bytes': bytes_transferred,
            'percentage': percentage,
            'speed': speed
        })
        
        # Update display every 2 seconds or on status change
        if now - self.last_update >= 2.0 or status != 'progress':
            self.last_update = now
            
            elapsed = now - self.start_time
            avg_speed = bytes_transferred / elapsed if elapsed > 0 else 0
            
            # Format speeds
            current_speed_mb = speed / (1024 * 1024)
            avg_speed_mb = avg_speed / (1024 * 1024)
            max_speed_mb = self.max_speed / (1024 * 1024)
            
            if status == 'progress':
                print(f"   =Ê {percentage:5.1f}% | "
                      f"Current: {current_speed_mb:5.1f}MB/s | "
                      f"Avg: {avg_speed_mb:5.1f}MB/s | "
                      f"Max: {max_speed_mb:5.1f}MB/s")
            
            elif status == 'completed':
                print(f"    Transfer completed!")
                print(f"      Duration: {elapsed:.1f}s")
                print(f"      Average speed: {avg_speed_mb:.1f}MB/s")
                print(f"      Peak speed: {max_speed_mb:.1f}MB/s")
                print(f"      Speed variations: {len(set(self.speed_history))} different speeds")
            
            elif status == 'error':
                error = kwargs.get('error', 'Unknown error')
                print(f"   L Transfer failed: {error}")


class ProgressAnalyzer:
    """Analyzer for progress tracking performance"""
    
    def __init__(self):
        self.trackers = {}
        
    def analyze_tracker(self, name: str, checkpoints: List[Dict]):
        """Analyze tracker performance"""
        if not checkpoints:
            return
        
        print(f"\n=È Analysis for {name}:")
        
        # Calculate statistics
        speeds = [cp['speed'] for cp in checkpoints if cp['speed'] > 0]
        if speeds:
            avg_speed = sum(speeds) / len(speeds) / (1024 * 1024)
            max_speed = max(speeds) / (1024 * 1024)
            min_speed = min(speeds) / (1024 * 1024)
            
            print(f"   Speed - Avg: {avg_speed:.1f}MB/s, Max: {max_speed:.1f}MB/s, Min: {min_speed:.1f}MB/s")
        
        # Calculate duration
        if len(checkpoints) >= 2:
            duration = checkpoints[-1]['time'] - checkpoints[0]['time']
            print(f"   Duration: {duration:.1f}s")
            
            # Update frequency
            updates_per_second = len(checkpoints) / duration if duration > 0 else 0
            print(f"   Update frequency: {updates_per_second:.1f} updates/second")


class ProgressExamplesDemo:
    """Complete progress tracking demonstration"""
    
    def __init__(self):
        self.sdk: Optional[PCloudSDK] = None
        self.demo_folder_id: Optional[int] = None
        self.test_files = []
        self.uploaded_files = []
        
    def setup_sdk(self) -> bool:
        """Setup and authenticate SDK"""
        print("=€ pCloud SDK Progress Tracking Examples")
        print("=" * 50)
        
        self.sdk = PCloudSDK(
            location_id=2,
            token_manager=True,
            token_file=".pcloud_progress_demo"
        )
        
        # Quick authentication check
        if self.sdk.is_authenticated():
            try:
                if self.sdk._test_existing_credentials():
                    email = self.sdk.get_saved_email()
                    print(f" Using saved credentials for: {email}")
                    return True
            except:
                pass
        
        # Need authentication
        print("= Authentication required for progress demo")
        email = input("=ç Enter pCloud email: ").strip()
        password = input("= Enter password: ").strip()
        
        try:
            self.sdk.login(email, password)
            print(" Authentication successful")
            return True
        except Exception as e:
            print(f"L Authentication failed: {e}")
            return False
    
    def setup_demo_environment(self):
        """Create demo folder and test files"""
        print("\n=Á Setting up demo environment...")
        
        # Create demo folder
        folder_name = f"Progress_Demo_{int(time.time())}"
        self.demo_folder_id = self.sdk.folder.create(folder_name)
        print(f" Created demo folder: {folder_name} (ID: {self.demo_folder_id})")
        
        # Create test files of different sizes
        temp_dir = tempfile.gettempdir()
        test_files_info = [
            ("small_file.txt", 1),    # 1MB
            ("medium_file.txt", 5),   # 5MB
            ("large_file.txt", 10),   # 10MB
        ]
        
        for filename, size_mb in test_files_info:
            filepath = os.path.join(temp_dir, filename)
            create_test_file(filepath, size_mb)
            self.test_files.append(filepath)
        
        print(f" Created {len(self.test_files)} test files")
    
    def demo_simple_progress_bar(self):
        """Demonstrate SimpleProgressBar tracker"""
        print("\n" + "="*60)
        print("1ã SIMPLE PROGRESS BAR DEMO")
        print("="*60)
        
        if not self.test_files:
            print("  No test files available")
            return
        
        # Upload with simple progress bar
        test_file = self.test_files[0]  # Small file
        filename = os.path.basename(test_file)
        
        print(f"=ä Uploading {filename} with SimpleProgressBar...")
        
        # Create progress bar with custom settings
        progress_bar = create_progress_bar(
            title=f"Upload: {filename}",
            width=40,
            show_speed=True,
            show_eta=True
        )
        
        try:
            result = self.sdk.file.upload(
                test_file,
                self.demo_folder_id,
                progress_callback=progress_bar
            )
            
            file_id = result['metadata']['fileid']
            self.uploaded_files.append(file_id)
            print(f"   File uploaded with ID: {file_id}")
            
        except Exception as e:
            print(f"L Upload failed: {e}")
    
    def demo_detailed_progress(self):
        """Demonstrate DetailedProgress tracker"""
        print("\n" + "="*60)
        print("2ã DETAILED PROGRESS DEMO")
        print("="*60)
        
        if len(self.test_files) < 2:
            print("  Not enough test files available")
            return
        
        test_file = self.test_files[1]  # Medium file
        filename = os.path.basename(test_file)
        
        print(f"=ä Uploading {filename} with DetailedProgress...")
        
        # Create detailed progress with log file
        log_file = f"progress_log_{int(time.time())}.txt"
        detailed_progress = create_detailed_progress(log_file=log_file)
        
        try:
            result = self.sdk.file.upload(
                test_file,
                self.demo_folder_id,
                progress_callback=detailed_progress
            )
            
            file_id = result['metadata']['fileid']
            self.uploaded_files.append(file_id)
            print(f"   File uploaded with ID: {file_id}")
            print(f"   Progress log saved to: {log_file}")
            
            # Show part of the log file
            if os.path.exists(log_file):
                print("\n=Ä Sample from progress log:")
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-3:]:  # Show last 3 lines
                        print(f"   {line.strip()}")
                
                # Cleanup log file
                os.remove(log_file)
        
        except Exception as e:
            print(f"L Upload failed: {e}")
    
    def demo_minimal_progress(self):
        """Demonstrate MinimalProgress tracker"""
        print("\n" + "="*60)
        print("3ã MINIMAL PROGRESS DEMO")
        print("="*60)
        
        if not self.uploaded_files:
            print("  No uploaded files to download")
            return
        
        # Download with minimal progress
        file_id = self.uploaded_files[0]
        temp_dir = tempfile.gettempdir()
        download_dir = os.path.join(temp_dir, "progress_downloads")
        
        print(f"=å Downloading file ID {file_id} with MinimalProgress...")
        
        minimal_progress = create_minimal_progress()
        
        try:
            os.makedirs(download_dir, exist_ok=True)
            
            success = self.sdk.file.download(
                file_id,
                download_dir,
                progress_callback=minimal_progress
            )
            
            if success:
                print("   Download completed successfully!")
                
                # Cleanup downloaded file
                for f in os.listdir(download_dir):
                    os.remove(os.path.join(download_dir, f))
                os.rmdir(download_dir)
        
        except Exception as e:
            print(f"L Download failed: {e}")
    
    def demo_silent_progress(self):
        """Demonstrate SilentProgress tracker with CSV logging"""
        print("\n" + "="*60)
        print("4ã SILENT PROGRESS DEMO")
        print("="*60)
        
        if len(self.test_files) < 3:
            print("  Not enough test files available")
            return
        
        test_file = self.test_files[2]  # Large file
        filename = os.path.basename(test_file)
        
        # Create CSV log file
        csv_log_file = f"silent_progress_{int(time.time())}.csv"
        
        print(f"=ä Uploading {filename} with SilentProgress...")
        print(f"   Progress will be logged to: {csv_log_file}")
        
        silent_progress = create_silent_progress(csv_log_file)
        
        try:
            result = self.sdk.file.upload(
                test_file,
                self.demo_folder_id,
                progress_callback=silent_progress
            )
            
            file_id = result['metadata']['fileid']
            self.uploaded_files.append(file_id)
            print(f" Upload completed silently! File ID: {file_id}")
            
            # Analyze the CSV log
            self._analyze_csv_log(csv_log_file)
            
            # Cleanup CSV file
            os.remove(csv_log_file)
        
        except Exception as e:
            print(f"L Upload failed: {e}")
    
    def demo_custom_progress(self):
        """Demonstrate custom progress tracker"""
        print("\n" + "="*60)
        print("5ã CUSTOM PROGRESS TRACKER DEMO")
        print("="*60)
        
        if not self.uploaded_files:
            print("  No uploaded files to download")
            return
        
        # Download with custom progress tracker
        file_id = self.uploaded_files[-1]  # Last uploaded file
        temp_dir = tempfile.gettempdir()
        download_dir = os.path.join(temp_dir, "custom_progress_downloads")
        
        print(f"=å Downloading file ID {file_id} with CustomProgressTracker...")
        
        custom_tracker = CustomProgressTracker("Advanced Stats Tracker")
        
        try:
            os.makedirs(download_dir, exist_ok=True)
            
            success = self.sdk.file.download(
                file_id,
                download_dir,
                progress_callback=custom_tracker
            )
            
            if success:
                print("   Download completed!")
                
                # Analyze the custom tracker's data
                analyzer = ProgressAnalyzer()
                analyzer.analyze_tracker("Custom Tracker", custom_tracker.checkpoints)
                
                # Cleanup downloaded file
                for f in os.listdir(download_dir):
                    os.remove(os.path.join(download_dir, f))
                os.rmdir(download_dir)
        
        except Exception as e:
            print(f"L Download failed: {e}")
    
    def demo_progress_comparison(self):
        """Compare different progress trackers"""
        print("\n" + "="*60)
        print("6ã PROGRESS TRACKER COMPARISON")
        print("="*60)
        
        if not self.uploaded_files:
            print("  No uploaded files for comparison")
            return
        
        print("=Ê Downloading same file with different trackers for comparison...")
        
        file_id = self.uploaded_files[0]
        temp_dir = tempfile.gettempdir()
        
        trackers = [
            ("SimpleProgressBar", create_progress_bar("Comparison Test", width=30)),
            ("MinimalProgress", create_minimal_progress()),
            ("CustomTracker", CustomProgressTracker("Comparison Tracker"))
        ]
        
        for name, tracker in trackers:
            print(f"\n= Testing {name}:")
            download_dir = os.path.join(temp_dir, f"compare_{name.lower()}")
            
            try:
                os.makedirs(download_dir, exist_ok=True)
                
                start_time = time.time()
                success = self.sdk.file.download(file_id, download_dir, progress_callback=tracker)
                duration = time.time() - start_time
                
                if success:
                    print(f"    {name} completed in {duration:.1f}s")
                    
                    # Cleanup
                    for f in os.listdir(download_dir):
                        os.remove(os.path.join(download_dir, f))
                    os.rmdir(download_dir)
                else:
                    print(f"   L {name} failed")
            
            except Exception as e:
                print(f"   L {name} error: {e}")
    
    def _analyze_csv_log(self, csv_file: str):
        """Analyze CSV progress log"""
        print("\n=È CSV Log Analysis:")
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                print("     No data in CSV log")
                return
            
            # Skip header comment lines
            data_rows = [row for row in rows if not row.get('# timestamp', '').startswith('#')]
            
            if not data_rows:
                print("     No data rows found")
                return
            
            print(f"   =Ê Total progress entries: {len(data_rows)}")
            
            # Analyze speeds
            speeds = []
            for row in data_rows:
                try:
                    speed = float(row.get('speed_mbps', 0))
                    if speed > 0:
                        speeds.append(speed)
                except:
                    continue
            
            if speeds:
                avg_speed = sum(speeds) / len(speeds)
                max_speed = max(speeds)
                min_speed = min(speeds)
                
                print(f"   =€ Speed analysis:")
                print(f"      Average: {avg_speed:.1f} MB/s")
                print(f"      Maximum: {max_speed:.1f} MB/s")
                print(f"      Minimum: {min_speed:.1f} MB/s")
            
        except Exception as e:
            print(f"   L Error analyzing CSV: {e}")
    
    def cleanup(self):
        """Clean up demo resources"""
        print("\n>ù Cleaning up demo resources...")
        
        try:
            # Delete demo folder
            if self.demo_folder_id:
                self.sdk.folder.delete_recursive(self.demo_folder_id)
                print(" Demo folder deleted")
            
            # Delete test files
            for test_file in self.test_files:
                if os.path.exists(test_file):
                    os.remove(test_file)
                    print(f"=Ñ Removed {os.path.basename(test_file)}")
        
        except Exception as e:
            print(f"  Cleanup error: {e}")
    
    def run_demo(self):
        """Run the complete progress tracking demo"""
        try:
            # Setup
            if not self.setup_sdk():
                return
            
            self.setup_demo_environment()
            
            # Run all progress demos
            self.demo_simple_progress_bar()
            self.demo_detailed_progress()
            self.demo_minimal_progress()
            self.demo_silent_progress()
            self.demo_custom_progress()
            self.demo_progress_comparison()
            
            print("\n<‰ All progress tracking demos completed!")
            
        except KeyboardInterrupt:
            print("\n  Demo interrupted by user")
        except Exception as e:
            print(f"\nL Demo failed: {e}")
        finally:
            self.cleanup()


def main():
    """Main function"""
    print("< Welcome to the pCloud SDK Progress Tracking Examples!")
    print()
    print("This demo will showcase all available progress tracking options:")
    print("" SimpleProgressBar - Visual progress with speed/ETA")
    print("" DetailedProgress - Detailed logging and checkpoints") 
    print("" MinimalProgress - Just key milestones")
    print("" SilentProgress - Background logging to CSV")
    print("" CustomProgress - Build your own tracker")
    print()
    
    proceed = input("Continue with the demo? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("Demo cancelled.")
        return
    
    # Run the demo
    demo = ProgressExamplesDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()