#!/usr/bin/env python3
"""
pCloud SDK Token Management Examples
===================================

This example demonstrates comprehensive token management features of the pCloud SDK.
Token management is crucial for production applications to provide seamless user
experiences and maintain security.

This example covers:
- Automatic token saving and loading
- Manual token management
- Multi-account setup
- Token validation and refresh
- Security best practices
- Credential file management
- Token lifecycle handling
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pcloud_sdk import PCloudException, PCloudSDK


class TokenManager:
    """Advanced token management utility"""

    def __init__(self, base_dir: str = "."):
        """
        Initialize token manager

        Args:
            base_dir: Base directory for storing credential files
        """
        self.base_dir = base_dir
        self.accounts = {}
        self.current_account = None

    def add_account(
        self, name: str, email: str, password: str, token_file: Optional[str] = None
    ) -> bool:
        """
        Add an account to the token manager

        Args:
            name: Account nickname
            email: pCloud email
            password: pCloud password
            token_file: Custom token file path

        Returns:
            True if account added successfully
        """
        try:
            if not token_file:
                # Generate safe filename from email
                safe_email = email.replace("@", "_").replace(".", "_")
                token_file = os.path.join(self.base_dir, f".pcloud_{safe_email}")

            # Initialize SDK for this account
            sdk = PCloudSDK(token_file=token_file)

            # Attempt login
            print(f"🔐 Logging in to account: {name} ({email})")
            sdk.login(email, password)

            # Store account info
            self.accounts[name] = {
                "email": email,
                "password": password,  # Store securely in production!
                "token_file": token_file,
                "sdk": sdk,
                "added_at": datetime.now().isoformat(),
            }

            print(f"✅ Account '{name}' added successfully")
            if not self.current_account:
                self.current_account = name
                print(f"🎯 Set as current account")

            return True

        except PCloudException as e:
            print(f"❌ Failed to add account '{name}': {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error adding account '{name}': {e}")
            return False

    def switch_account(self, name: str) -> bool:
        """
        Switch to a different account

        Args:
            name: Account name to switch to

        Returns:
            True if switch successful
        """
        if name not in self.accounts:
            print(f"❌ Account '{name}' not found")
            return False

        self.current_account = name
        print(f"🔄 Switched to account: {name}")
        return True

    def get_current_sdk(self) -> Optional[PCloudSDK]:
        """Get SDK instance for current account"""
        if not self.current_account or self.current_account not in self.accounts:
            print("❌ No current account selected")
            return None

        return self.accounts[self.current_account]["sdk"]

    def list_accounts(self):
        """List all managed accounts"""
        if not self.accounts:
            print("📭 No accounts configured")
            return

        print("📋 Configured accounts:")
        for name, info in self.accounts.items():
            current_marker = "👉 " if name == self.current_account else "   "
            added_date = info["added_at"][:10]  # Just the date part
            print(f"{current_marker}{name}: {info['email']} (added: {added_date})")

    def validate_all_tokens(self) -> Dict[str, bool]:
        """
        Validate tokens for all accounts

        Returns:
            Dict mapping account names to validation status
        """
        results = {}

        print("🔍 Validating tokens for all accounts...")

        for name, info in self.accounts.items():
            try:
                sdk = info["sdk"]
                user_info = sdk.user.get_user_info()
                results[name] = True
                print(f"✅ {name}: Token valid (user: {user_info.get('email')})")

            except PCloudException as e:
                results[name] = False
                print(f"❌ {name}: Token invalid ({e})")
            except Exception as e:
                results[name] = False
                print(f"❌ {name}: Validation error ({e})")

        return results

    def cleanup_invalid_tokens(self):
        """Remove accounts with invalid tokens"""
        validation_results = self.validate_all_tokens()

        invalid_accounts = [
            name for name, valid in validation_results.items() if not valid
        ]

        if not invalid_accounts:
            print("✅ All tokens are valid")
            return

        print(f"\n🧹 Found {len(invalid_accounts)} invalid tokens")

        for name in invalid_accounts:
            confirm = input(f"Remove invalid account '{name}'? (y/n): ").strip().lower()
            if confirm == "y":
                self.remove_account(name)

    def remove_account(self, name: str) -> bool:
        """
        Remove an account from management

        Args:
            name: Account name to remove

        Returns:
            True if removal successful
        """
        if name not in self.accounts:
            print(f"❌ Account '{name}' not found")
            return False

        # Get token file path
        token_file = self.accounts[name]["token_file"]

        # Remove from memory
        del self.accounts[name]

        # Remove token file
        try:
            if os.path.exists(token_file):
                os.remove(token_file)
                print(f"🗑️ Removed token file: {token_file}")
        except Exception as e:
            print(f"⚠️ Could not remove token file: {e}")

        # Update current account if necessary
        if self.current_account == name:
            if self.accounts:
                self.current_account = list(self.accounts.keys())[0]
                print(f"🔄 Switched to account: {self.current_account}")
            else:
                self.current_account = None
                print("📭 No accounts remaining")

        print(f"✅ Account '{name}' removed")
        return True

    def get_account_info(self, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an account

        Args:
            name: Account name (uses current if None)

        Returns:
            Account information dict or None
        """
        if not name:
            name = self.current_account

        if not name or name not in self.accounts:
            print(f"❌ Account '{name}' not found")
            return None

        account = self.accounts[name]
        sdk = account["sdk"]

        try:
            # Get credentials info from SDK
            creds_info = sdk.get_credentials_info()

            # Get user info from API
            user_info = sdk.user.get_user_info()

            return {
                "name": name,
                "email": account["email"],
                "token_file": account["token_file"],
                "added_at": account["added_at"],
                "credentials_age_days": creds_info.get("age_days", 0),
                "last_used": creds_info.get("last_used", "Unknown"),
                "user_quota": user_info.get("quota", 0),
                "user_used_quota": user_info.get("usedquota", 0),
                "user_email_verified": user_info.get("emailverified", False),
            }

        except Exception as e:
            print(f"❌ Error getting account info: {e}")
            return None


