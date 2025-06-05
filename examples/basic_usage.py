#!/usr/bin/env python3
"""
Basic usage example for pCloud SDK Python
Demonstrates the most common operations
"""

import os
import sys
import tempfile

# Import pCloud SDK
from pcloud_sdk import PCloudSDK
from pcloud_sdk.progress_utils import create_progress_bar


def main():
    """Basic usage example for pCloud SDK"""

    print("🚀 pCloud SDK Python - Basic Usage Example")
    print("=" * 50)

    # 1. Configuration and authentication
    print("\n1️⃣ Authentication...")

    # Option A: Use environment variables
    email = os.environ.get("PCLOUD_EMAIL")
    password = os.environ.get("PCLOUD_PASSWORD")

    pcloud = PCloudSDK()

    if email and password:
        print(f"📧 Connecting with email: {email}")
        pcloud.login(email, password)
    else:
        # Option B: Manual input (for demo)
        print("📧 Environment variables not found")
        print("💡 Tip: set PCLOUD_EMAIL and PCLOUD_PASSWORD")

        email = input("pCloud Email: ").strip()
        password = input("Password: ").strip()

        if not email or not password:
            print("❌ Email and password required")
            return

        pcloud.login(email, password)

    try:
        # 2. User information
        print("\n2️⃣ Account Information...")
        user_info = pcloud.user.get_user_info()

        print(f"👤 User: {user_info.get('email', 'N/A')}")
        print(f"💾 Quota: {user_info.get('quota', 0) // (1024**3):.1f} GB")
        print(f"📁 Used: {user_info.get('usedquota', 0) // (1024**3):.1f} GB")

        # 3. List root folder contents
        print("\n3️⃣ Root folder contents...")
        root_content = pcloud.folder.list_root()

        folders = root_content.get("contents", [])
        print(f"📂 {len([f for f in folders if f.get('isfolder')])} folders")
        print(f"📄 {len([f for f in folders if not f.get('isfolder')])} files")

        # Display some items
        for item in folders[:5]:  # First 5 items
            icon = "📁" if item.get("isfolder") else "📄"
            name = item.get("name", "N/A")
            size = item.get("size", 0)
            if not item.get("isfolder"):
                size_mb = size / (1024 * 1024)
                print(f"  {icon} {name} ({size_mb:.1f} MB)")
            else:
                print(f"  {icon} {name}/")

        if len(folders) > 5:
            print(f"  ... and {len(folders) - 5} more items")

        # 4. Create a test folder
        print("\n4️⃣ Creating test folder...")
        test_folder_name = "SDK_Test_Folder"

        try:
            folder_id = pcloud.folder.create(test_folder_name, parent=0)
            print(f"✅ Folder created: {test_folder_name} (ID: {folder_id})")
        except Exception as e:
            print(f"⚠️ Folder already exists or error: {e}")
            # Try to find it
            for item in folders:
                if item.get("name") == test_folder_name and item.get("isfolder"):
                    folder_id = item.get("folderid")
                    print(f"📁 Using existing folder (ID: {folder_id})")
                    break
            else:
                folder_id = 0  # Use root folder as fallback

        # 5. Upload a test file
        print("\n5️⃣ Uploading test file...")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as tmp_file:
            test_content = f"""pCloud SDK Test File
Created on: {__import__('datetime').datetime.now()}
Content: This is a test upload from the pCloud Python SDK
Size: About 200 characters to test upload functionality
"""
            tmp_file.write(test_content)
            tmp_file_path = tmp_file.name

        # Upload with progress bar
        progress_bar = create_progress_bar("Upload Test")

        try:
            upload_result = pcloud.file.upload(
                tmp_file_path,
                folder_id=folder_id,
                filename="test_sdk.txt",
                progress_callback=progress_bar,
            )

            file_id = upload_result["metadata"]["fileid"]
            file_name = upload_result["metadata"]["name"]
            print(f"✅ File uploaded: {file_name} (ID: {file_id})")

        except Exception as e:
            print(f"❌ Upload error: {e}")
            file_id = None

        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except OSError:
                pass

        # 6. Download the file
        if file_id:
            print("\n6️⃣ Downloading file...")

            download_dir = tempfile.mkdtemp()
            progress_bar_dl = create_progress_bar("Download Test")

            try:
                success = pcloud.file.download(
                    file_id, destination=download_dir, progress_callback=progress_bar_dl
                )

                if success:
                    downloaded_files = os.listdir(download_dir)
                    if downloaded_files:
                        downloaded_file = os.path.join(
                            download_dir, downloaded_files[0]
                        )
                        file_size = os.path.getsize(downloaded_file)
                        print(
                            f"✅ File downloaded: "
                            f"{downloaded_files[0]} "
                            f"({file_size} bytes)"
                        )

                        # Verify content
                        with open(downloaded_file, "r") as f:
                            content = f.read()
                            if "pCloud SDK" in content:
                                print("✅ Content verified - download successful!")

            except Exception as e:
                print(f"❌ Download error: {e}")

            finally:
                # Clean up download directory
                try:
                    import shutil

                    shutil.rmtree(download_dir)
                except OSError:
                    pass

            # 7. Delete test file
            print("\n7️⃣ Cleanup...")
            try:
                pcloud.file.delete(file_id)
                print("✅ Test file deleted")
            except Exception as e:
                print(f"⚠️ File deletion error: {e}")

        # 8. Delete test folder
        if folder_id and folder_id != 0:
            try:
                pcloud.folder.delete(folder_id)
                print("✅ Test folder deleted")
            except Exception as e:
                print(f"⚠️ Folder deletion error: {e}")

        print("\n🎉 Basic test completed successfully!")
        print("\n💡 What you can do now:")
        print("   - Explore other examples in the examples/ folder")
        print("   - Check documentation in docs/")
        print("   - Use the CLI: pcloud-sdk --help")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        print("💡 Check your credentials and internet connection")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
