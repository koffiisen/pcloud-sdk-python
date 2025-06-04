"""
pCloud SDK for Python
Converted from the PHP SDK

This package provides a Python interface to the pCloud API.
"""

import os
import time
from typing import Optional, Dict, Any

from pcloud_sdk.app import App
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.file_operations import File
from pcloud_sdk.folder_operations import Folder
from pcloud_sdk.user_operations import User


class PCloudSDK:
    """
    Convenient wrapper class for the pCloud SDK with integrated token management
    """

    def __init__(self, app_key: str = "", app_secret: str = "", access_token: str = "",
                 location_id: int = 2, auth_type: str = "direct",
                 token_manager: bool = True, token_file: str = ".pcloud_credentials"):
        """
        Initialize the pCloud SDK

        Args:
            app_key: Your pCloud app key (Client ID) - optional for direct login
            app_secret: Your pCloud app secret (Client Secret) - optional for direct login
            access_token: Access token (optional, can be set later)
            location_id: Server location (1=US, 2=EU) - default EU
            auth_type: Authentication type ("oauth2" or "direct") - default direct
            token_manager: Enable automatic token management (default True)
            token_file: File to store credentials (default .pcloud_credentials)
        """
        self.app = App()
        self.app.set_app_key(app_key)
        self.app.set_app_secret(app_secret)
        self.app.set_location_id(location_id)
        self.app.auth_type = auth_type

        # Token management
        self.token_manager_enabled = token_manager
        self.token_file = token_file
        self._saved_credentials = None

        if access_token:
            self.app.set_access_token(access_token, auth_type)
        elif token_manager:
            # Try to load existing credentials
            self._load_saved_credentials()

        self._user = None
        self._folder = None
        self._file = None

    def _save_credentials(self, email: str, token: str, location_id: int, user_info: Optional[Dict] = None):
        """Save credentials to file if token manager is enabled"""
        if not self.token_manager_enabled:
            return

        credentials = {
            "email": email,
            "access_token": token,
            "location_id": location_id,
            "auth_type": self.app.get_auth_type(),
            "user_info": user_info or {},
            "saved_at": time.time()
        }

        try:
            import json
            with open(self.token_file, 'w') as f:
                json.dump(credentials, f, indent=2)
            print(f"✅ Credentials sauvegardés dans {self.token_file}")
        except Exception as e:
            print(f"⚠️ Impossible de sauvegarder les credentials: {e}")

    def _load_saved_credentials(self) -> bool:
        """Load credentials from file if available"""
        if not self.token_manager_enabled or not os.path.exists(self.token_file):
            return False

        try:
            import json
            with open(self.token_file, 'r') as f:
                credentials = json.load(f)

            # Check if credentials are valid (not too old)
            saved_at = credentials.get('saved_at', 0)
            age_days = (time.time() - saved_at) / (24 * 3600)

            if age_days > 30:  # Consider credentials stale after 30 days
                print(f"⚠️ Credentials anciens ({age_days:.1f} jours), nouvelle connexion recommandée")
                return False

            # Set the loaded credentials
            self.app.set_access_token(credentials['access_token'], credentials.get('auth_type', 'direct'))
            self.app.set_location_id(credentials.get('location_id', 2))
            self._saved_credentials = credentials

            print(f"🔄 Credentials chargés: {credentials.get('email', 'Unknown')}")
            return True

        except Exception as e:
            print(f"⚠️ Impossible de charger les credentials: {e}")
            return False

    def _test_existing_credentials(self) -> bool:
        """Test if existing credentials still work"""
        if not self.app.get_access_token():
            return False

        try:
            # Quick test by getting user email
            user_email = self.user.get_user_email()
            print(f"✅ Credentials valides pour: {user_email}")
            return True
        except Exception:
            print("⚠️ Credentials expirés, nouvelle connexion requise")
            return False

    def clear_saved_credentials(self):
        """Clear saved credentials file"""
        if self.token_manager_enabled and os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
                print(f"🧹 Credentials supprimés de {self.token_file}")
            except Exception as e:
                print(f"⚠️ Erreur suppression credentials: {e}")
        self._saved_credentials = None

    def get_saved_email(self) -> Optional[str]:
        """Get the email from saved credentials"""
        if self._saved_credentials:
            return self._saved_credentials.get('email')
        return None

    @property
    def user(self) -> User:
        """Get User instance"""
        if self._user is None:
            self._user = User(self.app)
        return self._user

    @property
    def folder(self) -> Folder:
        """Get Folder instance"""
        if self._folder is None:
            self._folder = Folder(self.app)
        return self._folder

    @property
    def file(self) -> File:
        """Get File instance"""
        if self._file is None:
            self._file = File(self.app)
        return self._file

    def get_auth_url(self, redirect_uri: str = "") -> str:
        """Get OAuth2 authorization URL"""
        if redirect_uri:
            self.app.set_redirect_uri(redirect_uri)
        return self.app.get_authorize_code_url()

    def authenticate(self, code: str, location_id: int = 2) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        token_info = self.app.get_token_from_code(code, location_id)
        self.app.set_access_token(token_info["access_token"], "oauth2")
        self.app.set_location_id(token_info["locationid"])

        # Save credentials if token manager is enabled
        if self.token_manager_enabled:
            try:
                user_info = self.user.get_user_info()
                self._save_credentials(
                    email=user_info.get('email', ''),
                    token=token_info["access_token"],
                    location_id=token_info["locationid"],
                    user_info=user_info
                )
            except Exception as e:
                print(f"⚠️ Impossible de sauvegarder après OAuth2: {e}")

        return token_info

    def login(self, email: str = "", password: str = "", location_id: int = 2, force_login: bool = False) -> Dict[
        str, Any]:
        """
        Login with email/password or use saved credentials

        Args:
            email: pCloud email (optional if credentials are saved)
            password: pCloud password (optional if credentials are saved)
            location_id: Server location (1=US, 2=EU)
            force_login: Force new login even if credentials exist

        Returns:
            Dict containing login info
        """

        # Try to use existing credentials first (unless force_login)
        if not force_login and self.token_manager_enabled and self._saved_credentials:
            if self._test_existing_credentials():
                # Return info from saved credentials
                return {
                    "access_token": self.app.get_access_token(),
                    "locationid": self.app.get_location_id(),
                    "email": self._saved_credentials.get('email', ''),
                    "userid": self._saved_credentials.get('user_info', {}).get('userid'),
                    "quota": self._saved_credentials.get('user_info', {}).get('quota'),
                    "usedquota": self._saved_credentials.get('user_info', {}).get('usedquota')
                }

        # Need fresh login
        if not email or not password:
            saved_email = self.get_saved_email()
            if not email and saved_email:
                raise PCloudException(
                    f"Credentials expirés pour {saved_email}. Fournissez email et password pour reconnecter.")
            elif not email:
                raise PCloudException("Email et password requis pour la première connexion")

        print(f"🔐 Nouvelle connexion pour {email}...")
        login_info = self.app.login_with_credentials(email, password, location_id)

        # Save credentials if token manager is enabled
        if self.token_manager_enabled:
            try:
                user_info = self.user.get_user_info()
                self._save_credentials(
                    email=login_info['email'],
                    token=login_info['access_token'],
                    location_id=login_info['locationid'],
                    user_info=user_info
                )
            except Exception as e:
                print(f"⚠️ Impossible de sauvegarder les credentials: {e}")

        return login_info

    def login_or_load(self, email: str = "", password: str = "", location_id: int = 2,
                      force_login: bool = False) -> 'PCloudSDK':
        """
        Login or load existing credentials (for backward compatibility)
        """
        self.login(email, password, location_id, force_login)
        return self

    def set_access_token(self, access_token: str, auth_type: str = "direct"):
        """Set access token directly with authentication type"""
        self.app.set_access_token(access_token, auth_type)

    def is_authenticated(self) -> bool:
        """Check if SDK is authenticated"""
        return bool(self.app.get_access_token())

    def logout(self):
        """Logout and clear credentials"""
        self.clear_saved_credentials()
        self.app.set_access_token("", "direct")
        self._user = None
        self._folder = None
        self._file = None
        print("🚪 Déconnecté")

    def get_credentials_info(self) -> Dict[str, Any]:
        """Get information about current credentials"""
        if self._saved_credentials:
            saved_at = self._saved_credentials.get('saved_at', 0)
            age_days = (time.time() - saved_at) / (24 * 3600)

            return {
                "email": self._saved_credentials.get('email'),
                "location_id": self._saved_credentials.get('location_id'),
                "auth_type": self._saved_credentials.get('auth_type'),
                "age_days": age_days,
                "file": self.token_file,
                "token_manager_enabled": self.token_manager_enabled
            }

        return {
            "authenticated": self.is_authenticated(),
            "token_manager_enabled": self.token_manager_enabled,
            "file": self.token_file
        }
