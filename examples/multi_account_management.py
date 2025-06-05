"""
PCloud SDK Multi-Account Management Example

This example demonstrates how to use the PCloudSDK to manage multiple accounts,
perform operations on specific accounts, and utilize new multi-account features
like uploading to a suitable account and searching for files across accounts.

Prerequisites:
- Install the pCloud SDK: pip install pcloud-sdk (or from source)
- Set environment variables for your pCloud App Key and App Secret:
  export PCLOUD_APP_KEY="YOUR_APP_KEY"
  export PCLOUD_APP_SECRET="YOUR_APP_SECRET"
  (Alternatively, you can hardcode them below, but this is not recommended for production.)
- You will need credentials (email/password) for at least two pCloud accounts
  to fully demonstrate the multi-account features.
"""

import os
import time
from typing import Optional, Callable # Required for progress_callback type hint

from pcloud_sdk import PCloudSDK, Account
from pcloud_sdk.exceptions import PCloudException

# --- Configuration ---
# For demonstration, replace with your actual credentials or use environment variables.
# It's highly recommended to use environment variables for sensitive data.
APP_KEY = os.environ.get("PCLOUD_APP_KEY", "YOUR_APP_KEY_HERE")
APP_SECRET = os.environ.get("PCLOUD_APP_SECRET", "YOUR_APP_SECRET_HERE")

# Credentials for the first account
ACCOUNT1_EMAIL = "PCLOUD_ACC1_EMAIL"  # Replace with actual email
ACCOUNT1_PASSWORD = "PCLOUD_ACC1_PASSWORD"  # Replace with actual password
ACCOUNT1_LOCATION_ID = 1  # 1 for US, 2 for EU

# Credentials for the second account
ACCOUNT2_EMAIL = "PCLOUD_ACC2_EMAIL"  # Replace with actual email
ACCOUNT2_PASSWORD = "PCLOUD_ACC2_PASSWORD"  # Replace with actual password
ACCOUNT2_LOCATION_ID = 2  # 1 for US, 2 for EU

# Test file details
TEST_FILE_NAME = f"multi_account_test_file_{int(time.time())}.txt"
TEST_FILE_CONTENT = "This is a test file for pCloud SDK multi-account features.\n"
TEST_FOLDER_ID = 0  # Root folder

def list_managed_accounts(sdk: PCloudSDK, title: str = "Managed Accounts"):
    """Helper function to list accounts and their status."""
    print(f"\n--- {title} ---")
    accounts = sdk.account_manager.list_accounts()
    if not accounts:
        print("No accounts are currently managed.")
        return
    for acc in accounts:
        print(
            f"Account ID: {acc.account_id}, Email: {acc.email or 'N/A'}, "
            f"Authenticated: {acc.is_authenticated}, Location ID: {acc.location_id}"
        )
        if acc.is_authenticated:
            try:
                user_ops = sdk.get_user_operations(acc.account_id)
                # Quota info is fetched on demand by User class methods
                print(f"  Quota: {user_ops.get_quota() // (1024**3)} GB, Used: {user_ops.get_used_quota() // (1024**2)} MB")
            except PCloudException as e:
                print(f"  Could not fetch quota info for {acc.account_id}: {e}")
    print("--------------------")


