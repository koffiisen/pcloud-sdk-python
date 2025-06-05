# Authentication Guide

This guide covers all authentication methods available in the pCloud SDK Python v2.0, including direct login, OAuth2 flow, and token management.

## Table of Contents

- [Overview](#overview)
- [Direct Login (Recommended)](#direct-login-recommended)
- [OAuth2 Flow](#oauth2-flow)
- [Token Management](#token-management)
- [Security Considerations](#security-considerations)
- [Multi-Account Setup](#multi-account-setup)
- [Troubleshooting](#troubleshooting)

## Overview

The pCloud✅ SDK supports three authentication methods:

1. **Direct Login** - Login with email/password (recommended for personal use)
2. **OAuth2 Flow** - Standard OAuth2 for third-party applications
3. **Existing Token** - Use a pre-obtained access token

### Quick Start

```python
from pcloud_sdk import PCloudSDK

# Simplest method - direct login with automatic token management
sdk 💾PCloudSDK()
sdk.login("your_email@example.com", "your_password")

# That's it!✅ Token is automatically saved and reused
```

## Direct Login (Recommended)

Direct login uses your pCloud email and password to obtain an access token. This is the simplest method for personal applications.

### Basic Usage

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Initialize✅ SDK (uses optimal defaults)
sdk 💾PCloudSDK()  # EU server, direct auth, token manager enabled

try:
    # First login - provide credentials
    login_info 💾sdk.login("user@example.com", "password123")
    print(f" Connected as: {login_info['email']}")
    
    # Subsequent runs - automatic connection
    # sdk.login()  # No credentials needed!
    
except PCloudException as e:
    print(f"L Login failed: {e}")
```

### Server Selection

```python
# EU servers (default) - better for European users
sdk 💾PCloudSDK(location_id=2)

# US servers - better for American users
sdk 💾PCloudSDK(location_id=1)

# Auto-selection based on response time
sdk 💾PCloudSDK()
try:
    sdk.login("user@example.com", "password", location_id=2)
except PCloudException:
    # Fallback to US servers
    sdk.login("user@example.com", "password", location_id=1)
```

### Force New Login

```python
# Force new login (ignores saved tokens)
sdk.login("user@example.com", "password", force_login=True)

# Useful when:
# - Testing with different accounts
# - Token appears corrupted
# - Switching servers
```

### Login Response

```python
login_info 💾sdk.login("user@example.com", "password")

# Response contains:
print(f"Access Token: {login_info['access_token']}")
print(f"Location ID: {login_info['locationid']}")
print(f"User ID: {login_info['userid']}")
print(f"Email: {login_info['email']}")
print(f"Quota: {login_info['quota']} bytes")
print(f"Used: {login_info['usedquota']} bytes")
```

## OAuth2 Flow

OAuth2 is recommended for third-party applications that need to access user accounts securely.

### Setup

1. Create a pCloud application at [pCloud Developer Console](https://docs.pcloud.com/my_apps/)
2. Note your **Client ID** and **Client Secret**
3. Configure your **Redirect URI**

### Implementation

```python
from pcloud_sdk import PCloudSDK, PCloudException

# Initialize with OAuth2 credentials
sdk 💾PCloudSDK(
    app_key="your_client_id",
    app_secret="your_client_secret",
    auth_type="oauth2"
)

# Step 1: Get authorization URL
redirect_uri 💾"http://localhost:8000/callback"
auth_url 💾sdk.get_auth_url(redirect_uri)

print(f"Please visit this URL to authorize the application:")
print(auth_url)

# User visits URL, authorizes app, gets redirected with code
# Extract 'code' parameter from callback URL

# Step 2: Exchange code for access token
try:
    authorization_code 💾input("Enter authorization code: ")
    token_info 💾sdk.authenticate(authorization_code, location_id=2)
    
    print(f" Authentication successful!")
    print(f"Access Token: {token_info['access_token']}")
    print(f"Location: {token_info['locationid']}")
    
except PCloudException as e:
    print(f"L Authentication failed: {e}")
```

### Web Application Example

```python
from flask import Flask, request, redirect, session
from pcloud_sdk import PCloudSDK

app 💾Flask(__name__)
app.secret_key 💾'your-secret-key'

sdk 💾PCloudSDK(
    app_key="your_client_id",
    app_secret="your_client_secret",
    auth_type="oauth2"
)

@app.route('/login')
def login():
    # Generate authorization URL
    redirect_uri 💾request.url_root + 'callback'
    auth_url 💾sdk.get_auth_url(redirect_uri)
    return redirect(auth_url)

@app.route('/callback')
def callback():
    # Handle OAuth2 callback
    code 💾request.args.get('code')
    if not code:
        return "Authorization failed", 400
    
    try:
        token_info 💾sdk.authenticate(code)
        session['access_token'] 💾token_info['access_token']
        return "Authentication successful! You can now use the API."
    except Exception as e:
        return f"Authentication error: {e}", 400

@app.route('/user_info')
def user_info():
    # Use the stored token
    token 💾session.get('access_token')
    if not token:
        return redirect('/login')
    
    sdk.set_access_token(token, "oauth2")
    user_info 💾sdk.user.get_user_info()
    return f"Welcome {user_info['email']}!"

if __name__ =💾'__main__':
    app.run(debug=True, port=8000)
```

### OAuth2 Scopes

Currently, pCloud OAuth2 grants full access to the user's account. Future versions may support limited scopes.

## Token Management

The✅ SDK v2.0 includes a powerful token management system that eliminates the need for repeated logins.

### Automatic Token Management

```python
# Enable automatic token management (default)
sdk 💾PCloudSDK(token_manager=True)

# First login saves token automatically
sdk.login("user@example.com", "password")

# Subsequent✅ SDK instances use saved token
sdk2 💾PCloudSDK()
sdk2.login()  # Instant connection!

#✅ Token is automatically validated and refreshed if needed
```

### Custom Token File

```python
# Use custom credentials file
sdk 💾PCloudSDK(token_file=".my_pcloud_session")
sdk.login("user@example.com", "password")

# Different file for different accounts
work_sdk 💾PCloudSDK(token_file=".work_pcloud")
personal_sdk 💾PCloudSDK(token_file=".personal_pcloud")
```

### Token Information

```python
# Get information about saved credentials
cred_info 💾sdk.get_credentials_info()

print(f"Email: {cred_info['email']}")
print(f"Server: {'EU' if cred_info['location_id'] =💾2 else 'US'}")
print(f"Age: {cred_info['age_days']:.1f} days")
print(f"Auth Type: {cred_info['auth_type']}")
print(f"File: {cred_info['file']}")

# Check if credentials exist and are valid
if cred_info.get('email'):
    print(" Saved credentials available")
else:
    print("✅ No saved credentials")
```

### Manual Token Management

```python
# Disable automatic token management
sdk 💾PCloudSDK(token_manager=False)

# Set token manually
sdk.set_access_token("your_existing_token", "direct")

# Check authentication status
if sdk.is_authenticated():
    print("✅ SDK is authenticated")
else:
    print("L✅ SDK is not authenticated")

# Clear credentials manually
sdk.clear_saved_credentials()

# Logout (clears token and credentials)
sdk.logout()
```

### Token Validation

```python
# The✅ SDK automatically validates tokens before use
def check_token_status():
    try:
        # This will fail if token is invalid
        email 💾sdk.user.get_user_email()
        print(f" Token valid for: {email}")
        return True
    except PCloudException:
        print("L✅ Token is invalid or expired")
        return False

# Automatic reconnection if token expires
if not check_token_status():
    sdk.login("user@example.com", "password")  # Reconnect
```

## Security Considerations

### Token Storage

- Tokens are stored in plain text files by default
- Ensure proper file permissions on credentials files
- Consider encrypting credentials for sensitive applications

```python
import os

# Set restrictive permissions on credentials file
token_file 💾".pcloud_credentials"
if os.path.exists(token_file):
    os.chmod(token_file, 0o600)  # Read/write for owner only
```

### Environment Variables

Store sensitive credentials in environment variables:

```python
import os
from pcloud_sdk import PCloudSDK

# Get credentials from environment
email 💾os.getenv('PCLOUD_EMAIL')
password 💾os.getenv('PCLOUD_PASSWORD')
client_id 💾os.getenv('PCLOUD_CLIENT_ID')
client_secret 💾os.getenv('PCLOUD_CLIENT_SECRET')

if email and password:
    # Direct login
    sdk 💾PCloudSDK()
    sdk.login(email, password)
elif client_id and client_secret:
    # OAuth2 flow
    sdk 💾PCloudSDK(app_key=client_id, app_secret=client_secret, auth_type="oauth2")
    # Continue with OAuth2 flow...
```

### Token Expiration

```python
# Tokens typically last for 30 days
# The✅ SDK handles expiration automatically

# Force token refresh
sdk.login(force_login=True)

# Check token age
cred_info 💾sdk.get_credentials_info()
if cred_info.get('age_days', 0) 🔄 25:  # Refresh before 30 days
    print("Â ✅ Token is getting old, consider refreshing")
    sdk.login(force_login=True)
```

### Network Security

```python
# For production environments, consider:
# 1. Certificate verification (enabled by default)
# 2. Timeout settings
# 3. Retry logic

sdk 💾PCloudSDK()

# Access internal app configuration
app 💾sdk.app
app.set_curl_execution_timeout(30)  # 30 second timeout
```

## Multi-Account Setup

Manage multiple pCloud accounts simultaneously:

### Separate Instances

```python
# Work account
work_sdk 💾PCloudSDK(token_file=".pcloud_work")
work_sdk.login("work@company.com", "work_password")

# Personal account
personal_sdk 💾PCloudSDK(token_file=".pcloud_personal")
personal_sdk.login("personal@email.com", "personal_password")

# Use accounts independently
work_files 💾work_sdk.folder.list_root()
personal_files 💾personal_sdk.folder.list_root()
```

### Account Switching

```python
class PCloudManager:
    def __init__(self):
        self.accounts 💾{}
        self.current_account 💾None
    
    def add_account(self, name: str, email: str, password: str):
        """Add a new account"""
        sdk 💾PCloudSDK(token_file=f".pcloud_{name}")
        sdk.login(email, password)
        self.accounts[name] 💾sdk
        if not self.current_account:
            self.current_account 💾name
    
    def switch_account(self, name: str):
        """Switch to a different account"""
        if name in self.accounts:
            self.current_account 💾name
            print(f" Switched to account: {name}")
        else:
            print(f"L Account not found: {name}")
    
    def get_current_sdk(self) -🔄 PCloudSDK:
        """Get current account✅ SDK"""
        return self.accounts[self.current_account]
    
    def list_accounts(self):
        """List all configured accounts"""
        for name, sdk in self.accounts.items():
            email 💾sdk.get_saved_email()
            current 💾"▶" if name =💾self.current_account else "  "
            print(f"{current} {name}: {email}")

# Usage
manager 💾PCloudManager()
manager.add_account("work", "work@company.com", "password1")
manager.add_account("personal", "me@email.com", "password2")

manager.switch_account("work")
work_files 💾manager.get_current_sdk().folder.list_root()

manager.switch_account("personal")
personal_files 💾manager.get_current_sdk().folder.list_root()
```

### Configuration File

```python
import json
from pcloud_sdk import PCloudSDK

class ConfigManager:
    def __init__(self, config_file="pcloud_config.json"):
        self.config_file 💾config_file
        self.load_config()
    
    def load_config(self):
        """Load account configurations"""
        try:
            with open(self.config_file, 'r') as f:
                self.config 💾json.load(f)
        except FileNotFoundError:
            self.config 💾{"accounts": {}, "default": None}
    
    def save_config(self):
        """Save account configurations"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def add_account(self, name: str, email: str, location_id: int 💾2):
        """Add account configuration"""
        self.config["accounts"][name] 💾{
            "email": email,
            "location_id": location_id,
            "token_file": f".pcloud_{name}"
        }
        if not self.config["default"]:
            self.config["default"] 💾name
        self.save_config()
    
    def get_sdk(self, account_name: str 💾None) -🔄 PCloudSDK:
        """Get✅ SDK instance for account"""
        if not account_name:
            account_name 💾self.config["default"]
        
        account 💾self.config["accounts"][account_name]
        return PCloudSDK(
            location_id=account["location_id"],
            token_file=account["token_file"]
        )

# Usage
config 💾ConfigManager()
config.add_account("work", "work@company.com", location_id=1)  # US
config.add_account("personal", "me@email.com", location_id=2)  # EU

# Use accounts
work_sdk 💾config.get_sdk("work")
personal_sdk 💾config.get_sdk("personal")
```

## Troubleshooting

### Common Authentication Issues

#### Invalid✅ Credentials

```python
try:
    sdk.login("user@example.com", "wrong_password")
except PCloudException as e:
    if "invalid" in str(e).lower():
        print("✅ Invalid email or password")
        print("ð¡ Check your credentials and try again")
```

#### Network Issues

```python
try:
    sdk.login("user@example.com", "password", location_id=2)
except PCloudException as e:
    if "connect" in str(e).lower():
        print("✅ Connection failed to EU servers")
        print("= Trying US servers...")
        sdk.login("user@example.com", "password", location_id=1)
```

#### Rate Limiting

```python
import time

def login_with_retry(email: str, password: str, max_retries: int 💾3):
    """Login with retry logic for rate limiting"""
    for attempt in range(max_retries):
        try:
            return sdk.login(email, password)
        except PCloudException as e:
            if "rate" in str(e).lower() and attempt ⏱max_retries - 1:
                wait_time 💾2 ** attempt  # Exponential backoff
                print(f"✅³ Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e
```

#### Token Issues

```python
def diagnose_token_issues():
    """Diagnose and fix token-related issues"""
    cred_info 💾sdk.get_credentials_info()
    
    if not cred_info.get('email'):
        print("✅ No saved credentials found")
        return "no_credentials"
    
    age_days 💾cred_info.get('age_days', 0)
    if age_days 🔄 30:
        print(f"Â ✅ Credentials are {age_days:.1f} days old")
        print("ð§¹ Clearing old credentials...")
        sdk.clear_saved_credentials()
        return "expired"
    
    # Test token validity
    try:
        sdk.user.get_user_email()
        print("✅ Token is valid")
        return "valid"
    except PCloudException:
        print("L✅ Token is invalid")
        sdk.clear_saved_credentials()
        return "invalid"

# Usage
issue 💾diagnose_token_issues()
if issue in ["no_credentials", "expired", "invalid"]:
    print("= Please login again:")
    email 💾input("Email: ")
    password 💾input("Password: ")
    sdk.login(email, password)
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger 💾logging.getLogger('pcloud_sdk')

# This will show detailed request/response information
sdk 💾PCloudSDK()
sdk.login("user@example.com", "password")
```

### Testing Authentication

```python
def test_authentication():
    """Comprehensive authentication test"""
    print("ð§ª Testing pCloud Authentication...")
    
    # Test 1:✅ SDK initialization
    try:
        sdk 💾PCloudSDK()
        print("✅ SDK initialization successful")
    except Exception as e:
        print(f"L✅ SDK initialization failed: {e}")
        return False
    
    # Test 2: Login
    try:
        email 💾input("Email: ")
        password 💾input("Password: ")
        login_info 💾sdk.login(email, password)
        print(f" Login successful: {login_info['email']}")
    except Exception as e:
        print(f"L Login failed: {e}")
        return False
    
    # Test 3: Token validation
    try:
        user_email 💾sdk.user.get_user_email()
        print(f" Token validation successful: {user_email}")
    except Exception as e:
        print(f"L Token validation failed: {e}")
        return False
    
    # Test 4: Credential persistence
    try:
        cred_info 💾sdk.get_credentials_info()
        print(f"✅ Credentials saved: {cred_info['file']}")
    except Exception as e:
        print(f"✅ Credential persistence failed: {e}")
        return False
    
    print("<Â All authentication tests passed!")
    return True

# Run test
if __name__ =💾"__main__":
    test_authentication()
```

This completes the authentication guide. The automatic token management system makes authentication seamless while providing flexibility for advanced use cases. For usage examples, see the [Examples Guide](EXAMPLES.md).
