#!/usr/bin/env python3
"""
pCloud SDK Complete Demo
========================

This comprehensive example demonstrates all major features of the pCloud SDK:
- Authentication and user account management
- Folder creation, navigation, and management
- File upload with different progress trackers
- File download and verification
- File operations (rename, move, copy, delete)
- Error handling and cleanup
- Best practices demonstration

Run this script to see the SDK in action!
"""

import os
import tempfile
import hashlib
import time
from typing import Optional

from pcloud_sdk import PCloudSDK, create_progress_bar, create_detailed_progress
from pcloud_sdk.exceptions import PCloudException


def create_test_file(filename: str, size_mb: int = 5) -> str:
    """Create a test file for upload demonstration"""
    content = f"This is a test file created by pCloud SDK demo.\n" * (size_mb * 1024 * 20)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filename


def calculate_file_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file for verification"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def format_bytes(bytes_size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


class PCloudDemo:
    """Complete pCloud SDK demonstration class"""
    
    def __init__(self):
        self.sdk: Optional[PCloudSDK] = None
        self.demo_folder_id: Optional[int] = None
        self.temp_files = []
        
    def setup_sdk(self):
        """Initialize and authenticate with pCloud SDK"""
        print("=€ pCloud SDK Complete Demo")
        print("=" * 50)
        
        # Initialize SDK with automatic token management
        self.sdk = PCloudSDK(
            location_id=2,  # EU server
            token_manager=True,
            token_file=".pcloud_demo_credentials"
        )
        
        # Check if we have saved credentials
        if self.sdk.is_authenticated():
            print("= Using saved credentials...")
            try:
                if self.sdk._test_existing_credentials():
                    email = self.sdk.get_saved_email()
                    print(f" Successfully authenticated as: {email}")
                    return True
                else:
                    print("  Saved credentials expired, need fresh login")
            except Exception as e:
                print(f"  Credential test failed: {e}")
        
        # Need fresh authentication
        print("\n= Authentication Required")
        print("Choose authentication method:")
        print("1. Email/Password (Direct)")
        print("2. OAuth2 Flow")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            return self._authenticate_direct()
        elif choice == "2":
            return self._authenticate_oauth2()
        else:
            print("L Invalid choice")
            return False
    
    def _authenticate_direct(self) -> bool:
        """Direct email/password authentication"""
        try:
            email = input("=ç Enter your pCloud email: ").strip()
            password = input("= Enter your password: ").strip()
            
            if not email or not password:
                print("L Email and password are required")
                return False
            
            print("= Authenticating...")
            login_info = self.sdk.login(email, password, location_id=2)
            
            print(f" Successfully logged in as: {login_info['email']}")
            return True
            
        except PCloudException as e:
            print(f"L Authentication failed: {e}")
            return False
    
    def _authenticate_oauth2(self) -> bool:
        """OAuth2 authentication flow"""
        try:
            # Note: This requires app_key and app_secret to be set
            if not self.sdk.app.get_app_key():
                print("L OAuth2 requires app_key and app_secret to be configured")
                print("Please modify this script to include your pCloud app credentials")
                return False
            
            # Generate authorization URL
            redirect_uri = "http://localhost:8080/callback"  # Example redirect URI
            auth_url = self.sdk.get_auth_url(redirect_uri)
            
            print(f"< Please visit this URL to authorize the app:")
            print(auth_url)
            print()
            
            # Get authorization code from user
            code = input("=Ý Enter the authorization code from the callback URL: ").strip()
            
            if not code:
                print("L Authorization code is required")
                return False
            
            print("= Exchanging code for token...")
            token_info = self.sdk.authenticate(code, location_id=2)
            
            print(f" OAuth2 authentication successful!")
            return True
            
        except PCloudException as e:
            print(f"L OAuth2 authentication failed: {e}")
            return False
    
    def display_account_info(self):
        """Display user account information"""
        print("\n=d Account Information")
        print("-" * 30)
        
        try:
            user_info = self.sdk.user.get_user_info()
            
            print(f"=ç Email: {user_info.get('email', 'N/A')}")
            print(f"<” User ID: {user_info.get('userid', 'N/A')}")
            
            quota = user_info.get('quota', 0)
            used_quota = user_info.get('usedquota', 0)
            free_space = quota - used_quota
            
            print(f"=¾ Storage Used: {format_bytes(used_quota)}")
            print(f"=Ê Total Quota: {format_bytes(quota)}")
            print(f"=¿ Free Space: {format_bytes(free_space)}")
            print(f"=È Usage: {(used_quota/quota)*100:.1f}%")
            
            # Check if business account
            if user_info.get('business'):
                print("<â Business Account: Yes")
            
        except Exception as e:
            print(f"  Error getting account info: {e}")
    
    def demonstrate_folder_operations(self):
        """Demonstrate folder creation and management"""
        print("\n=Á Folder Operations Demo")
        print("-" * 30)
        
        try:
            # List root folder
            print("=Ë Root folder contents:")
            root_contents = self.sdk.folder.get_content(path="/")
            
            for item in root_contents[:5]:  # Show first 5 items
                if item.get('isfolder'):
                    print(f"  =Á {item['name']} (folder)")
                else:
                    size = format_bytes(item.get('size', 0))
                    print(f"  =Ä {item['name']} ({size})")
            
            if len(root_contents) > 5:
                print(f"  ... and {len(root_contents) - 5} more items")
            
            # Create demo folder
            demo_folder_name = f"pCloud_SDK_Demo_{int(time.time())}"
            print(f"\n=Á Creating demo folder: {demo_folder_name}")
            
            self.demo_folder_id = self.sdk.folder.create(demo_folder_name)
            print(f" Demo folder created with ID: {self.demo_folder_id}")
            
            # Create subfolder
            subfolder_id = self.sdk.folder.create("Subfolder_Test", self.demo_folder_id)
            print(f" Subfolder created with ID: {subfolder_id}")
            
            # List demo folder contents
            print("\n=Ë Demo folder contents:")
            demo_contents = self.sdk.folder.get_content(self.demo_folder_id)
            
            if demo_contents:
                for item in demo_contents:
                    if item.get('isfolder'):
                        print(f"  =Á {item['name']}")
                    else:
                        print(f"  =Ä {item['name']}")
            else:
                print("  (Empty except for subfolder)")
            
        except Exception as e:
            print(f"L Error in folder operations: {e}")
    
    def demonstrate_file_upload(self):
        """Demonstrate file upload with different progress trackers"""
        print("\n=ä File Upload Demo")
        print("-" * 30)
        
        # Create test files
        test_files = []
        temp_dir = tempfile.gettempdir()
        
        try:
            # Create different sized test files
            small_file = os.path.join(temp_dir, "small_test.txt")
            medium_file = os.path.join(temp_dir, "medium_test.txt")
            
            create_test_file(small_file, 1)  # 1MB
            create_test_file(medium_file, 5)  # 5MB
            
            test_files.extend([small_file, medium_file])
            self.temp_files.extend(test_files)
            
            # Upload with simple progress bar
            print("1ã Upload with Simple Progress Bar:")
            progress_bar = create_progress_bar("Small File Upload")
            
            result = self.sdk.file.upload(
                small_file, 
                self.demo_folder_id,
                progress_callback=progress_bar
            )
            small_file_id = result['metadata']['fileid']
            print(f"   File ID: {small_file_id}")
            
            # Upload with detailed progress
            print("\n2ã Upload with Detailed Progress:")
            detailed_progress = create_detailed_progress()
            
            result = self.sdk.file.upload(
                medium_file, 
                self.demo_folder_id,
                progress_callback=detailed_progress
            )
            medium_file_id = result['metadata']['fileid']
            print(f"   File ID: {medium_file_id}")
            
            # Store file IDs for later operations
            self.uploaded_file_ids = [small_file_id, medium_file_id]
            
        except Exception as e:
            print(f"L Error in file upload: {e}")
            # Cleanup temp files
            for f in test_files:
                if os.path.exists(f):
                    os.remove(f)
    
    def demonstrate_file_download(self):
        """Demonstrate file download with verification"""
        print("\n=å File Download Demo")
        print("-" * 30)
        
        if not hasattr(self, 'uploaded_file_ids') or not self.uploaded_file_ids:
            print("  No uploaded files to download")
            return
        
        temp_dir = tempfile.gettempdir()
        download_dir = os.path.join(temp_dir, "pcloud_downloads")
        
        try:
            # Create download directory
            os.makedirs(download_dir, exist_ok=True)
            
            # Download first file with progress
            file_id = self.uploaded_file_ids[0]
            print(f"=å Downloading file ID {file_id}...")
            
            progress_bar = create_progress_bar("Download Progress")
            
            success = self.sdk.file.download(
                file_id,
                download_dir,
                progress_callback=progress_bar
            )
            
            if success:
                # List downloaded files
                downloaded_files = os.listdir(download_dir)
                print(f" Downloaded files: {downloaded_files}")
                
                # Verify file integrity (if we have original)
                if self.temp_files:
                    original_file = self.temp_files[0]
                    downloaded_file = os.path.join(download_dir, os.path.basename(original_file))
                    
                    if os.path.exists(downloaded_file):
                        original_hash = calculate_file_hash(original_file)
                        downloaded_hash = calculate_file_hash(downloaded_file)
                        
                        if original_hash == downloaded_hash:
                            print(" File integrity verified - checksums match!")
                        else:
                            print("  File integrity check failed - checksums don't match")
            
            # Cleanup downloaded files
            for f in os.listdir(download_dir):
                os.remove(os.path.join(download_dir, f))
            os.rmdir(download_dir)
            
        except Exception as e:
            print(f"L Error in file download: {e}")
    
    def demonstrate_file_operations(self):
        """Demonstrate file operations (rename, move, copy, delete)"""
        print("\n=' File Operations Demo")
        print("-" * 30)
        
        if not hasattr(self, 'uploaded_file_ids') or not self.uploaded_file_ids:
            print("  No uploaded files for operations")
            return
        
        try:
            file_id = self.uploaded_file_ids[0]
            
            # Get original file info
            print("=Ë Original file info:")
            file_info = self.sdk.file.get_info(file_id)
            original_name = file_info['metadata']['name']
            print(f"   Name: {original_name}")
            print(f"   Size: {format_bytes(file_info['metadata']['size'])}")
            
            # Rename file
            new_name = f"renamed_{original_name}"
            print(f"\n<÷ Renaming file to: {new_name}")
            self.sdk.file.rename(file_id, new_name)
            print(" File renamed successfully")
            
            # Copy file
            print(f"\n=Ë Copying file...")
            copy_result = self.sdk.file.copy(file_id, self.demo_folder_id)
            copied_file_id = copy_result['metadata']['fileid']
            print(f" File copied successfully (new ID: {copied_file_id})")
            
            # Move copied file to subfolder (if exists)
            demo_contents = self.sdk.folder.get_content(self.demo_folder_id)
            subfolder = next((item for item in demo_contents if item.get('isfolder')), None)
            
            if subfolder:
                print(f"\n=Á Moving copied file to subfolder...")
                self.sdk.file.move(copied_file_id, subfolder['folderid'])
                print(" File moved successfully")
            
            # Delete the copied file
            print(f"\n=Ñ Deleting copied file...")
            self.sdk.file.delete(copied_file_id)
            print(" File deleted successfully")
            
        except Exception as e:
            print(f"L Error in file operations: {e}")
    
    def cleanup(self):
        """Clean up demo resources"""
        print("\n>ù Cleanup")
        print("-" * 30)
        
        try:
            # Delete demo folder and contents
            if self.demo_folder_id:
                print("=Ñ Deleting demo folder and all contents...")
                self.sdk.folder.delete_recursive(self.demo_folder_id)
                print(" Demo folder cleaned up")
            
            # Clean up temp files
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"=Ñ Removed temp file: {os.path.basename(temp_file)}")
            
        except Exception as e:
            print(f"  Error during cleanup: {e}")
    
    def run_complete_demo(self):
        """Run the complete demonstration"""
        try:
            # Setup and authentication
            if not self.setup_sdk():
                print("L Authentication failed, exiting demo")
                return
            
            # Run all demonstrations
            self.display_account_info()
            self.demonstrate_folder_operations()
            self.demonstrate_file_upload()
            self.demonstrate_file_download()
            self.demonstrate_file_operations()
            
            print("\n<‰ Demo completed successfully!")
            
        except KeyboardInterrupt:
            print("\n  Demo interrupted by user")
        except Exception as e:
            print(f"\nL Demo failed with error: {e}")
        finally:
            # Always cleanup
            self.cleanup()
            print("\n=K Demo finished")


def main():
    """Main function to run the complete demo"""
    print("< Welcome to the pCloud SDK Complete Demo!")
    print("This demo will showcase all major SDK features.")
    print()
    
    # Ask user if they want to proceed
    proceed = input("Do you want to continue? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("Demo cancelled.")
        return
    
    # Run the demo
    demo = PCloudDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()