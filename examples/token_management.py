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

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from pcloud_sdk import PCloudSDK
from pcloud_sdk.exceptions import PCloudException


class TokenManager:
    """Advanced token management utility"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.accounts: Dict[str, Dict] = {}
        
    def save_account_token(self, email: str, token_data: Dict, custom_filename: Optional[str] = None) -> str:
        """Save token for a specific account"""
        if custom_filename:
            token_file = os.path.join(self.base_dir, custom_filename)
        else:
            # Create safe filename from email
            safe_email = email.replace('@', '_at_').replace('.', '_dot_')
            token_file = os.path.join(self.base_dir, f".pcloud_token_{safe_email}")
        
        # Add metadata
        token_data.update({
            'email': email,
            'saved_at': time.time(),
            'saved_date': datetime.now().isoformat()
        })
        
        try:
            with open(token_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            self.accounts[email] = {
                'file': token_file,
                'data': token_data
            }
            
            print(f" Token saved for {email} in {token_file}")
            return token_file
            
        except Exception as e:
            print(f"L Failed to save token for {email}: {e}")
            raise
    
    def load_account_token(self, email: str) -> Optional[Dict]:
        """Load token for a specific account"""
        if email in self.accounts:
            token_file = self.accounts[email]['file']
        else:
            # Try to find token file
            safe_email = email.replace('@', '_at_').replace('.', '_dot_')
            token_file = os.path.join(self.base_dir, f".pcloud_token_{safe_email}")
        
        if not os.path.exists(token_file):
            return None
        
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            self.accounts[email] = {
                'file': token_file,
                'data': token_data
            }
            
            return token_data
            
        except Exception as e:
            print(f"  Error loading token for {email}: {e}")
            return None
    
    def list_saved_accounts(self) -> List[Dict]:
        """List all saved accounts"""
        accounts = []
        
        # Scan directory for token files
        for filename in os.listdir(self.base_dir):
            if filename.startswith('.pcloud_token_') or filename.startswith('.pcloud_'):
                filepath = os.path.join(self.base_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    email = data.get('email', 'Unknown')
                    saved_at = data.get('saved_at', 0)
                    age_days = (time.time() - saved_at) / (24 * 3600) if saved_at else 999
                    
                    accounts.append({
                        'email': email,
                        'file': filepath,
                        'age_days': age_days,
                        'location': 'EU' if data.get('location_id') == 2 else 'US',
                        'auth_type': data.get('auth_type', 'unknown')
                    })
                    
                except Exception:
                    continue
        
        return sorted(accounts, key=lambda x: x['age_days'])
    
    def validate_token(self, email: str) -> bool:
        """Validate if saved token is still valid"""
        token_data = self.load_account_token(email)
        if not token_data:
            return False
        
        try:
            # Create temporary SDK instance to test token
            sdk = PCloudSDK(
                access_token=token_data.get('access_token', ''),
                location_id=token_data.get('location_id', 2),
                auth_type=token_data.get('auth_type', 'direct'),
                token_manager=False  # Don't interfere with existing files
            )
            
            # Test token by getting user info
            user_info = sdk.user.get_user_info()
            return user_info.get('email') == email
            
        except Exception:
            return False
    
    def cleanup_invalid_tokens(self) -> List[str]:
        """Remove invalid/expired tokens"""
        accounts = self.list_saved_accounts()
        removed = []
        
        for account in accounts:
            if not self.validate_token(account['email']):
                try:
                    os.remove(account['file'])
                    removed.append(account['email'])
                    print(f"=Ñ Removed invalid token for {account['email']}")
                except Exception as e:
                    print(f"  Could not remove {account['file']}: {e}")
        
        return removed
    
    def get_token_info(self, email: str) -> Optional[Dict]:
        """Get detailed token information"""
        token_data = self.load_account_token(email)
        if not token_data:
            return None
        
        saved_at = token_data.get('saved_at', 0)
        age_days = (time.time() - saved_at) / (24 * 3600) if saved_at else 999
        
        return {
            'email': email,
            'location': 'EU' if token_data.get('location_id') == 2 else 'US',
            'auth_type': token_data.get('auth_type', 'unknown'),
            'age_days': age_days,
            'is_valid': self.validate_token(email),
            'user_info': token_data.get('user_info', {}),
            'saved_date': token_data.get('saved_date', 'Unknown')
        }


class MultiAccountManager:
    """Manage multiple pCloud accounts"""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.current_account: Optional[str] = None
        self.sdk: Optional[PCloudSDK] = None
    
    def add_account(self, email: str, password: str, location_id: int = 2) -> bool:
        """Add a new account with credentials"""
        print(f"• Adding account: {email}")
        
        try:
            # Create SDK instance for authentication
            sdk = PCloudSDK(
                location_id=location_id,
                token_manager=False  # We'll manage tokens manually
            )
            
            # Login to get token
            login_info = sdk.login(email, password, location_id)
            
            # Get user info
            user_info = sdk.user.get_user_info()
            
            # Save token data
            token_data = {
                'access_token': login_info['access_token'],
                'location_id': login_info['locationid'],
                'auth_type': 'direct',
                'user_info': user_info
            }
            
            self.token_manager.save_account_token(email, token_data)
            print(f" Account {email} added successfully")
            return True
            
        except Exception as e:
            print(f"L Failed to add account {email}: {e}")
            return False
    
    def switch_account(self, email: str) -> bool:
        """Switch to a different account"""
        print(f"= Switching to account: {email}")
        
        token_data = self.token_manager.load_account_token(email)
        if not token_data:
            print(f"L No saved token found for {email}")
            return False
        
        # Validate token first
        if not self.token_manager.validate_token(email):
            print(f"L Token for {email} is invalid or expired")
            return False
        
        try:
            # Create new SDK instance with the account's token
            self.sdk = PCloudSDK(
                access_token=token_data['access_token'],
                location_id=token_data.get('location_id', 2),
                auth_type=token_data.get('auth_type', 'direct'),
                token_manager=False
            )
            
            self.current_account = email
            print(f" Switched to account: {email}")
            return True
            
        except Exception as e:
            print(f"L Failed to switch to {email}: {e}")
            return False
    
    def list_accounts(self):
        """List all managed accounts"""
        accounts = self.token_manager.list_saved_accounts()
        
        if not accounts:
            print("=í No saved accounts found")
            return
        
        print(f"\n=e Saved Accounts ({len(accounts)}):")
        print("-" * 60)
        
        for account in accounts:
            status = " Valid" if self.token_manager.validate_token(account['email']) else "L Invalid"
            current_marker = " =H CURRENT" if account['email'] == self.current_account else ""
            
            print(f"=ç {account['email']}{current_marker}")
            print(f"   Status: {status}")
            print(f"   Location: {account['location']}")
            print(f"   Auth Type: {account['auth_type']}")
            print(f"   Age: {account['age_days']:.1f} days")
            print(f"   File: {os.path.basename(account['file'])}")
            print()
    
    def get_current_account_info(self) -> Optional[Dict]:
        """Get current account information"""
        if not self.current_account or not self.sdk:
            return None
        
        try:
            user_info = self.sdk.user.get_user_info()
            token_info = self.token_manager.get_token_info(self.current_account)
            
            return {
                'email': self.current_account,
                'user_info': user_info,
                'token_info': token_info
            }
        except Exception as e:
            print(f"  Error getting current account info: {e}")
            return None
    
    def remove_account(self, email: str) -> bool:
        """Remove an account and its token"""
        accounts = self.token_manager.list_saved_accounts()
        account = next((acc for acc in accounts if acc['email'] == email), None)
        
        if not account:
            print(f"L Account {email} not found")
            return False
        
        try:
            os.remove(account['file'])
            print(f"=Ñ Removed account: {email}")
            
            if self.current_account == email:
                self.current_account = None
                self.sdk = None
                print("  Removed current account - no account selected")
            
            return True
            
        except Exception as e:
            print(f"L Failed to remove {email}: {e}")
            return False


class TokenManagementDemo:
    """Complete token management demonstration"""
    
    def __init__(self):
        self.token_manager = TokenManager()
        self.multi_account = MultiAccountManager()
        
    def demo_basic_token_management(self):
        """Demonstrate basic token management"""
        print("1ã BASIC TOKEN MANAGEMENT")
        print("=" * 40)
        
        # Show how automatic token management works
        print("=' Creating SDK with automatic token management...")
        
        sdk = PCloudSDK(
            location_id=2,
            token_manager=True,
            token_file=".pcloud_demo_basic"
        )
        
        # Check if we have existing credentials
        if sdk.is_authenticated():
            print(" Found existing credentials")
            
            # Test them
            try:
                if sdk._test_existing_credentials():
                    email = sdk.get_saved_email()
                    print(f" Valid credentials for: {email}")
                    
                    # Show credential info
                    cred_info = sdk.get_credentials_info()
                    print("\n=Ë Credential Information:")
                    for key, value in cred_info.items():
                        print(f"   {key}: {value}")
                    
                    return sdk
            except Exception as e:
                print(f"  Credential test failed: {e}")
        
        # Need new authentication
        print("\n= New authentication required")
        email = input("=ç Enter pCloud email: ").strip()
        password = input("= Enter password: ").strip()
        
        try:
            sdk.login(email, password)
            print(" Authentication successful and token saved!")
            return sdk
            
        except Exception as e:
            print(f"L Authentication failed: {e}")
            return None
    
    def demo_manual_token_management(self):
        """Demonstrate manual token handling"""
        print("\n2ã MANUAL TOKEN MANAGEMENT")
        print("=" * 40)
        
        print("=' Manual token extraction and storage...")
        
        # Get saved accounts
        accounts = self.token_manager.list_saved_accounts()
        
        if accounts:
            print(f"\n=Ë Found {len(accounts)} saved accounts:")
            for i, account in enumerate(accounts, 1):
                status = "" if self.token_manager.validate_token(account['email']) else "L"
                print(f"   {i}. {account['email']} {status}")
            
            # Let user choose
            try:
                choice = int(input(f"\nSelect account (1-{len(accounts)}) or 0 for new: "))
                
                if 1 <= choice <= len(accounts):
                    selected_account = accounts[choice - 1]
                    email = selected_account['email']
                    
                    print(f"\n= Loading token for {email}...")
                    token_data = self.token_manager.load_account_token(email)
                    
                    if token_data:
                        print(" Token loaded successfully")
                        
                        # Create SDK with manual token
                        sdk = PCloudSDK(
                            access_token=token_data['access_token'],
                            location_id=token_data.get('location_id', 2),
                            auth_type=token_data.get('auth_type', 'direct'),
                            token_manager=False  # Manual management
                        )
                        
                        # Test the token
                        try:
                            user_info = sdk.user.get_user_info()
                            print(f" Token valid for: {user_info['email']}")
                            return sdk
                        except Exception as e:
                            print(f"L Token invalid: {e}")
                    
            except ValueError:
                print("L Invalid choice")
        
        return None
    
    def demo_multi_account_management(self):
        """Demonstrate multi-account management"""
        print("\n3ã MULTI-ACCOUNT MANAGEMENT")
        print("=" * 40)
        
        while True:
            print("\n=e Multi-Account Manager")
            print("1. List accounts")
            print("2. Add account") 
            print("3. Switch account")
            print("4. Remove account")
            print("5. Current account info")
            print("6. Validate all tokens")
            print("0. Exit multi-account demo")
            
            choice = input("\nEnter choice: ").strip()
            
            if choice == '1':
                self.multi_account.list_accounts()
                
            elif choice == '2':
                email = input("=ç Email: ").strip()
                password = input("= Password: ").strip()
                location = input("< Location (1=US, 2=EU) [2]: ").strip() or "2"
                
                try:
                    location_id = int(location)
                    self.multi_account.add_account(email, password, location_id)
                except ValueError:
                    print("L Invalid location")
                
            elif choice == '3':
                accounts = self.token_manager.list_saved_accounts()
                if not accounts:
                    print("L No accounts available")
                    continue
                
                print("\nAvailable accounts:")
                for i, account in enumerate(accounts, 1):
                    print(f"   {i}. {account['email']}")
                
                try:
                    acc_choice = int(input("Select account: "))
                    if 1 <= acc_choice <= len(accounts):
                        email = accounts[acc_choice - 1]['email']
                        self.multi_account.switch_account(email)
                except ValueError:
                    print("L Invalid choice")
                
            elif choice == '4':
                email = input("=ç Email to remove: ").strip()
                if email:
                    confirm = input(f"  Really remove {email}? (y/N): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        self.multi_account.remove_account(email)
                
            elif choice == '5':
                info = self.multi_account.get_current_account_info()
                if info:
                    print(f"\n=d Current Account: {info['email']}")
                    user_info = info['user_info']
                    print(f"   User ID: {user_info.get('userid')}")
                    print(f"   Quota: {user_info.get('quota', 0):,} bytes")
                    print(f"   Used: {user_info.get('usedquota', 0):,} bytes")
                else:
                    print("L No current account")
                
            elif choice == '6':
                print("\n= Validating all saved tokens...")
                accounts = self.token_manager.list_saved_accounts()
                
                for account in accounts:
                    is_valid = self.token_manager.validate_token(account['email'])
                    status = " Valid" if is_valid else "L Invalid"
                    print(f"   {account['email']}: {status}")
                
            elif choice == '0':
                break
                
            else:
                print("L Invalid choice")
    
    def demo_token_security_practices(self):
        """Demonstrate security best practices"""
        print("\n4ã SECURITY BEST PRACTICES")
        print("=" * 40)
        
        print("= Security recommendations for token management:")
        print()
        
        print(" DO:")
        print("   " Use automatic token management for convenience")
        print("   " Store tokens in secure, user-specific directories") 
        print("   " Validate tokens before use")
        print("   " Set appropriate file permissions (600)")
        print("   " Use different token files for different environments")
        print("   " Implement token rotation for long-running applications")
        print()
        
        print("L DON'T:")
        print("   " Store tokens in version control")
        print("   " Use same token file for multiple applications")
        print("   " Ignore token validation errors")
        print("   " Store tokens in world-readable locations")
        print("   " Hardcode tokens in source code")
        print()
        
        # Demonstrate file permission check
        accounts = self.token_manager.list_saved_accounts()
        if accounts:
            print("= Checking file permissions for saved tokens:")
            
            for account in accounts:
                file_path = account['file']
                if os.path.exists(file_path):
                    # Check file permissions
                    file_stat = os.stat(file_path)
                    permissions = oct(file_stat.st_mode)[-3:]
                    
                    if permissions == '600':
                        status = " Secure (600)"
                    elif permissions in ['644', '664']:
                        status = "  Readable by others"
                    else:
                        status = f"S Permissions: {permissions}"
                    
                    print(f"   {os.path.basename(file_path)}: {status}")
    
    def demo_token_cleanup(self):
        """Demonstrate token cleanup"""
        print("\n5ã TOKEN CLEANUP")
        print("=" * 40)
        
        print(">ù Token cleanup operations...")
        
        # List all tokens with their status
        accounts = self.token_manager.list_saved_accounts()
        
        if not accounts:
            print("=í No tokens found to clean up")
            return
        
        print(f"\n=Ë Found {len(accounts)} token files:")
        
        valid_count = 0
        invalid_count = 0
        
        for account in accounts:
            is_valid = self.token_manager.validate_token(account['email'])
            if is_valid:
                valid_count += 1
                print(f"    {account['email']} (valid)")
            else:
                invalid_count += 1
                print(f"   L {account['email']} (invalid/expired)")
        
        print(f"\n=Ê Summary: {valid_count} valid, {invalid_count} invalid")
        
        if invalid_count > 0:
            cleanup = input(f"\n=Ñ Remove {invalid_count} invalid tokens? (y/N): ").strip().lower()
            if cleanup in ['y', 'yes']:
                removed = self.token_manager.cleanup_invalid_tokens()
                print(f" Cleaned up {len(removed)} invalid tokens")
    
    def run_demo(self):
        """Run the complete token management demo"""
        print("=€ pCloud SDK Token Management Examples")
        print("=" * 50)
        
        try:
            # Run all demonstrations
            self.demo_basic_token_management()
            self.demo_manual_token_management()
            self.demo_multi_account_management()
            self.demo_token_security_practices()
            self.demo_token_cleanup()
            
            print("\n<‰ Token management demo completed!")
            
        except KeyboardInterrupt:
            print("\n  Demo interrupted by user")
        except Exception as e:
            print(f"\nL Demo failed: {e}")


def main():
    """Main function"""
    print("< Welcome to the pCloud SDK Token Management Examples!")
    print()
    print("This comprehensive demo covers:")
    print("" Automatic vs manual token management")
    print("" Multi-account handling")
    print("" Token validation and cleanup")
    print("" Security best practices")
    print("" Real-world usage patterns")
    print()
    
    proceed = input("Continue with the token management demo? (y/N): ").strip().lower()
    if proceed not in ['y', 'yes']:
        print("Demo cancelled.")
        return
    
    # Run the demo
    demo = TokenManagementDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()