def demonstrate_automatic_token_management():
    """Demonstrate automatic token management"""
    print("\n" + "=" * 60)
    print("1️⃣ AUTOMATIC TOKEN MANAGEMENT")
    print("=" * 60)

    print("📋 Features:")
    print("   • Automatic token saving")
    print("   • Automatic token loading")
    print("   • Seamless reconnection")
    print("   • Zero configuration")

    # Get credentials
    email = input("\nEnter pCloud email: ").strip()
    password = input("Enter pCloud password: ").strip()

    if not email or not password:
        print("❌ Email and password required")
        return

    try:
        print("\n🔧 First login (will save token automatically)...")

        # First login - token will be saved
        sdk1 = PCloudSDK()  # Uses default token file
        sdk1.login(email, password)

        user_info = sdk1.user.get_user_info()
        print(f"✅ First login successful: {user_info.get('email')}")
        print(f"💾 Token automatically saved to: {sdk1.token_file}")

        # Simulate app restart - create new SDK instance
        print("\n🔄 Simulating app restart (new SDK instance)...")

        sdk2 = PCloudSDK()  # New instance
        sdk2.login()  # No credentials needed - uses saved token!

        user_info2 = sdk2.user.get_user_info()
        print(f"✅ Second login successful: {user_info2.get('email')}")
        print("🚀 No credentials needed - used saved token!")

        # Show credentials info
        creds_info = sdk2.get_credentials_info()
        print(f"\n📊 Token information:")
        print(f"   📅 Age: {creds_info.get('age_days', 0):.2f} days")
        print(f"   🕐 Last used: {creds_info.get('last_used', 'Unknown')}")

    except PCloudException as e:
        print(f"❌ Error: {e}")


