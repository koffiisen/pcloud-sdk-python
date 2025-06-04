#!/usr/bin/env python3
"""
pCloud SDK OAuth2 Authentication Example
========================================

This example demonstrates how to implement OAuth2 authentication flow with the pCloud SDK.
OAuth2 is the recommended authentication method for production applications as it doesn't
require storing user passwords.

Prerequisites:
1. Register your app at https://docs.pcloud.com/
2. Get your Client ID (app_key) and Client Secret (app_secret)
3. Configure your redirect URI in your pCloud app settings

This example shows:
- OAuth2 flow setup and configuration
- Authorization URL generation
- Code exchange for tokens
- Token storage and reuse
- Error handling for OAuth2 specific issues
"""

import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
from typing import Optional, Dict, Any

from pcloud_sdk import PCloudSDK
from pcloud_sdk.exceptions import PCloudException


# Replace these with your actual pCloud app credentials
# Get them from: https://docs.pcloud.com/
PCLOUD_APP_KEY = "YOUR_CLIENT_ID_HERE"      # Your pCloud Client ID
PCLOUD_APP_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Your pCloud Client Secret
REDIRECT_URI = "http://localhost:8080/callback"  # Must match your app settings


class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth2 callback"""
    
    def do_GET(self):
        """Handle GET request from OAuth2 callback"""
        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Extract authorization code or error
        if 'code' in query_params:
            # Success - got authorization code
            self.server.auth_code = query_params['code'][0]
            self.server.auth_error = None
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
            <html>
            <head><title>pCloud OAuth2 Success</title></head>
            <body>
                <h1> Authorization Successful!</h1>
                <p>You can now close this window and return to the application.</p>
                <script>window.close();</script>
            </body>
            </html>
            """
            self.wfile.write(success_html.encode())
            
        elif 'error' in query_params:
            # Error in authorization
            error = query_params['error'][0]
            error_description = query_params.get('error_description', ['Unknown error'])[0]
            
            self.server.auth_code = None
            self.server.auth_error = f"{error}: {error_description}"
            
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <html>
            <head><title>pCloud OAuth2 Error</title></head>
            <body>
                <h1>L Authorization Failed</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description}</p>
                <p>Please close this window and try again.</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())
        
        else:
            # Unknown callback
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Invalid callback parameters")
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging"""
        pass


class OAuth2Server:
    """Simple HTTP server to handle OAuth2 callbacks"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the callback server"""
        try:
            self.server = HTTPServer(('localhost', self.port), OAuth2CallbackHandler)
            self.server.auth_code = None
            self.server.auth_error = None
            
            # Start server in a separate thread
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            
            print(f"< OAuth2 callback server started on http://localhost:{self.port}")
            return True
            
        except OSError as e:
            print(f"L Failed to start callback server on port {self.port}: {e}")
            return False
    
    def wait_for_callback(self, timeout: int = 300) -> tuple[Optional[str], Optional[str]]:
        """Wait for OAuth2 callback with timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.server:
                if self.server.auth_code:
                    return self.server.auth_code, None
                elif self.server.auth_error:
                    return None, self.server.auth_error
            
            time.sleep(0.5)
        
        return None, "Timeout waiting for authorization"
    
    def stop(self):
        """Stop the callback server"""
        if self.server:
            self.server.shutdown()
            print("=Ñ OAuth2 callback server stopped")


class PCloudOAuth2Example:
    """Complete OAuth2 authentication example"""
    
    def __init__(self, app_key: str, app_secret: str, redirect_uri: str):
        """Initialize OAuth2 example with app credentials"""
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.sdk: Optional[PCloudSDK] = None
        
    def setup_sdk(self) -> bool:
        """Initialize pCloud SDK for OAuth2"""
        try:
            self.sdk = PCloudSDK(
                app_key=self.app_key,
                app_secret=self.app_secret,
                location_id=2,  # EU server
                auth_type="oauth2",
                token_manager=True,
                token_file=".pcloud_oauth2_credentials"
            )
            
            print(" pCloud SDK initialized for OAuth2")
            return True
            
        except Exception as e:
            print(f"L Failed to initialize SDK: {e}")
            return False
    
    def check_existing_token(self) -> bool:
        """Check if we have a valid existing token"""
        if not self.sdk.is_authenticated():
            return False
        
        try:
            # Test the existing token
            user_info = self.sdk.user.get_user_info()
            email = user_info.get('email', 'Unknown')
            print(f" Found valid existing token for: {email}")
            return True
            
        except Exception as e:
            print(f"  Existing token invalid: {e}")
            return False
    
    def perform_oauth2_flow(self) -> bool:
        """Perform complete OAuth2 authorization flow"""
        print("\n= Starting OAuth2 Authorization Flow")
        print("-" * 40)
        
        # Start callback server
        oauth_server = OAuth2Server(8080)
        if not oauth_server.start():
            return False
        
        try:
            # Generate authorization URL
            print("= Generating authorization URL...")
            auth_url = self.sdk.get_auth_url(self.redirect_uri)
            
            print(f"=Í Authorization URL: {auth_url}")
            print("\n< Opening browser for authorization...")
            print("   Please authorize the application in your browser.")
            print("   If the browser doesn't open automatically, copy the URL above.")
            
            # Open browser automatically
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                print(f"  Could not open browser automatically: {e}")
                print("Please manually open the URL above in your browser.")
            
            # Wait for callback
            print("\nó Waiting for authorization callback...")
            auth_code, error = oauth_server.wait_for_callback(timeout=300)  # 5 minute timeout
            
            if error:
                print(f"L Authorization failed: {error}")
                return False
            
            if not auth_code:
                print("L No authorization code received")
                return False
            
            print(f" Authorization code received: {auth_code[:10]}...")
            
            # Exchange code for token
            print("\n= Exchanging authorization code for access token...")
            
            token_info = self.sdk.authenticate(auth_code, location_id=2)
            
            print(" OAuth2 authentication successful!")
            print(f"   Access Token: {token_info['access_token'][:20]}...")
            print(f"   Location ID: {token_info['locationid']}")
            
            return True
            
        except PCloudException as e:
            print(f"L OAuth2 authentication failed: {e}")
            return False
        except Exception as e:
            print(f"L Unexpected error during OAuth2 flow: {e}")
            return False
        finally:
            oauth_server.stop()
    
    def demonstrate_authenticated_operations(self):
        """Demonstrate operations with OAuth2 authenticated SDK"""
        print("\n=d Testing Authenticated Operations")
        print("-" * 40)
        
        try:
            # Get user information
            user_info = self.sdk.user.get_user_info()
            
            print(f"=ç Email: {user_info.get('email', 'N/A')}")
            print(f"<” User ID: {user_info.get('userid', 'N/A')}")
            
            quota = user_info.get('quota', 0)
            used_quota = user_info.get('usedquota', 0)
            
            print(f"=¾ Storage Used: {used_quota:,} bytes")
            print(f"=Ê Total Quota: {quota:,} bytes")
            print(f"=¿ Free Space: {quota - used_quota:,} bytes")
            
            # List root folder
            print("\n=Á Root folder contents (first 5 items):")
            root_contents = self.sdk.folder.get_content(path="/")
            
            for i, item in enumerate(root_contents[:5]):
                if item.get('isfolder'):
                    print(f"   =Á {item['name']}")
                else:
                    size = item.get('size', 0)
                    print(f"   =Ä {item['name']} ({size:,} bytes)")
            
            if len(root_contents) > 5:
                print(f"   ... and {len(root_contents) - 5} more items")
            
            print(" All operations completed successfully!")
            
        except Exception as e:
            print(f"L Error during operations: {e}")
    
    def show_token_info(self):
        """Display information about stored tokens"""
        print("\n= Token Information")
        print("-" * 40)
        
        cred_info = self.sdk.get_credentials_info()
        
        print(f"=Á Token File: {cred_info.get('file', 'N/A')}")
        print(f"=' Token Manager: {'Enabled' if cred_info.get('token_manager_enabled') else 'Disabled'}")
        
        if 'email' in cred_info:
            print(f"=ç Email: {cred_info['email']}")
            print(f"< Location: {'EU' if cred_info.get('location_id') == 2 else 'US'}")
            print(f"= Auth Type: {cred_info.get('auth_type', 'N/A')}")
            print(f"ð Token Age: {cred_info.get('age_days', 0):.1f} days")
        else:
            print("=Ë No saved credentials found")
    
    def clear_saved_tokens(self):
        """Clear saved OAuth2 tokens"""
        print("\n>ù Clearing Saved Tokens")
        print("-" * 40)
        
        try:
            self.sdk.clear_saved_credentials()
            print(" Saved tokens cleared successfully")
        except Exception as e:
            print(f"  Error clearing tokens: {e}")
    
    def run_example(self):
        """Run the complete OAuth2 example"""
        print("=€ pCloud SDK OAuth2 Authentication Example")
        print("=" * 50)
        
        # Validate credentials
        if self.app_key == "YOUR_CLIENT_ID_HERE" or self.app_secret == "YOUR_CLIENT_SECRET_HERE":
            print("L Please configure your pCloud app credentials first!")
            print("\n=Ý To get your credentials:")
            print("1. Visit https://docs.pcloud.com/")
            print("2. Register your application")
            print("3. Get your Client ID and Client Secret")
            print("4. Update PCLOUD_APP_KEY and PCLOUD_APP_SECRET in this script")
            print("5. Make sure your redirect URI matches: " + self.redirect_uri)
            return
        
        # Setup SDK
        if not self.setup_sdk():
            return
        
        # Check for existing valid token
        print("\n= Checking for existing authentication...")
        if self.check_existing_token():
            print(" Using existing valid token")
            use_existing = input("\nUse existing token? (Y/n): ").strip().lower()
            if use_existing in ['', 'y', 'yes']:
                self.demonstrate_authenticated_operations()
                self.show_token_info()
                return
            else:
                print("= Performing fresh OAuth2 flow...")
                self.clear_saved_tokens()
        
        # Perform OAuth2 flow
        if self.perform_oauth2_flow():
            self.demonstrate_authenticated_operations()
            self.show_token_info()
            
            print("\n<‰ OAuth2 example completed successfully!")
            print("\n=¡ Next time you run this script, it will use the saved token")
            print("   unless it has expired or you choose to get a new one.")
        else:
            print("\nL OAuth2 example failed")


def main():
    """Main function"""
    print("< Welcome to the pCloud SDK OAuth2 Example!")
    print("\nThis example demonstrates the complete OAuth2 authentication flow.")
    print("You'll need valid pCloud app credentials to proceed.")
    print()
    
    # Create and run example
    oauth_example = PCloudOAuth2Example(
        app_key=PCLOUD_APP_KEY,
        app_secret=PCLOUD_APP_SECRET,
        redirect_uri=REDIRECT_URI
    )
    
    oauth_example.run_example()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Example interrupted by user")
    except Exception as e:
        print(f"\nL Unexpected error: {e}")