def main():
    print("Initializing PCloudSDK for multi-account management...")
    # Initialize PCloudSDK. App Key and Secret are global for the SDK instance.
    # Token manager is enabled by default, using ".pcloud_accounts" to store credentials.
    sdk = PCloudSDK(app_key=APP_KEY, app_secret=APP_SECRET)

    # --- 1. Login multiple accounts ---
    print("\nLogging in Account 1...")
    try:
        if ACCOUNT1_EMAIL == "PCLOUD_ACC1_EMAIL" or ACCOUNT1_PASSWORD == "PCLOUD_ACC1_PASSWORD":
            print("WARN: Account 1 credentials are placeholders. Skipping login.")
        else:
            acc1 = sdk.login(
                email=ACCOUNT1_EMAIL,
                password=ACCOUNT1_PASSWORD,
                location_id=ACCOUNT1_LOCATION_ID,
            )
            print(f"Account 1 ({acc1.email}) logged in successfully.")
    except PCloudException as e:
        print(f"Error logging in Account 1: {e}")

    print("\nLogging in Account 2...")
    try:
        if ACCOUNT2_EMAIL == "PCLOUD_ACC2_EMAIL" or ACCOUNT2_PASSWORD == "PCLOUD_ACC2_PASSWORD":
            print("WARN: Account 2 credentials are placeholders. Skipping login.")
        else:
            acc2 = sdk.login(
                email=ACCOUNT2_EMAIL,
                password=ACCOUNT2_PASSWORD,
                location_id=ACCOUNT2_LOCATION_ID,
            )
            print(f"Account 2 ({acc2.email}) logged in successfully.")
    except PCloudException as e:
        print(f"Error logging in Account 2: {e}")

    # --- 2. List managed accounts ---
    list_managed_accounts(sdk, "Accounts After Login")

    # --- 3. Create a local test file ---
    print(f"\nCreating local test file: {TEST_FILE_NAME}")
    with open(TEST_FILE_NAME, "w") as f:
        f.write(TEST_FILE_CONTENT * 10) # Make it a bit larger than zero bytes
    print(f"Local test file '{TEST_FILE_NAME}' created with size: {os.path.getsize(TEST_FILE_NAME)} bytes.")

    # --- 4. Upload a file using upload_to_suitable_account ---
    print(f"\nUploading '{TEST_FILE_NAME}' using smart upload...")
    uploaded_file_metadata = None
    try:
        # Define a simple progress callback (optional)
        def my_progress_callback(current_bytes, total_bytes, percentage, speed, status, filename, error=None):
            print(f"  Upload {filename}: {status} - {current_bytes}/{total_bytes} ({percentage:.2f}%) at {speed/1024:.2f} KB/s")
            if error:
                print(f"  Upload error for {filename}: {error}")

        upload_result = sdk.upload_to_suitable_account(
            file_path=TEST_FILE_NAME,
            folder_id=TEST_FOLDER_ID,
            filename=TEST_FILE_NAME, # Explicitly set filename on pCloud
            progress_callback=my_progress_callback
        )
        print("Upload successful!")
        print(f"  File uploaded to Account ID: {upload_result.get('account_id_used')}")
        print(f"  Account Email: {upload_result.get('account_email_used')}")
        print(f"  pCloud File ID: {upload_result.get('metadata', [{}])[0].get('fileid')}") # Accessing fileid from list of metadata
        uploaded_file_metadata = upload_result.get('metadata', [{}])[0]
    except PCloudException as e:
        print(f"Error during smart upload: {e}")
    except FileNotFoundError as e:
        print(f"Error: Test file not found for upload: {e}")


    # --- 5. Search for the uploaded file ---
    if uploaded_file_metadata: # Only search if upload seemed to succeed
        print(f"\nSearching for '{TEST_FILE_NAME}' across all accounts in folder {TEST_FOLDER_ID}...")
        try:
            found_files = sdk.find_file_in_accounts(
                filename=TEST_FILE_NAME, folder_id=TEST_FOLDER_ID
            )
            if found_files:
                print(f"Found {len(found_files)} instance(s) of '{TEST_FILE_NAME}':")
                for f_info in found_files:
                    print(
                        f"  - Name: {f_info['name']}, File ID: {f_info['fileid']}, "
                        f"Size: {f_info['size']} bytes, "
                        f"Found in Account: {f_info['account_id_found_in']} (Email: {f_info['account_email_found_in']})"
                    )
            else:
                print(f"File '{TEST_FILE_NAME}' not found in any account in folder {TEST_FOLDER_ID}.")
        except PCloudException as e:
            print(f"Error during file search: {e}")

    # --- 6. Perform a specific operation for one account ---
    # Example: Get user info for the first logged-in account (if available)
    # Check if any accounts were successfully logged in
    logged_in_accounts = [acc for acc in sdk.account_manager.list_accounts() if acc.is_authenticated]
    if logged_in_accounts:
        target_account_id = logged_in_accounts[0].account_id
        print(f"\nPerforming specific operation for account: {target_account_id}")
        try:
            user_ops = sdk.get_user_operations(target_account_id)
            user_info = user_ops.get_user_info() # Fetches if not cached
            print(f"  User info for {target_account_id} (Email: {user_ops.get_user_email()}):")
            print(f"    User ID: {user_ops.get_user_id()}")
            print(f"    Registered: {user_info.get('registered')}")
            print(f"    Total Quota: {user_ops.get_quota()} bytes")
            print(f"    Used Quota: {user_ops.get_used_quota()} bytes")

            # Example: Refresh user info
            print(f"  Refreshing user info for {target_account_id}...")
            refreshed_info = user_ops.refresh_user_info()
            print(f"  Refreshed email: {refreshed_info.get('email')}")

        except PCloudException as e:
            print(f"Error performing operation for account {target_account_id}: {e}")
    else:
        print("\nSkipping specific account operation as no accounts were successfully logged in.")

    # --- 7. Log out one account ---
    if logged_in_accounts:
        account_to_logout_id = logged_in_accounts[0].account_id
        print(f"\nLogging out account: {account_to_logout_id}")
        try:
            sdk.logout(account_to_logout_id)
            print(f"Account {account_to_logout_id} logged out.")
        except PCloudException as e:
            print(f"Error logging out account {account_to_logout_id}: {e}")
        except KeyError as e: # If account was somehow removed or ID is wrong
             print(f"Error logging out account {account_to_logout_id}: {e}")


    # --- 8. List accounts again ---
    list_managed_accounts(sdk, "Accounts After Logout")

    # --- 9. (Optional) Clear all saved credentials ---
    # Uncomment the following lines to test clearing all credentials.
    # print("\nClearing all saved credentials...")
    # sdk.clear_saved_credentials()
    # list_managed_accounts(sdk, "Accounts After Clearing All Credentials")
    # print("Exiting. Next run will require fresh logins if credentials were cleared.")

    # --- Cleanup local test file ---
    if os.path.exists(TEST_FILE_NAME):
        print(f"\nCleaning up local test file: {TEST_FILE_NAME}")
        os.remove(TEST_FILE_NAME)

    print("\nMulti-account management example finished.")


if __name__ == "__main__":
    # Basic check for placeholder credentials
    if "YOUR_APP_KEY_HERE" in APP_KEY or "YOUR_APP_SECRET_HERE" in APP_SECRET:
        print("ERROR: Please replace placeholder APP_KEY and APP_SECRET with your actual pCloud app credentials.")
        print("       You can set them as environment variables PCLOUD_APP_KEY and PCLOUD_APP_SECRET,")
        print("       or hardcode them in the example script (not recommended for production).")
        exit(1)

    if "PCLOUD_ACC1_EMAIL" in ACCOUNT1_EMAIL or "PCLOUD_ACC2_EMAIL" in ACCOUNT2_EMAIL:
        print("WARN: Account email placeholders detected. Some parts of the example might be skipped.")
        print("      Please replace PCLOUD_ACCx_EMAIL and PCLOUD_ACCx_PASSWORD with actual test account credentials.")

    main()
