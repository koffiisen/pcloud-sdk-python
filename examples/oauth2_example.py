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

from pcloud_sdk import PCloudSDK, PCloudException


class OAuth2CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth2 callback"""

    def do_GET(self):
        """Handle GET request for OAuth2 callback"""
        # Parse the callback URL
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Extract authorization code or error
        if "code" in query_params:
            self.server.auth_code = query_params["code"][0]
            response = """
            <html>
            <head><title>pCloud OAuth2 - Success</title></head>
            <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to your application.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
            """
        elif "error" in query_params:
            self.server.auth_error = query_params["error"][0]
            error_description = query_params.get(
                "error_description", ["Unknown error"]
            )[0]
            response = f"""
            <html>
            <head><title>pCloud OAuth2 - Error</title></head>
            <body>
                <h1>❌ Authorization Failed</h1>
                <p>Error: {query_params['error'][0]}</p>
                <p>Description: {error_description}</p>
                <p>You can close this window.</p>
            </body>
            </html>
            """
        else:
            response = """
            <html>
            <head><title>pCloud OAuth2 - Invalid Request</title></head>
            <body>
                <h1>⚠️ Invalid Request</h1>
                <p>No authorization code or error received.</p>
            </body>
            </html>
            """

        # Send response
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(response.encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class OAuth2FlowManager:
    """Manages OAuth2 authentication flow"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback",
    ):
        """
        Initialize OAuth2 flow manager

        Args:
            client_id: Your pCloud app client ID
            client_secret: Your pCloud app client secret
            redirect_uri: Redirect URI (must match app settings)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.server = None
        self.server_thread = None

    def start_callback_server(self, port: int = 8080) -> bool:
        """Start local server to handle OAuth2 callback"""
        try:
            self.server = HTTPServer(("localhost", port), OAuth2CallbackHandler)
            self.server.auth_code = None
            self.server.auth_error = None

            # Start server in separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()

            print(f"🌐 OAuth2 callback server started on http://localhost:{port}")
            return True

        except Exception as e:
            print(f"❌ Failed to start callback server: {e}")
            return False

    def stop_callback_server(self):
        """Stop the callback server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=1)
            print("🛑 OAuth2 callback server stopped")

    def get_authorization_url(self) -> str:
        """Generate OAuth2 authorization URL"""
        base_url = "https://my.pcloud.com/oauth2/authorize"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": "pcloud_sdk_example",  # Optional: add CSRF protection
        }

        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"

    def wait_for_callback(self, timeout: int = 300) -> Optional[str]:
        """
        Wait for OAuth2 callback with authorization code

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Authorization code or None if timeout/error
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if hasattr(self.server, "auth_code") and self.server.auth_code:
                return self.server.auth_code

            if hasattr(self.server, "auth_error") and self.server.auth_error:
                print(f"❌ OAuth2 authorization error: {self.server.auth_error}")
                return None

            time.sleep(0.5)

        print("⏰ Timeout waiting for OAuth2 callback")
        return None

    def exchange_code_for_token(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token

        Args:
            auth_code: Authorization code from callback

        Returns:
            Token information or None if failed
        """
        try:
            # Initialize SDK for token exchange
            sdk = PCloudSDK(
                app_key=self.client_id,
                app_secret=self.client_secret,
                auth_type="oauth2",
            )

            # Exchange code for token
            token_info = sdk.authenticate(auth_code)

            print("✅ Successfully exchanged code for access token")
            return token_info

        except PCloudException as e:
            print(f"❌ Failed to exchange code for token: {e}")
            return None


