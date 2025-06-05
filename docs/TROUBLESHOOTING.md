# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the pCloud SDK Python v2.0.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Authentication Issues](#authentication-issues)
- [Network Problems](#network-problems)
- [Upload/Download Issues](#uploaddownload-issues)
- [Performance Issues](#performance-issues)
- [Token Management Issues](#token-management-issues)
- [Error Codes Reference](#error-codes-reference)
- [Debug Mode](#debug-mode)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Script

Run this script to quickly diagnose common issues:

```python
#!/usr/bin/env python3
"""
pCloud SDK Health Check
Quick diagnostic tool for common issues
"""

import os
import sys
import time
import tempfile
from pcloud_sdk import PCloudSDK, PCloudException

def health_check():
    """Comprehensive health check for pCloud SDK"""
    
    print("<å pCloud SDK Health Check")
    print("=" * 40)
    
    issues_found 💾0
    
    # Test 1: Import and version check
    print("\n1ã Testing SDK Import...")
    try:
        import pcloud_sdk
        print(f"    SDK version: {pcloud_sdk.__version__}")
    except ImportError as e:
        print(f"   L Import failed: {e}")
        print("   =¡ Solution: pip install pcloud-sdk-python")
        issues_found +💾1
    
    # Test 2: Network connectivity
    print("\n2ã Testing Network Connectivity...")
    try:
        import requests
        response 💾requests.get("https://api.pcloud.com", timeout=10)
        if response.status_code =💾200:
            print("    pCloud API is reachable")
        else:
            print(f"     pCloud API returned status: {response.status_code}")
    except Exception as e:
        print(f"   L Network connectivity issue: {e}")
        print("   =¡ Check your internet connection")
        issues_found +💾1
    
    # Test 3: Authentication
    print("\n3ã Testing Authentication...")
    try:
        sdk 💾PCloudSDK()
        
        # Check for saved credentials
        cred_info 💾sdk.get_credentials_info()
        if cred_info.get('email'):
            print(f"   =Á Found saved credentials for: {cred_info['email']}")
            print(f"   =Å Credentials age: {cred_info.get('age_days', 0):.1f} days")
            
            # Test if credentials work
            try:
                sdk.login()
                email 💾sdk.user.get_user_email()
                print(f"    Authentication successful: {email}")
            except Exception as e:
                print(f"   L Saved credentials invalid: {e}")
                print("   =¡ Try logging in with fresh credentials")
                issues_found +💾1
        else:
            print("   9 No saved credentials found")
            print("   =¡ Run: sdk.login('email', 'password') to authenticate")
            
    except Exception as e:
        print(f"   L Authentication test failed: {e}")
        issues_found +💾1
    
    # Test 4: Basic operations (if authenticated)
    if 'sdk' in locals() and sdk.is_authenticated():
        print("\n4ã Testing Basic Operations...")
        try:
            # Test folder listing
            root_contents 💾sdk.folder.list_root()
            print(f"    Folder listing works ({len(root_contents['contents'])} items)")
            
            # Test file upload/download
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                tmp.write("Health check test file")
                test_file 💾tmp.name
            
            try:
                result 💾sdk.file.upload(test_file, filename="health_check.txt")
                file_id 💾result['metadata'][0]['fileid']
                print("    File upload works")
                
                # Test download
                download_dir 💾tempfile.mkdtemp()
                success 💾sdk.file.download(file_id, download_dir)
                if success:
                    print("    File download works")
                else:
                    print("   L File download failed")
                    issues_found +💾1
                
                # Cleanup
                sdk.file.delete(file_id)
                os.unlink(test_file)
                import shutil
                shutil.rmtree(download_dir)
                
            except Exception as e:
                print(f"   L File operations failed: {e}")
                issues_found +💾1
                
        except Exception as e:
            print(f"   L Basic operations test failed: {e}")
            issues_found +💾1
    
    # Summary
    print(f"\n=Ê Health Check Summary:")
    if issues_found =💾0:
        print("   < All tests passed! SDK is working correctly.")
    else:
        print(f"     Found {issues_found} issue(s). See solutions above.")
    
    return issues_found =💾0

if __name__ =💾"__main__":
    success 💾health_check()
    sys.exit(0 if success else 1)
```

### Quick Environment Check

```python
def check_environment():
    """Quick environment diagnostic"""
    
    print("= Environment Check:")
    
    # Python version
    import sys
    print(f"   Python: {sys.version}")
    
    # Operating system
    import platform
    print(f"   OS: {platform.system()} {platform.release()}")
    
    # Required packages
    try:
        import requests
        print(f"   requests: {requests.__version__}")
    except ImportError:
        print("   L requests not installed")
    
    try:
        import pcloud_sdk
        print(f"   pcloud-sdk: {pcloud_sdk.__version__}")
    except ImportError:
        print("   L pcloud-sdk not installed")
    
    # Network configuration
    try:
        import socket
        hostname 💾socket.gethostname()
        local_ip 💾socket.gethostbyname(hostname)
        print(f"   Network: {hostname} ({local_ip})")
    except:
        print("     Network info unavailable")

check_environment()
```

## Authentication Issues

### Issue: "Invalid credentials" or "Login failed"

**Symptoms:**
- Login fails with email/password
- Error messages about invalid credentials

**Solutions:**

1. **Verify credentials:**
   ```python
   # Test with manual input to avoid typos
   email 💾input("Email: ").strip()
   password 💾input("Password: ").strip()
   
   sdk 💾PCloudSDK()
   try:
       sdk.login(email, password)
       print(" Credentials are correct")
   except PCloudException as e:
       print(f"L Login failed: {e}")
   ```

2. **Try different server locations:**
   ```python
   # Try EU servers first (default)
   try:
       sdk.login(email, password, location_id=2)
   except PCloudException:
       # Fallback to US servers
       print("= Trying US servers...")
       sdk.login(email, password, location_id=1)
   ```

3. **Check for special characters:**
   ```python
   # Ensure no hidden characters or encoding issues
   import unicodedata
   
   def clean_credentials(text):
       # Remove non-printable characters
       return ''.join(char for char in text if unicodedata.category(char)[0] !💾'C')
   
   email 💾clean_credentials(email)
   password 💾clean_credentials(password)
   ```

### Issue: "Token expired" or "Authentication required"

**Symptoms:**
- Operations fail with authentication errors
- Previously working credentials stop working

**Solutions:**

1. **Force re-authentication:**
   ```python
   sdk 💾PCloudSDK()
   
   # Clear old credentials
   sdk.clear_saved_credentials()
   
   # Login with fresh credentials
   sdk.login(email, password, force_login=True)
   ```

2. **Check token age:**
   ```python
   cred_info 💾sdk.get_credentials_info()
   age_days 💾cred_info.get('age_days', 0)
   
   if age_days 🔄 25:  # Refresh before 30-day expiry
       print(f"  Token is {age_days:.1f} days old")
       sdk.login(email, password, force_login=True)
   ```

### Issue: OAuth2 authentication problems

**Symptoms:**
- OAuth2 flow fails
- Invalid authorization code errors

**Solutions:**

1. **Verify OAuth2 setup:**
   ```python
   # Check your app configuration
   sdk 💾PCloudSDK(
       app_key="your_client_id",     # From pCloud developer console
       app_secret="your_client_secret",
       auth_type="oauth2"
   )
   
   # Ensure redirect URI matches exactly
   redirect_uri 💾"http://localhost:8000/callback"  # Must match app config
   auth_url 💾sdk.get_auth_url(redirect_uri)
   print(f"Authorization URL: {auth_url}")
   ```

2. **Debug OAuth2 callback:**
   ```python
   def debug_oauth_callback(callback_url):
       """Extract and validate OAuth2 code from callback URL"""
       from urllib.parse import urlparse, parse_qs
       
       parsed 💾urlparse(callback_url)
       params 💾parse_qs(parsed.query)
       
       if 'code' in params:
           code 💾params['code'][0]
           print(f" Authorization code: {code}")
           return code
       elif 'error' in params:
           error 💾params['error'][0]
           print(f"L OAuth2 error: {error}")
           return None
       else:
           print("L No code or error in callback URL")
           return None
   
   # Usage
   callback_url 💾input("Paste the full callback URL: ")
   code 💾debug_oauth_callback(callback_url)
   if code:
       token_info 💾sdk.authenticate(code)
   ```

## Network Problems

### Issue: Connection timeouts or network errors

**Symptoms:**
- Operations fail with timeout errors
- "Cannot connect to pCloud servers" messages

**Solutions:**

1. **Test network connectivity:**
   ```python
   import requests
   import time
   
   def test_network_connectivity():
       """Test connection to pCloud servers"""
       servers 💾{
           "EU": "https://eapi.pcloud.com",
           "US": "https://api.pcloud.com"
       }
       
       for region, url in servers.items():
           try:
               start_time 💾time.time()
               response 💾requests.get(url, timeout=10)
               elapsed 💾time.time() - start_time
               
               print(f" {region} server: {response.status_code} ({elapsed:.2f}s)")
           except requests.exceptions.Timeout:
               print(f"ð {region} server: Timeout")
           except requests.exceptions.ConnectionError:
               print(f"L {region} server: Connection failed")
           except Exception as e:
               print(f"L {region} server: {e}")
   
   test_network_connectivity()
   ```

2. **Adjust timeout settings:**
   ```python
   # Increase timeout for slow connections
   sdk 💾PCloudSDK()
   sdk.app.set_curl_execution_timeout(300)  # 5 minutes
   ```

3. **Implement retry logic:**
   ```python
   import time
   import random
   
   def retry_with_backoff(func, max_retries=3, base_delay=1):
       """Retry function with exponential backoff"""
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt =💾max_retries - 1:
                   raise e
               
               delay 💾base_delay * (2 ** attempt) + random.uniform(0, 1)
               print(f"= Retry {attempt + 1}/{max_retries} in {delay:.1f}s: {e}")
               time.sleep(delay)
   
   # Usage
   def upload_operation():
       return sdk.file.upload("file.txt")
   
   result 💾retry_with_backoff(upload_operation)
   ```

### Issue: Proxy or firewall blocking connections

**Symptoms:**
- SSL certificate errors
- Connection refused errors
- Proxy authentication required

**Solutions:**

1. **Configure proxy settings:**
   ```python
   import os
   
   # Set proxy environment variables
   os.environ['HTTP_PROXY'] 💾'http://proxy.company.com:8080'
   os.environ['HTTPS_PROXY'] 💾'https://proxy.company.com:8080'
   
   # For authenticated proxies
   os.environ['HTTP_PROXY'] 💾'http://username:password@proxy.company.com:8080'
   ```

2. **Test with different network:**
   ```python
   def test_different_networks():
       """Test connectivity from different networks"""
       print("< Testing network connectivity...")
       print("=¡ Try from different networks:")
       print("   - Mobile hotspot")
       print("   - Different WiFi")
       print("   - VPN connection")
       print("   - Direct ethernet")
   
   test_different_networks()
   ```

## Upload/Download Issues

### Issue: Large file uploads failing

**Symptoms:**
- Uploads stop partway through
- Memory errors with large files
- Timeout errors on large uploads

**Solutions:**

1. **Monitor upload progress:**
   ```python
   from pcloud_sdk.progress_utils import create_detailed_progress
   
   def robust_large_upload(file_path):
       """Upload large files with detailed monitoring"""
       
       file_size 💾os.path.getsize(file_path)
       print(f"=Á File size: {file_size / (1024**3):.2f} GB")
       
       # Use detailed progress for monitoring
       progress 💾create_detailed_progress("upload.log")
       
       try:
           result 💾sdk.file.upload(file_path, progress_callback=progress)
           return result
       except Exception as e:
           print(f"L Upload failed: {e}")
           print("=Ë Check upload.log for details")
           raise
   
   # Usage
   result 💾robust_large_upload("large_file.zip")
   ```

2. **Optimize chunk size:**
   ```python
   from pcloud_sdk.config import Config
   
   # Adjust chunk size based on file size and network speed
   file_size 💾os.path.getsize("large_file.zip")
   
   if file_size 🔄 1024**3:  # 🔄 1GB
       Config.FILE_PART_SIZE 💾50 * 1024 * 1024  # 50MB chunks
   elif file_size 🔄 100 * 1024**2:  # 🔄 100MB
       Config.FILE_PART_SIZE 💾20 * 1024 * 1024  # 20MB chunks
   else:
       Config.FILE_PART_SIZE 💾10 * 1024 * 1024  # 10MB chunks (default)
   
   print(f"=' Chunk size: {Config.FILE_PART_SIZE / (1024**2):.0f}MB")
   ```

3. **Implement upload resume:**
   ```python
   def upload_with_resume(file_path, max_attempts=3):
       """Upload with resume capability"""
       
       for attempt in range(max_attempts):
           try:
               print(f"=ä Upload attempt {attempt + 1}/{max_attempts}")
               
               def progress_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
                   # Save progress for potential resume
                   status 💾kwargs.get('status', 'progress')
                   if status =💾'error':
                       print(f"=¾ Progress saved: {percentage:.1f}%")
               
               result 💾sdk.file.upload(file_path, progress_callback=progress_callback)
               print(" Upload completed successfully")
               return result
               
           except Exception as e:
               print(f"L Attempt {attempt + 1} failed: {e}")
               if attempt ⏱max_attempts - 1:
                   print("= Retrying...")
                   time.sleep(5)
               else:
                   print("L All attempts failed")
                   raise
   
   # Usage
   result 💾upload_with_resume("large_file.zip")
   ```

### Issue: Download corruption or incomplete downloads

**Symptoms:**
- Downloaded files are corrupted
- Downloads stop before completion
- File size mismatches

**Solutions:**

1. **Verify download integrity:**
   ```python
   import hashlib
   
   def verify_download(file_id, local_path):
       """Verify downloaded file integrity"""
       
       # Get file info from pCloud
       try:
           file_info 💾sdk.file.get_info(file_id)
           expected_size 💾file_info.get('size', 0)
           
           # Check local file
           if os.path.exists(local_path):
               actual_size 💾os.path.getsize(local_path)
               
               if actual_size =💾expected_size:
                   print(f" File size matches: {actual_size:,} bytes")
                   return True
               else:
                   print(f"L Size mismatch: expected {expected_size:,}, got {actual_size:,}")
                   return False
           else:
               print(f"L Downloaded file not found: {local_path}")
               return False
               
       except Exception as e:
           print(f"L Verification failed: {e}")
           return False
   
   # Usage
   success 💾sdk.file.download(file_id, "./downloads/")
   if success:
       downloaded_file 💾"./downloads/filename.ext"  # Adjust path
       verify_download(file_id, downloaded_file)
   ```

2. **Download with retry:**
   ```python
   def download_with_retry(file_id, destination, max_retries=3):
       """Download with automatic retry on failure"""
       
       for attempt in range(max_retries):
           try:
               print(f"=å Download attempt {attempt + 1}/{max_retries}")
               
               success 💾sdk.file.download(file_id, destination)
               if success:
                   print(" Download completed")
                   return True
               else:
                   print("L Download returned False")
                   
           except Exception as e:
               print(f"L Download failed: {e}")
               
           if attempt ⏱max_retries - 1:
               print("= Retrying in 5 seconds...")
               time.sleep(5)
       
       print("L All download attempts failed")
       return False
   
   # Usage
   success 💾download_with_retry(file_id, "./downloads/")
   ```

## Performance Issues

### Issue: Slow upload/download speeds

**Symptoms:**
- Transfer speeds much slower than expected
- Operations taking excessively long

**Solutions:**

1. **Benchmark network speed:**
   ```python
   import time
   import tempfile
   
   def benchmark_upload_speed():
       """Benchmark upload speed with test file"""
       
       # Create test file (1MB)
       test_size 💾1024 * 1024
       with tempfile.NamedTemporaryFile(mode='wb', suffix='.dat', delete=False) as tmp:
           tmp.write(b'0' * test_size)
           test_file 💾tmp.name
       
       try:
           start_time 💾time.time()
           
           result 💾sdk.file.upload(test_file, filename="speed_test.dat")
           
           elapsed 💾time.time() - start_time
           speed_mbps 💾(test_size / elapsed) / (1024 * 1024)
           
           print(f"=Ê Upload speed: {speed_mbps:.2f} MB/s")
           
           # Cleanup
           file_id 💾result['metadata'][0]['fileid']
           sdk.file.delete(file_id)
           
       finally:
           os.unlink(test_file)
   
   benchmark_upload_speed()
   ```

2. **Optimize settings for performance:**
   ```python
   def optimize_for_performance():
       """Configure SDK for maximum performance"""
       
       from pcloud_sdk.config import Config
       
       # Increase chunk size for faster networks
       Config.FILE_PART_SIZE 💾20 * 1024 * 1024  # 20MB chunks
       
       # Increase timeout for large files
       sdk.app.set_curl_execution_timeout(3600)  # 1 hour
       
       # Use minimal progress tracking
       from pcloud_sdk.progress_utils import create_minimal_progress
       return create_minimal_progress()
   
   progress 💾optimize_for_performance()
   ```

### Issue: High memory usage

**Symptoms:**
- Memory consumption increases during uploads
- Out of memory errors
- System becomes slow during transfers

**Solutions:**

1. **Monitor memory usage:**
   ```python
   import psutil
   import os
   
   def monitor_memory_usage():
       """Monitor memory usage during operations"""
       process 💾psutil.Process(os.getpid())
       
       def memory_callback(bytes_transferred, total_bytes, percentage, speed, **kwargs):
           memory_mb 💾process.memory_info().rss / (1024 * 1024)
           print(f"=Ê {percentage:.1f}% - Memory: {memory_mb:.1f}MB")
       
       return memory_callback
   
   # Usage
   memory_progress 💾monitor_memory_usage()
   result 💾sdk.file.upload("large_file.zip", progress_callback=memory_progress)
   ```

2. **Reduce chunk size for large files:**
   ```python
   from pcloud_sdk.config import Config
   
   # Reduce chunk size to lower memory usage
   Config.FILE_PART_SIZE 💾5 * 1024 * 1024  # 5MB chunks
   print(f"=' Reduced chunk size to {Config.FILE_PART_SIZE / (1024**2):.0f}MB")
   ```

## Token Management Issues

### Issue: Credentials not saving or loading

**Symptoms:**
- SDK asks for login every time
- Saved credentials not found
- Permission errors with credential files

**Solutions:**

1. **Check file permissions:**
   ```python
   import os
   import stat
   
   def check_credentials_file():
       """Check credentials file status"""
       
       token_file 💾".pcloud_credentials"
       
       if os.path.exists(token_file):
           # Check permissions
           file_stat 💾os.stat(token_file)
           permissions 💾stat.filemode(file_stat.st_mode)
           size 💾file_stat.st_size
           
           print(f"=Ä Credentials file: {token_file}")
           print(f"   Size: {size} bytes")
           print(f"   Permissions: {permissions}")
           
           # Check if readable
           if os.access(token_file, os.R_OK):
               print("    File is readable")
           else:
               print("   L File is not readable")
               
           # Check if writable
           if os.access(token_file, os.W_OK):
               print("    File is writable")
           else:
               print("   L File is not writable")
               
           # Try to read content
           try:
               with open(token_file, 'r') as f:
                   import json
                   data 💾json.load(f)
                   print(f"   =ç Email: {data.get('email', 'Unknown')}")
                   print(f"   =Å Saved: {data.get('saved_at', 'Unknown')}")
           except Exception as e:
               print(f"   L Cannot read file: {e}")
       else:
           print(f"L Credentials file not found: {token_file}")
   
   check_credentials_file()
   ```

2. **Fix file permissions:**
   ```python
   def fix_credentials_permissions():
       """Fix credentials file permissions"""
       
       token_file 💾".pcloud_credentials"
       
       if os.path.exists(token_file):
           try:
               # Set read/write for owner only
               os.chmod(token_file, 0o600)
               print(f" Fixed permissions for {token_file}")
           except Exception as e:
               print(f"L Cannot fix permissions: {e}")
   
   fix_credentials_permissions()
   ```

3. **Use custom credentials file:**
   ```python
   # Use a different location if default doesn't work
   custom_file 💾os.path.expanduser("~/pcloud_credentials.json")
   
   sdk 💾PCloudSDK(token_file=custom_file)
   print(f"=Á Using custom credentials file: {custom_file}")
   ```

## Error Codes Reference

### Common pCloud API Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 1000 | Login failed | Check email/password, try different server |
| 2000 | File not found | Verify file ID exists |
| 2001 | Folder not found | Verify folder ID exists |
| 2003 | Access denied | Check permissions, re-authenticate |
| 2005 | File/folder already exists | Use different name or delete existing |
| 2008 | Name too long | Use shorter filename |
| 2009 | Invalid name | Use valid characters only |
| 4000 | Too many login attempts | Wait before retrying |
| 5000 | Internal error | Retry operation, contact support if persistent |

### SDK-Specific Error Handling

```python
from pcloud_sdk import PCloudException

def handle_pcloud_errors(func):
    """Decorator for comprehensive error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PCloudException as e:
            error_code 💾getattr(e, 'code', 5000)
            error_msg 💾str(e).lower()
            
            if error_code =💾1000:
                print("= Authentication failed - check credentials")
            elif error_code =💾2000:
                print("=Ä File not found - check file ID")
            elif error_code =💾2001:
                print("=Á Folder not found - check folder ID")
            elif error_code =💾2003:
                print("=« Access denied - check permissions")
            elif error_code =💾4000:
                print("ð Rate limited - wait before retrying")
            elif "quota" in error_msg:
                print("=¾ Storage quota exceeded")
            elif "network" in error_msg:
                print("< Network error - check connection")
            else:
                print(f"L pCloud error {error_code}: {e}")
                
            return None
        except Exception as e:
            print(f"L Unexpected error: {e}")
            return None
    
    return wrapper

# Usage
@handle_pcloud_errors
def safe_upload(file_path):
    return sdk.file.upload(file_path)

result 💾safe_upload("file.txt")
```

## Debug Mode

### Enable Detailed Logging

```python
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pcloud_debug.log'),
        logging.StreamHandler()
    ]
)

# Enable debug for specific modules
logger 💾logging.getLogger('pcloud_sdk')
logger.setLevel(logging.DEBUG)

# Enable debug for requests library
logging.getLogger('urllib3').setLevel(logging.DEBUG)
```

### Debug Helper Functions

```python
def debug_request_response():
    """Debug HTTP requests and responses"""
    
    import requests
    import logging
    
    # Enable HTTP debug logging
    import http.client as http_client
    http_client.HTTPConnection.debuglevel 💾1
    
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log 💾logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate 💾True

def debug_sdk_state(sdk):
    """Print SDK state information"""
    
    print("= SDK Debug Information:")
    print(f"   Authenticated: {sdk.is_authenticated()}")
    print(f"   Token Manager: {sdk.token_manager_enabled}")
    print(f"   Token File: {sdk.token_file}")
    print(f"   Location ID: {sdk.app.get_location_id()}")
    print(f"   Auth Type: {sdk.app.get_auth_type()}")
    
    cred_info 💾sdk.get_credentials_info()
    if cred_info.get('email'):
        print(f"   Saved Email: {cred_info['email']}")
        print(f"   Credentials Age: {cred_info.get('age_days', 0):.1f} days")

# Usage
debug_request_response()  # Enable HTTP debugging
debug_sdk_state(sdk)      # Print SDK state
```

## Getting Help

### Collecting Debug Information

When reporting issues, include this debug information:

```python
def collect_debug_info():
    """Collect comprehensive debug information"""
    
    import sys
    import platform
    import os
    
    debug_info 💾{
        'python_version': sys.version,
        'platform': platform.platform(),
        'pcloud_sdk_version': None,
        'requests_version': None,
        'environment': {},
        'sdk_state': {},
        'network_test': {}
    }
    
    # Package versions
    try:
        import pcloud_sdk
        debug_info['pcloud_sdk_version'] 💾pcloud_sdk.__version__
    except:
        debug_info['pcloud_sdk_version'] 💾'Not installed'
    
    try:
        import requests
        debug_info['requests_version'] 💾requests.__version__
    except:
        debug_info['requests_version'] 💾'Not installed'
    
    # Environment variables
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY']:
        debug_info['environment'][key] 💾os.environ.get(key, 'Not set')
    
    # SDK state (if available)
    try:
        sdk 💾PCloudSDK()
        debug_info['sdk_state'] 💾{
            'authenticated': sdk.is_authenticated(),
            'token_manager': sdk.token_manager_enabled,
            'credentials_exist': bool(sdk.get_credentials_info().get('email')),
            'location_id': sdk.app.get_location_id()
        }
    except:
        debug_info['sdk_state'] 💾'SDK not available'
    
    # Network test
    try:
        import requests
        response 💾requests.get('https://api.pcloud.com', timeout=10)
        debug_info['network_test'] 💾{
            'status': 'OK',
            'status_code': response.status_code,
            'response_time': 'Available'
        }
    except Exception as e:
        debug_info['network_test'] 💾{
            'status': 'ERROR',
            'error': str(e)
        }
    
    return debug_info

# Usage
debug_data 💾collect_debug_info()
print("=Ë Debug Information:")
for key, value in debug_data.items():
    print(f"   {key}: {value}")
```

### Support Channels

1. **GitHub Issues**: [Report bugs and feature requests](https://github.com/koffiisen/pcloud-sdk-python/issues)
2. **Documentation**: Check other documentation files in the `docs/` folder
3. **Community Forums**: Search for similar issues in pCloud community
4. **Stack Overflow**: Tag questions with `pcloud` and `python`

### Creating a Minimal Reproduction Case

When reporting issues, create a minimal example:

```python
#!/usr/bin/env python3
"""
Minimal reproduction case for issue reporting
"""

from pcloud_sdk import PCloudSDK, PCloudException

def minimal_reproduction():
    """Minimal example that reproduces the issue"""
    
    # Initialize SDK
    sdk 💾PCloudSDK()
    
    # Attempt to reproduce the issue
    try:
        # Replace with your specific issue
        sdk.login("test@example.com", "password")
        result 💾sdk.file.upload("test.txt")
        print(f"Success: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        
        # Include debug information
        import traceback
        traceback.print_exc()

if __name__ =💾"__main__":
    minimal_reproduction()
```

This troubleshooting guide should help you resolve most common issues with the pCloud SDK. If you encounter persistent problems, don't hesitate to seek help through the support channels mentioned above.