def demonstrate_manual_token_management():
    """Demonstrate manual token extraction and management"""
    print("\n" + "=" * 60)
    print("2️⃣ MANUAL TOKEN MANAGEMENT")
    print("=" * 60)

    print("📋 Features:")
    print("   • Manual token extraction")
    print("   • Token storage control")
    print("   • Custom token files")
    print("   • Token validation")

    # Get credentials
    email = input("\nEnter pCloud email: ").strip()
    password = input("Enter pCloud password: ").strip()

    if not email or not password:
        print("❌ Email and password required")
        return

    try:
        print("\n🔧 Manual token extraction...")

        # Login and extract token manually
        sdk = PCloudSDK(token_manager=False)  # Disable auto token management
        login_result = sdk.login(email, password)

        # Extract token information
        access_token = sdk.app.access_token
        print(f"✅ Login successful")
        print(f"🔑 Access token: {access_token[:20]}...")

        # Save token manually to custom file
        token_data = {
            "access_token": access_token,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
        }

        custom_token_file = "custom_token.json"
        with open(custom_token_file, "w") as f:
            json.dump(token_data, f, indent=2)

        print(f"💾 Token saved manually to: {custom_token_file}")

        # Test reusing the manually saved token
        print("\n🔄 Testing manual token reuse...")

        with open(custom_token_file, "r") as f:
            saved_token_data = json.load(f)

        # Create new SDK with saved token
        sdk2 = PCloudSDK(
            access_token=saved_token_data["access_token"], token_manager=False
        )

        # Test API call
        user_info = sdk2.user.get_user_info()
        print(f"✅ Manual token reuse successful: {user_info.get('email')}")

        # Clean up
        os.remove(custom_token_file)
        print(f"🧹 Cleaned up: {custom_token_file}")

    except PCloudException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demonstrate_multi_account_management():
    """Demonstrate multi-account token management"""
    print("\n" + "=" * 60)
    print("3️⃣ MULTI-ACCOUNT MANAGEMENT")
    print("=" * 60)

    print("📋 Features:")
    print("   • Multiple account support")
    print("   • Account switching")
    print("   • Separate token files")
    print("   • Account validation")

    # Initialize token manager
    token_manager = TokenManager()

    print("\n👥 Multi-account setup (you can use the same credentials for demo)")

    # Add accounts
    accounts_to_add = []

    for i in range(1, 3):  # Add 2 accounts for demo
        print(f"\n📧 Account {i}:")
        email = input(f"  Email (or press Enter to skip): ").strip()

        if not email:
            print("  ⏭️ Skipping account")
            continue

        password = input(f"  Password: ").strip()
        name = (
            input(f"  Account nickname (default: Account{i}): ").strip()
            or f"Account{i}"
        )

        if email and password:
            accounts_to_add.append((name, email, password))

    if not accounts_to_add:
        print("❌ No accounts to add")
        return

    # Add accounts to manager
    for name, email, password in accounts_to_add:
        token_manager.add_account(name, email, password)

    # Demonstrate account management
    print("\n📋 Account management operations:")

    # List accounts
    token_manager.list_accounts()

    # Get current account info
    print("\n📊 Current account information:")
    current_info = token_manager.get_account_info()
    if current_info:
        print(f"   👤 Name: {current_info['name']}")
        print(f"   📧 Email: {current_info['email']}")
        print(f"   📅 Added: {current_info['added_at'][:10]}")
        print(f"   ⏰ Token age: {current_info['credentials_age_days']:.2f} days")
        print(f"   💾 Quota: {current_info['user_quota'] // (1024**3):.1f} GB")
        print(f"   📁 Used: {current_info['user_used_quota'] // (1024**3):.1f} GB")

    # Test API call with current account
    current_sdk = token_manager.get_current_sdk()
    if current_sdk:
        try:
            folders = current_sdk.folder.list_root()
            folder_count = len(
                [f for f in folders.get("contents", []) if f.get("isfolder")]
            )
            file_count = len(
                [f for f in folders.get("contents", []) if not f.get("isfolder")]
            )
            print(f"   📂 Root folder: {folder_count} folders, {file_count} files")
        except Exception as e:
            print(f"   ❌ API test failed: {e}")

    # Switch accounts if multiple
    if len(token_manager.accounts) > 1:
        print("\n🔄 Account switching demonstration:")
        account_names = list(token_manager.accounts.keys())
        for name in account_names:
            if name != token_manager.current_account:
                token_manager.switch_account(name)

                # Test API call with switched account
                sdk = token_manager.get_current_sdk()
                if sdk:
                    try:
                        user_info = sdk.user.get_user_info()
                        print(f"   ✅ API test with {name}: {user_info.get('email')}")
                    except Exception as e:
                        print(f"   ❌ API test with {name} failed: {e}")
                break

    # Validate all tokens
    print("\n🔍 Token validation:")
    token_manager.validate_all_tokens()

    # Cleanup demonstration
    print("\n🧹 Cleanup options:")
    cleanup_choice = input("Clean up demo accounts? (y/n): ").strip().lower()
    if cleanup_choice == "y":
        for name in list(token_manager.accounts.keys()):
            token_manager.remove_account(name)
        print("✅ All demo accounts cleaned up")