def oauth2_flow_example():
    """Complete OAuth2 flow example"""
    print("🔐 pCloud SDK OAuth2 Authentication Example")
    print("=" * 50)

    # Configuration (replace with your actual app credentials)
    CLIENT_ID = input("Enter your pCloud Client ID (App Key): ").strip()
    CLIENT_SECRET = input("Enter your pCloud Client Secret (App Secret): ").strip()

    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Client ID and Client Secret are required")
        return

    # Initialize OAuth2 flow manager
    oauth_manager = OAuth2FlowManager(CLIENT_ID, CLIENT_SECRET)

    try:
        # Step 1: Start callback server
        print("\n1️⃣ Starting OAuth2 callback server...")
        if not oauth_manager.start_callback_server():
            return

        # Step 2: Generate authorization URL
        print("\n2️⃣ Generating authorization URL...")
        auth_url = oauth_manager.get_authorization_url()
        print(f"🔗 Authorization URL: {auth_url}")

        # Step 3: Open browser (optional)
        try:
            print("\n3️⃣ Opening browser for authorization...")
            webbrowser.open(auth_url)
            print("🌐 Browser opened. Please authorize the application.")
        except Exception as e:
            print(f"⚠️ Could not open browser automatically: {e}")
            print(f"📋 Please manually visit: {auth_url}")

        # Step 4: Wait for callback
        print("\n4️⃣ Waiting for authorization callback...")
        print("   (Complete the authorization in your browser)")

        auth_code = oauth_manager.wait_for_callback(timeout=300)  # 5 minutes

        if not auth_code:
            print("❌ Failed to receive authorization code")
            return

        print(f"✅ Received authorization code: {auth_code[:10]}...")

        # Step 5: Exchange code for token
        print("\n5️⃣ Exchanging code for access token...")
        token_info = oauth_manager.exchange_code_for_token(auth_code)

        if not token_info:
            print("❌ Failed to get access token")
            return

        print(f"✅ Access token received: {token_info['access_token'][:20]}...")

        # Step 6: Test the token with API calls
        print("\n6️⃣ Testing token with API calls...")

        try:
            # Initialize SDK with the token
            sdk = PCloudSDK(
                access_token=token_info["access_token"],
                auth_type="direct",
                token_manager=False,  # Disable auto-save for this example
            )

            # Test API call
            user_info = sdk.user.get_user_info()
            print(f"👤 Successfully authenticated as: {user_info.get('email')}")
            print(f"💾 Account quota: {user_info.get('quota', 0) // (1024**3):.1f} GB")

            # Optional: Save token for later use
            save_token = input("\n💾 Save token for later use? (y/n): ").strip().lower()
            if save_token == "y":
                token_file = "oauth2_token.json"
                with open(token_file, "w") as f:
                    import json

                    json.dump(token_info, f, indent=2)
                print(f"💾 Token saved to {token_file}")
                print("   You can use this token for future authentication")

        except PCloudException as e:
            print(f"❌ API test failed: {e}")

        print("\n🎉 OAuth2 flow completed successfully!")

    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Clean up
        oauth_manager.stop_callback_server()


def reuse_saved_token_example():
    """Example of reusing a saved OAuth2 token"""
    print("\n🔄 Reusing Saved OAuth2 Token Example")
    print("=" * 40)

    token_file = "oauth2_token.json"

    try:
        # Load saved token
        with open(token_file, "r") as f:
            import json

            token_info = json.load(f)

        print(f"📂 Loaded token from {token_file}")

        # Initialize SDK with saved token
        sdk = PCloudSDK(
            access_token=token_info["access_token"],
            auth_type="direct",
            token_manager=False,
        )

        # Test API call
        user_info = sdk.user.get_user_info()
        print(f"✅ Token still valid")
        print(f"👤 User: {user_info.get('email')}")

    except FileNotFoundError:
        print(f"❌ Token file {token_file} not found")
        print("   Run the OAuth2 flow first and save the token")
    except PCloudException as e:
        print(f"❌ Token appears to be invalid: {e}")
        print("   You may need to re-authenticate")
    except Exception as e:
        print(f"❌ Error loading token: {e}")


def main():
    """Main example function"""
    print("🚀 pCloud SDK OAuth2 Examples")
    print("=" * 35)

    while True:
        print("\nChoose an example:")
        print("1. Complete OAuth2 flow")
        print("2. Reuse saved token")
        print("3. Exit")

        choice = input("Enter choice (1-3): ").strip()

        if choice == "1":
            oauth2_flow_example()
        elif choice == "2":
            reuse_saved_token_example()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
