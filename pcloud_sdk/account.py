from typing import Optional, Dict, Any
import requests
import json
from urllib.parse import urlencode

from pcloud_sdk.config import Config
from pcloud_sdk.exceptions import PCloudException


class Account:
    """Represents a pCloud account and its authentication details."""

    def __init__(
        self,
        account_id: str,
        access_token: str = "",
        location_id: int = 1,  # Default to US
        auth_type: str = "oauth2",
        app_key: str = "",
        app_secret: str = "",
        redirect_uri: str = "",
        email: str = "",
        user_id: Optional[int] = None,
        quota: Optional[int] = None,
        used_quota: Optional[int] = None,
        is_authenticated: bool = False,
        curl_exec_timeout: int = 3600,  # Default timeout in seconds
    ):
        """
        Initializes an Account instance.

        Args:
            account_id: A unique identifier for the account (e.g., email or UUID).
            access_token: The access token for API authentication.
            location_id: The server location ID (1 for US, 2 for EU).
            auth_type: The authentication type (e.g., 'oauth2').
            app_key: The application key for OAuth.
            app_secret: The application secret for OAuth.
            redirect_uri: The redirect URI for OAuth.
            email: The user's email address.
            user_id: The user's unique ID.
            quota: The user's storage quota in bytes.
            used_quota: The user's used storage in bytes.
            is_authenticated: Boolean indicating if the account is authenticated.
            curl_exec_timeout: Timeout for cURL execution in seconds.
        """
        self.account_id = account_id
        self.access_token = access_token
        self.location_id = location_id
        self.auth_type = auth_type
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.email = email
        self.user_id = user_id
        self.quota = quota
        self.used_quota = used_quota
        self.is_authenticated = is_authenticated
        self.curl_exec_timeout = curl_exec_timeout

    def set_credentials(
        self, access_token: str, location_id: int, auth_type: str
    ) -> None:
        """
        Sets or updates the account's authentication credentials.

        Args:
            access_token: The new access token.
            location_id: The new server location ID.
            auth_type: The new authentication type.
        """
        self.access_token = access_token
        self.location_id = location_id
        self.auth_type = auth_type
        self.is_authenticated = True

    def set_user_details(
        self, email: str, user_id: int, quota: int, used_quota: int
    ) -> None:
        """
        Sets or updates user-specific details.

        Args:
            email: The user's email address.
            user_id: The user's unique ID.
            quota: The user's storage quota.
            used_quota: The user's used storage.
        """
        self.email = email
        self.user_id = user_id
        self.quota = quota
        self.used_quota = used_quota

    def clear_credentials(self) -> None:
        """Clears authentication credentials and user-specific details."""
        self.access_token = ""
        self.auth_type = "oauth2"  # Reset to default or keep as is?
        # self.location_id = 1 # Reset to default or keep as is?
        self.email = ""
        self.user_id = None
        self.quota = None
        self.used_quota = None
        self.is_authenticated = False

    def set_curl_exec_timeout(self, timeout: int) -> None:
        """
        Sets the cURL execution timeout.

        Args:
            timeout: The timeout in seconds.
        """
        self.curl_exec_timeout = timeout

    def get_info(self) -> dict:
        """
        Returns a dictionary representation of the account's details.

        Useful for saving account information to a file or for debugging.
        """
        return {
            "account_id": self.account_id,
            "access_token": self.access_token,
            "location_id": self.location_id,
            "auth_type": self.auth_type,
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "email": self.email,
            "user_id": self.user_id,
            "quota": self.quota,
            "used_quota": self.used_quota,
            "is_authenticated": self.is_authenticated,
            "curl_exec_timeout": self.curl_exec_timeout,
            # "saved_at": getattr(self, 'saved_at', 0) # Example if we add saved_at
        }

    def perform_direct_login(self, email: str, password: str, location_id: int) -> Dict[str, Any]:
        """
        Performs direct login (username/password) for this account.
        Updates account details on successful authentication.

        Args:
            email: The email for login.
            password: The password for login.
            location_id: The server location ID.

        Returns:
            The API response dictionary.

        Raises:
            PCloudException: If login fails or API returns an error.
        """
        api_host = Config.get_api_host_by_location_id(location_id)
        url = f"{api_host}userinfo"
        params = {
            "getauth": 1,
            "logout": 1,  # Ensure any previous session for this IP is cleared
            "username": email,
            "password": password,
        }

        try:
            response = requests.get(url, params=params, timeout=self.curl_exec_timeout)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise PCloudException(f"Network error during direct login: {e}")
        except json.JSONDecodeError:
            raise PCloudException(f"Failed to decode JSON response from direct login: {response.text}")

        if data.get("result") == 0 and "auth" in data:
            self.set_credentials(
                access_token=data["auth"],
                location_id=location_id, # Use the location_id provided for this successful login
                auth_type="direct",
            )
            self.set_user_details(
                email=data.get("email", email), # Prefer API email, fallback to provided
                user_id=data["userid"],
                quota=data["quota"],
                used_quota=data["usedquota"],
            )
            # self.is_authenticated = True # set_credentials already does this
            return data
        else:
            error_message = data.get("error", "Unknown error during direct login.")
            # Logout might return result 2009 if already logged out or invalid user.
            if data.get("result") == 2009 and "auth" not in data : # Specific error for bad credentials
                 raise PCloudException(f"Login failed: Invalid email or password. API Error: {error_message} (Result {data.get('result')})")
            raise PCloudException(f"Login failed: {error_message} (Result {data.get('result')})")

    def perform_oauth_exchange(self, code: str, location_id: int, app_key: str, app_secret: str) -> Dict[str, Any]:
        """
        Performs OAuth 2.0 code exchange for an access token.
        Updates account details on successful authentication.

        Args:
            code: The authorization code received from pCloud.
            location_id: The server location ID.
            app_key: The application's client_id.
            app_secret: The application's client_secret.

        Returns:
            The API response dictionary containing token information.

        Raises:
            PCloudException: If OAuth exchange fails or API returns an error.
        """
        api_host = Config.get_api_host_by_location_id(location_id)
        url = f"{api_host}oauth2_token"
        params = {
            "client_id": app_key,
            "client_secret": app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }
        if self.redirect_uri: # Add redirect_uri if it's set in the account
            params["redirect_uri"] = self.redirect_uri

        try:
            response = requests.get(url, params=params, timeout=self.curl_exec_timeout)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            raise PCloudException(f"Network error during OAuth exchange: {e}")
        except json.JSONDecodeError:
            raise PCloudException(f"Failed to decode JSON response from OAuth exchange: {response.text}")

        if "access_token" in data and data.get("access_token"):
            self.set_credentials(
                access_token=data["access_token"],
                location_id=data.get("locationid", location_id), # Prefer locationid from response
                auth_type="oauth2",
            )
            # OAuth response also includes userid and sometimes email
            if "userid" in data:
                self.user_id = data["userid"]
            if "email" in data and data["email"]: # Only update email if provided and not empty
                self.email = data["email"]

            # To fully populate user details like quota, a separate userinfo call would be needed
            # after OAuth. For now, only what's available from oauth2_token is set.
            # self.is_authenticated = True # set_credentials already does this
            return data
        else:
            error_message = data.get("error_description", data.get("error", "Unknown error during OAuth exchange."))
            raise PCloudException(f"OAuth exchange failed: {error_message}")
