# Progress Callbacks Documentation

Comprehensive guide to the progress tracking system in pCloud SDK Python, including built-in progress trackers, custom callbacks, and performance considerations.

## Table of Contents

- [Overview](#overview)
- [Progress Callback Interface](#progress-callback-interface)
- [Built-in Progress Trackers](#built-in-progress-trackers)
- [Custom Progress Callbacks](#custom-progress-callbacks)
- [Advanced Usage](#advanced-usage)
- [Performance Considerations](#performance-considerations)
- [Real-World Examples](#real-world-examples)
- [Best Practices](#best-practices)

## Overview

The pCloud SDK v2.0 includes a comprehensive progress tracking system that provides real-time feedback during file upload and download operations. This system is designed to be:

- **Flexible**: Support for multiple display styles and custom implementations
- **Performant**: Minimal overhead during file transfers
- **Informative**: Rich information about transfer status, speed, and estimates
- **Easy to use**: Ready-to-use progress trackers with simple factory functions

### Key Features

- Real-time transfer progress with percentage, speed, and ETA
- Multiple built-in progress display styles
- Support for custom progress callbacks
- Detailed transfer information including file names and operation types
- Error handling and status reporting
- Logging and CSV export capabilities
- Thread-safe implementation

## Progress Callback Interface

All progress callbacks follow a standardized interface that provides comprehensive information about the transfer.

### Callback Signature

```python
def progress_callback(
    bytes_transferred: int,
    total_bytes: int,
    percentage: float,
    speed: float,
    **kwargs
) -🔄 None:
    """
    Progress callback function interface
    
    Args:
        bytes_transferred (int): Number of bytes transferred so far
        total_bytes (int): Total number of bytes to transfer
        percentage (float): Transfer percentage (0.0 to 100.0)
        speed (float): Current transfer speed in bytes per second
        **kwargs: Additional information about the transfer
    
    Keyword Arguments:
        operation (str): Type of operation ("upload" or "download")
        filename (str): Name of the file being transferred
        status (str): Current status ("starting", "progress", "saving", "completed", "error")
        error (str): Error message (only when status="error")
    """
    pass
```

### Transfer Status Values

The `status` keyword argument provides information about the current transfer phase:

- **"starting"**: Transfer is initializing
- **"progress"**: Transfer is in progress (normal operation)
- **"saving"**: Upload is complete, file is being saved to pCloud
- **"completed"**: Transfer completed successfully
- **"error"**: Transfer failed with an error

### Basic Example

```python
def simple_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    """Simple progress callback example"""
    operation 💾kwargs.get('operation', 'transfer')
    filename 💾kwargs.get('filename', 'file')
    status 💾kwargs.get('status', 'progress')
    
    if status =💾"starting":
        print(f"=ï¿½ Starting {operation} of {filename}")
    elif status =💾"completed":
        print(f" {operation.title()} completed: {filename}")
    elif status =💾"error":
        error 💾kwargs.get('error', 'Unknown error')
        print(f"L {operation.title()} failed: {error}")
    else:
        # Regular progress update
        speed_mb 💾speed / (1024 * 1024)
        print(f"=ï¿½ {operation.title()}: {percentage:.1f}% at {speed_mb:.1f} MB/s")

# Usage
from pcloud_sdk import PCloudSDK

sdk 💾PCloudSDK()
sdk.login("your_email@example.com", "your_password")

result 💾sdk.file.upload("document.pdf", progress_callback=simple_progress)
```

## Built-in Progress Trackers

The SDK includes four ready-to-use progress trackers, each optimized for different use cases.

### 1. SimpleProgressBar

An interactive progress bar with speed and ETA information.

```python
from pcloud_sdk.progress_utils import create_progress_bar

# Basic usage
progress_bar 💾create_progress_bar("Upload Progress")
result 💾sdk.file.upload("file.txt", progress_callback=progress_bar)

# Customized progress bar
progress_bar 💾create_progress_bar(
    title="Document Upload",
    width=60,           # Progress bar width in characters
    show_speed=True,    # Show transfer speed
    show_eta=True       # Show estimated time remaining
)
result 💾sdk.file.upload("document.pdf", progress_callback=progress_bar)
```

**Output example:**
```
Upload Progress: document.pdf
[ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½ï¿½] 100.0% (15.2/15.2MB) 2.1MB/s ETA:0s
 Completed in 7.2s (average speed: 2.1MB/s)
```

**Features:**
- Animated progress bar with Unicode characters
- Real-time speed calculation in MB/s
- ETA (Estimated Time of Arrival) calculation
- Completion summary with average speed
- Customizable width and display options

### 2. DetailedProgress

Comprehensive progress tracking with optional logging to file.

```python
from pcloud_sdk.progress_utils import create_detailed_progress

# Basic detailed progress
detailed 💾create_detailed_progress()
result 💾sdk.file.upload("large_file.zip", progress_callback=detailed)

# With logging to file
detailed_with_log 💾create_detailed_progress("transfer.log")
result 💾sdk.file.upload("data.csv", progress_callback=detailed_with_log)
```

**Output example:**
```
=ï¿½ Starting upload: large_file.zip (52,428,800 bytes)
=ï¿½ Progress: 20.0% (10,485,760/52,428,800 bytes) - 1.8MB/s - 5.2s elapsed
=ï¿½ Progress: 40.0% (20,971,520/52,428,800 bytes) - 2.1MB/s - 10.1s elapsed
=ï¿½ Saving in progress...
 Transfer completed!
   Duration: 25.4s
   Average speed: 2.0MB/s
   Size: 52,428,800 bytes
```

**Features:**
- Milestone-based progress reporting (every 20%)
- Detailed transfer statistics
- Optional file logging
- Transfer phase notifications
- Comprehensive completion summary

### 3. MinimalProgress

Lightweight progress tracker showing only key milestones.

```python
from pcloud_sdk.progress_utils import create_minimal_progress

minimal 💾create_minimal_progress()
result 💾sdk.file.upload("image.jpg", progress_callback=minimal)
```

**Output example:**
```
=ï¿½ Upload: image.jpg
=ï¿½ 25%...
=ï¿½ 50%...
=ï¿½ 75%...
 Completed in 3.2s
```

**Features:**
- Minimal output (start, 25%, 50%, 75%, completion)
- Low overhead for automated scripts
- Clean, distraction-free output
- Suitable for batch operations

### 4. SilentProgress

Silent operation with CSV logging for analysis.

```python
from pcloud_sdk.progress_utils import create_silent_progress

silent 💾create_silent_progress("transfers.csv")
result 💾sdk.file.upload("video.mp4", progress_callback=silent)

# Check the CSV file for detailed transfer logs
```

**CSV output format:**
```csv
# timestamp,operation,filename,percentage,bytes_transferred,total_bytes,speed_mbps,status
2024-01-15T10:30:00,upload,video.mp4,0.0,0,104857600,0.00,starting
2024-01-15T10:30:01,upload,video.mp4,5.2,5452595,104857600,5.20,progress
2024-01-15T10:30:02,upload,video.mp4,10.8,11324211,104857600,5.87,progress
...
2024-01-15T10:30:20,upload,video.mp4,100.0,104857600,104857600,5.24,completed
```

**Features:**
- No console output during transfer
- Comprehensive CSV logging
- Ideal for automated systems and analysis
- Includes all transfer metrics with timestamps

### Factory Functions

```python
from pcloud_sdk.progress_utils import (
    create_progress_bar,
    create_detailed_progress, 
    create_minimal_progress,
    create_silent_progress
)

# Quick creation with defaults
progress_bar 💾create_progress_bar()
detailed 💾create_detailed_progress()
minimal 💾create_minimal_progress()
silent 💾create_silent_progress("log.csv")

# Customized creation
custom_bar 💾create_progress_bar(
    title="Custom Upload",
    width=80,
    show_speed=True,
    show_eta=False
)

detailed_logged 💾create_detailed_progress("detailed_transfers.log")
```

## Custom Progress Callbacks

Create your own progress callbacks for specific requirements.

### Basic Custom Callback

```python
def my_custom_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    """Custom progress callback example"""
    
    # Extract information
    operation 💾kwargs.get('operation', 'transfer')
    filename 💾kwargs.get('filename', 'file')
    status 💾kwargs.get('status', 'progress')
    
    # Custom logic based on status
    if status =💾"starting":
        print(f"<ï¿½ {operation.upper()} STARTED: {filename}")
        
    elif status =💾"completed":
        print(f"<ï¿½ {operation.upper()} FINISHED: {filename}")
        
    elif status =💾"error":
        error_msg 💾kwargs.get('error', 'Unknown error')
        print(f"=ï¿½ {operation.upper()} FAILED: {error_msg}")
        
    elif int(percentage) % 10 =💾0:  # Every 10%
        speed_mb 💾speed / (1024 * 1024)
        print(f"ï¿½ {percentage:.0f}% complete at {speed_mb:.1f} MB/s")

# Usage
result 💾sdk.file.upload("my_file.txt", progress_callback=my_custom_progress)
```

### Advanced Custom Callback with State

```python
class AdvancedProgressTracker:
    """Advanced progress tracker with state management"""
    
    def __init__(self, notification_interval=5):
        self.notification_interval 💾notification_interval  # seconds
        self.last_notification 💾0
        self.start_time 💾None
        self.checkpoints 💾[]
        
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        """Progress callback with advanced features"""
        
        import time
        current_time 💾time.time()
        
        # Initialize on first call
        if self.start_time is None:
            self.start_time 💾current_time
            operation 💾kwargs.get('operation', 'transfer')
            filename 💾kwargs.get('filename', 'file')
            print(f"=ï¿½ Starting {operation}: {filename}")
            print(f"=ï¿½ Size: {total_bytes:,} bytes ({total_bytes/(1024**2):.1f} MB)")
        
        # Record checkpoint
        checkpoint 💾{
            'time': current_time,
            'bytes': bytes_transferred,
            'percentage': percentage,
            'speed': speed
        }
        self.checkpoints.append(checkpoint)
        
        # Status-based handling
        status 💾kwargs.get('status', 'progress')
        
        if status =💾"starting":
            pass  # Already handled above
            
        elif status =💾"saving":
            print("=ï¿½ Upload complete, saving to pCloud...")
            
        elif status =💾"completed":
            elapsed 💾current_time - self.start_time
            avg_speed 💾bytes_transferred / elapsed / (1024**2)
            
            print(f" Transfer completed!")
            print(f"   =ï¿½ Total time: {elapsed:.1f}s")
            print(f"   =ï¿½ Average speed: {avg_speed:.1f} MB/s")
            print(f"   =ï¿½ Checkpoints recorded: {len(self.checkpoints)}")
            
        elif status =💾"error":
            error_msg 💾kwargs.get('error', 'Unknown error')
            elapsed 💾current_time - self.start_time
            print(f"L Transfer failed after {elapsed:.1f}s: {error_msg}")
            
        else:
            # Time-based notifications
            if current_time - self.last_notification 🔄💾self.notification_interval:
                self.last_notification 💾current_time
                elapsed 💾current_time - self.start_time
                speed_mb 💾speed / (1024 * 1024)
                
                print(f"=ï¿½ {percentage:.1f}% | {speed_mb:.1f} MB/s | {elapsed:.0f}s elapsed")
                
                # Estimate remaining time
                if speed 🔄 0:
                    remaining_bytes 💾total_bytes - bytes_transferred
                    eta_seconds 💾remaining_bytes / speed
                    print(f"ï¿½ ETA: {eta_seconds:.0f}s remaining")
        
    def get_statistics(self):
        """Get transfer statistics"""
        if not self.checkpoints:
            return None
            
        total_time 💾self.checkpoints[-1]['time'] - self.checkpoints[0]['time']
        final_bytes 💾self.checkpoints[-1]['bytes']
        avg_speed 💾final_bytes / total_time if total_time 🔄 0 else 0
        
        return {
            'total_time': total_time,
            'total_bytes': final_bytes,
            'average_speed': avg_speed,
            'checkpoints': len(self.checkpoints)
        }

# Usage
tracker 💾AdvancedProgressTracker(notification_interval=3)
result 💾sdk.file.upload("large_file.zip", progress_callback=tracker)

# Get statistics after completion
stats 💾tracker.get_statistics()
if stats:
    print(f"Final stats: {stats}")
```

### Database Logging Callback

```python
import sqlite3
from datetime import datetime

class DatabaseProgressLogger:
    """Progress callback that logs to SQLite database"""
    
    def __init__(self, db_path="transfers.db"):
        self.db_path 💾db_path
        self.transfer_id 💾None
        self.init_database()
        
    def init_database(self):
        """Initialize database schema"""
        conn 💾sqlite3.connect(self.db_path)
        cursor 💾conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                operation TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                total_bytes INTEGER,
                status TEXT,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_id INTEGER,
                timestamp TIMESTAMP,
                bytes_transferred INTEGER,
                percentage REAL,
                speed REAL,
                FOREIGN KEY (transfer_id) REFERENCES transfers (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        """Progress callback with database logging"""
        
        operation 💾kwargs.get('operation', 'transfer')
        filename 💾kwargs.get('filename', 'file')
        status 💾kwargs.get('status', 'progress')
        
        conn 💾sqlite3.connect(self.db_path)
        cursor 💾conn.cursor()
        
        try:
            if status =💾"starting":
                # Create new transfer record
                cursor.execute('''
                    INSERT INTO transfers (filename, operation, start_time, total_bytes, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filename, operation, datetime.now(), total_bytes, 'in_progress'))
                
                self.transfer_id 💾cursor.lastrowid
                print(f"=ï¿½ Started logging transfer ID {self.transfer_id}: {filename}")
                
            elif status in ["completed", "error"]:
                # Update transfer record
                error_msg 💾kwargs.get('error') if status =💾"error" else None
                cursor.execute('''
                    UPDATE transfers 
                    SET end_time 💾?, status 💾?, error_message 💾?
                    WHERE id 💾?
                ''', (datetime.now(), status, error_msg, self.transfer_id))
                
                print(f"=ï¿½ Transfer {self.transfer_id} {status}")
                
            # Log progress data
            if self.transfer_id:
                cursor.execute('''
                    INSERT INTO progress_logs (transfer_id, timestamp, bytes_transferred, percentage, speed)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.transfer_id, datetime.now(), bytes_transferred, percentage, speed))
            
            conn.commit()
            
        finally:
            conn.close()
    
    def get_transfer_stats(self, transfer_id=None):
        """Get statistics for a transfer"""
        conn 💾sqlite3.connect(self.db_path)
        cursor 💾conn.cursor()
        
        if transfer_id is None:
            transfer_id 💾self.transfer_id
            
        cursor.execute('''
            SELECT t.*, 
                   COUNT(p.id) as progress_records,
                   AVG(p.speed) as avg_speed,
                   MAX(p.speed) as max_speed
            FROM transfers t
            LEFT JOIN progress_logs p ON t.id 💾p.transfer_id
            WHERE t.id 💾?
            GROUP BY t.id
        ''', (transfer_id,))
        
        result 💾cursor.fetchone()
        conn.close()
        
        return result

# Usage
db_logger 💾DatabaseProgressLogger("my_transfers.db")
result 💾sdk.file.upload("document.pdf", progress_callback=db_logger)

# Get statistics
stats 💾db_logger.get_transfer_stats()
print(f"Database stats: {stats}")
```

## Advanced Usage

### Multiple Progress Callbacks

You can combine multiple progress callbacks for different purposes:

```python
def combine_callbacks(*callbacks):
    """Combine multiple progress callbacks"""
    def combined_callback(*args, **kwargs):
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Callback error: {e}")
    
    return combined_callback

# Usage
progress_bar 💾create_progress_bar("Upload")
silent_logger 💾create_silent_progress("upload.csv")
db_logger 💾DatabaseProgressLogger()

combined 💾combine_callbacks(progress_bar, silent_logger, db_logger)
result 💾sdk.file.upload("important_file.zip", progress_callback=combined)
```

### Conditional Progress Callbacks

```python
def conditional_progress(verbose=True, log_file=None):
    """Create progress callback based on conditions"""
    
    if verbose and log_file:
        return create_detailed_progress(log_file)
    elif verbose:
        return create_progress_bar("Transfer")
    elif log_file:
        return create_silent_progress(log_file)
    else:
        return create_minimal_progress()

# Usage based on environment or user preference
import os

verbose_mode 💾os.getenv('VERBOSE', 'false').lower() =💾'true'
log_file 💾os.getenv('LOG_FILE')

progress_callback 💾conditional_progress(verbose_mode, log_file)
result 💾sdk.file.upload("file.txt", progress_callback=progress_callback)
```

### Rate-Limited Progress Updates

```python
class RateLimitedProgress:
    """Progress callback with rate limiting to reduce output frequency"""
    
    def __init__(self, base_callback, update_interval=1.0, percentage_threshold=5.0):
        """
        Args:
            base_callback: Underlying progress callback
            update_interval: Minimum seconds between updates
            percentage_threshold: Minimum percentage change to trigger update
        """
        self.base_callback 💾base_callback
        self.update_interval 💾update_interval
        self.percentage_threshold 💾percentage_threshold
        self.last_update_time 💾0
        self.last_percentage 💾0
        
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        import time
        
        current_time 💾time.time()
        status 💾kwargs.get('status', 'progress')
        
        # Always pass through status changes
        if status !💾'progress':
            self.base_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs)
            return
        
        # Rate limit regular progress updates
        time_elapsed 💾current_time - self.last_update_time
        percentage_change 💾abs(percentage - self.last_percentage)
        
        if (time_elapsed 🔄💾self.update_interval or 
            percentage_change 🔄💾self.percentage_threshold):
            
            self.base_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs)
            self.last_update_time 💾current_time
            self.last_percentage 💾percentage

# Usage
base_progress 💾create_progress_bar("Rate Limited Upload")
rate_limited 💾RateLimitedProgress(base_progress, update_interval=2.0, percentage_threshold=10.0)

result 💾sdk.file.upload("file.txt", progress_callback=rate_limited)
```

## Performance Considerations

### Callback Overhead

Progress callbacks are called frequently during transfers. Keep them lightweight:

```python
#  Good: Lightweight callback
def efficient_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    if int(percentage) % 25 =💾0:  # Only update every 25%
        print(f"Progress: {percentage:.0f}%")

# L Avoid: Heavy operations in callbacks
def inefficient_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    # Don't do this - expensive operations on every call
    with open("log.txt", "a") as f:  # File I/O on every call
        f.write(f"{percentage}\n")
    
    time.sleep(0.1)  # Never sleep in callbacks
    
    # Complex calculations on every call
    import hashlib
    data 💾str(bytes_transferred).encode()
    hash_value 💾hashlib.sha256(data).hexdigest()
```

### Memory Usage

Be careful with state accumulation in callbacks:

```python
class MemoryEfficientProgress:
    """Progress callback that manages memory usage"""
    
    def __init__(self, max_checkpoints=100):
        self.checkpoints 💾[]
        self.max_checkpoints 💾max_checkpoints
        
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        # Limit checkpoint storage
        if len(self.checkpoints) 🔄💾self.max_checkpoints:
            # Keep only recent checkpoints
            self.checkpoints 💾self.checkpoints[-self.max_checkpoints//2:]
        
        self.checkpoints.append({
            'percentage': percentage,
            'speed': speed,
            'time': time.time()
        })
        
        if int(percentage) % 20 =💾0:
            print(f"Progress: {percentage:.0f}%")
```

### Thread Safety

Progress callbacks should be thread-safe if used in multi-threaded environments:

```python
import threading

class ThreadSafeProgress:
    """Thread-safe progress callback"""
    
    def __init__(self):
        self.lock 💾threading.Lock()
        self.data 💾{}
        
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        with self.lock:
            # Thread-safe operations only
            self.data['last_update'] 💾{
                'percentage': percentage,
                'speed': speed
            }
            
            if int(percentage) % 10 =💾0:
                print(f"Thread-safe progress: {percentage:.0f}%")
```

## Real-World Examples

### Backup Progress with Email Notifications

```python
import smtplib
from email.mime.text import MimeText
from datetime import datetime

class BackupProgressNotifier:
    """Progress callback for backup operations with email notifications"""
    
    def __init__(self, smtp_config, recipient_email):
        self.smtp_config 💾smtp_config
        self.recipient_email 💾recipient_email
        self.start_time 💾None
        self.notified_milestones 💾set()
        
    def send_notification(self, subject, message):
        """Send email notification"""
        try:
            msg 💾MimeText(message)
            msg['Subject'] 💾subject
            msg['From'] 💾self.smtp_config['from_email']
            msg['To'] 💾self.recipient_email
            
            server 💾smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port'])
            server.starttls()
            server.login(self.smtp_config['username'], self.smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        operation 💾kwargs.get('operation', 'transfer')
        filename 💾kwargs.get('filename', 'file')
        status 💾kwargs.get('status', 'progress')
        
        if status =💾"starting":
            self.start_time 💾datetime.now()
            message 💾f"Backup started: {filename}\nSize: {total_bytes:,} bytes"
            self.send_notification("Backup Started", message)
            
        elif status =💾"completed":
            duration 💾datetime.now() - self.start_time
            avg_speed 💾bytes_transferred / duration.total_seconds() / (1024**2)
            
            message 💾f"""Backup completed successfully!
File: {filename}
Size: {bytes_transferred:,} bytes
Duration: {duration}
Average speed: {avg_speed:.1f} MB/s"""
            
            self.send_notification("Backup Completed", message)
            
        elif status =💾"error":
            error_msg 💾kwargs.get('error', 'Unknown error')
            message 💾f"Backup failed: {filename}\nError: {error_msg}"
            self.send_notification("Backup Failed", message)
            
        else:
            # Milestone notifications (25%, 50%, 75%)
            milestone 💾int(percentage // 25) * 25
            if milestone 🔄 0 and milestone not in self.notified_milestones:
                self.notified_milestones.add(milestone)
                
                if milestone in [25, 50, 75]:
                    speed_mb 💾speed / (1024 * 1024)
                    elapsed 💾datetime.now() - self.start_time
                    
                    message 💾f"""Backup progress update:
File: {filename}
Progress: {milestone}%
Speed: {speed_mb:.1f} MB/s
Elapsed: {elapsed}"""
                    
                    self.send_notification(f"Backup {milestone}% Complete", message)

# Usage
smtp_config 💾{
    'server': 'smtp.gmail.com',
    'port': 587,
    'username': 'your_email@gmail.com',
    'password': 'your_app_password',
    'from_email': 'your_email@gmail.com'
}

notifier 💾BackupProgressNotifier(smtp_config, "admin@company.com")
result 💾sdk.file.upload("critical_backup.zip", progress_callback=notifier)
```

### Monitoring Dashboard Progress

```python
import json
import time
from datetime import datetime

class DashboardProgress:
    """Progress callback that writes status to a JSON file for dashboard monitoring"""
    
    def __init__(self, status_file="transfer_status.json"):
        self.status_file 💾status_file
        self.transfer_data 💾{}
        
    def update_status_file(self):
        """Update the JSON status file"""
        try:
            with open(self.status_file, 'w') as f:
                json.dump(self.transfer_data, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to update status file: {e}")
    
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        operation 💾kwargs.get('operation', 'transfer')
        filename 💾kwargs.get('filename', 'file')
        status 💾kwargs.get('status', 'progress')
        
        # Update transfer data
        self.transfer_data.update({
            'filename': filename,
            'operation': operation,
            'status': status,
            'percentage': round(percentage, 2),
            'bytes_transferred': bytes_transferred,
            'total_bytes': total_bytes,
            'speed_mbps': round(speed / (1024 * 1024), 2),
            'last_update': datetime.now(),
            'error_message': kwargs.get('error') if status =💾'error' else None
        })
        
        if status =💾"starting":
            self.transfer_data.update({
                'start_time': datetime.now(),
                'estimated_completion': None
            })
            
        elif status =💾"completed":
            self.transfer_data.update({
                'end_time': datetime.now(),
                'estimated_completion': None
            })
            
        elif speed 🔄 0 and status =💾"progress":
            # Calculate ETA
            remaining_bytes 💾total_bytes - bytes_transferred
            eta_seconds 💾remaining_bytes / speed
            eta_time 💾datetime.now().timestamp() + eta_seconds
            
            self.transfer_data['estimated_completion'] 💾datetime.fromtimestamp(eta_time)
        
        # Write to file
        self.update_status_file()

# Usage
dashboard 💾DashboardProgress("current_transfer.json")
result 💾sdk.file.upload("large_dataset.csv", progress_callback=dashboard)

# Dashboard can read current_transfer.json for real-time updates
```

## Best Practices

### 1. Choose the Right Progress Tracker

```python
# For interactive user applications
progress_bar 💾create_progress_bar("User Upload")

# For automated scripts with logging
detailed 💾create_detailed_progress("automation.log")

# For batch operations
minimal 💾create_minimal_progress()

# For headless systems with data analysis needs
silent 💾create_silent_progress("metrics.csv")
```

### 2. Handle Errors Gracefully

```python
def robust_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    """Progress callback with error handling"""
    try:
        status 💾kwargs.get('status', 'progress')
        
        if status =💾"error":
            # Log error details
            error_msg 💾kwargs.get('error', 'Unknown error')
            print(f"L Transfer failed: {error_msg}")
            
            # Could implement retry logic or notifications here
            
        elif status =💾"completed":
            print(f" Transfer completed successfully")
            
        else:
            # Regular progress display
            if int(percentage) % 20 =💾0:
                speed_mb 💾speed / (1024 * 1024)
                print(f"=ï¿½ {percentage:.0f}% at {speed_mb:.1f} MB/s")
                
    except Exception as e:
        # Never let callback errors break the transfer
        print(f"Progress callback error: {e}")
```

### 3. Optimize for Performance

```python
#  Efficient: Update only when needed
def efficient_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    # Use integer percentage to avoid floating point precision issues
    int_percentage 💾int(percentage)
    
    # Update only at specific intervals
    if int_percentage % 10 =💾0:  # Every 10%
        print(f"Progress: {int_percentage}%")

#  Rate-limited updates for high-frequency callbacks
class RateLimitedCallback:
    def __init__(self, min_interval=0.5):  # Minimum 0.5 seconds between updates
        self.last_update 💾0
        self.min_interval 💾min_interval
    
    def __call__(self, bytes_transferred, total_bytes, percentage, speed, **kwargs):
        current_time 💾time.time()
        
        if current_time - self.last_update 🔄💾self.min_interval:
            print(f"Progress: {percentage:.1f}%")
            self.last_update 💾current_time
```

### 4. Provide Meaningful Feedback

```python
def user_friendly_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
    """Progress callback optimized for user experience"""
    
    operation 💾kwargs.get('operation', 'transfer')
    filename 💾kwargs.get('filename', 'file')
    status 💾kwargs.get('status', 'progress')
    
    if status =💾"starting":
        # Show file size in human-readable format
        size_mb 💾total_bytes / (1024 * 1024)
        if size_mb ⏱1:
            size_str 💾f"{total_bytes / 1024:.1f} KB"
        elif size_mb ⏱1024:
            size_str 💾f"{size_mb:.1f} MB"
        else:
            size_str 💾f"{size_mb / 1024:.1f} GB"
            
        print(f"=ï¿½ Starting {operation} of {filename} ({size_str})")
        
    elif status =💾"saving":
        print("=ï¿½ Upload complete, saving to pCloud...")
        
    elif status =💾"completed":
        print(f" {operation.title()} completed successfully!")
        
    elif status =💾"error":
        error_msg 💾kwargs.get('error', 'Unknown error')
        print(f"L {operation.title()} failed: {error_msg}")
        
    else:
        # Show progress with context
        if int(percentage) % 25 =💾0:
            speed_mb 💾speed / (1024 * 1024)
            
            if speed_mb 🔄 10:
                speed_emoji 💾"=ï¿½"
            elif speed_mb 🔄 5:
                speed_emoji 💾"ï¿½"
            elif speed_mb 🔄 1:
                speed_emoji 💾"=ï¿½"
            else:
                speed_emoji 💾"="
                
            print(f"{speed_emoji} {percentage:.0f}% complete at {speed_mb:.1f} MB/s")
```

This comprehensive guide covers all aspects of the progress callback system in the pCloud SDK. The system is designed to be both powerful and easy to use, providing the flexibility needed for any application while maintaining excellent performance during file transfers.