def demonstrate_token_security_practices():
    """Demonstrate token security best practices"""
    print("\n" + "=" * 60)
    print("4️⃣ TOKEN SECURITY BEST PRACTICES")
    print("=" * 60)

    print("📋 Security features:")
    print("   • Token file encryption")
    print("   • Automatic expiration")
    print("   • Secure file permissions")
    print("   • Token validation")

    # Get credentials
    email = input("\nEnter pCloud email: ").strip()
    password = input("Enter pCloud password: ").strip()

    if not email or not password:
        print("❌ Email and password required")
        return

    try:
        # Demonstrate secure token handling
        print("\n🔒 Secure token management demo...")

        # Create SDK with secure settings
        secure_token_file = ".secure_pcloud_token"
        sdk = PCloudSDK(token_file=secure_token_file)

        # Login and save token securely
        sdk.login(email, password)
        print("✅ Secure login completed")

        # Check file permissions
        if os.path.exists(secure_token_file):
            stat_info = os.stat(secure_token_file)
            permissions = oct(stat_info.st_mode)[-3:]
            print(f"🔒 Token file permissions: {permissions}")

            # Show file size (tokens are encrypted, so size may vary)
            file_size = stat_info.st_size
            print(f"📁 Token file size: {file_size} bytes")

        # Show token information without exposing actual token
        creds_info = sdk.get_credentials_info()
        print(f"\n🛡️ Security information:")
        print(f"   📅 Token age: {creds_info.get('age_days', 0):.2f} days")
        print(f"   ⏰ Last used: {creds_info.get('last_used', 'Unknown')}")
        print(f"   🔐 Token file: {secure_token_file}")

        # Demonstrate token validation
        print("\n✅ Token validation:")
        try:
            user_info = sdk.user.get_user_info()
            print(f"   ✅ Token is valid (user: {user_info.get('email')})")
        except PCloudException as e:
            print(f"   ❌ Token validation failed: {e}")

        # Demonstrate secure logout
        print("\n🚪 Secure logout (removes token file):")
        confirm_logout = input("   Perform secure logout? (y/n): ").strip().lower()
        if confirm_logout == "y":
            sdk.logout()

            if not os.path.exists(secure_token_file):
                print("   ✅ Token file securely removed")
            else:
                print("   ⚠️ Token file still exists")

        print("\n🛡️ Security best practices:")
        print("   1. Use automatic token management when possible")
        print("   2. Never store passwords in plain text")
        print("   3. Use secure file permissions for token files")
        print("   4. Regularly validate and refresh tokens")
        print("   5. Implement proper logout procedures")
        print("   6. Monitor token usage and age")

    except PCloudException as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main demonstration function"""
    print("🔑 pCloud SDK Token Management Examples")
    print("=" * 45)

    while True:
        print("\nChoose a demonstration:")
        print("1. Automatic token management")
        print("2. Manual token management")
        print("3. Multi-account management")
        print("4. Token security practices")
        print("5. Exit")

        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            demonstrate_automatic_token_management()
        elif choice == "2":
            demonstrate_manual_token_management()
        elif choice == "3":
            demonstrate_multi_account_management()
        elif choice == "4":
            demonstrate_token_security_practices()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()
