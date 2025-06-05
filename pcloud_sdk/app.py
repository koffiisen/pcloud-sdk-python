import json
from typing import Any, Dict, List, Union
from urllib.parse import urlencode

import requests

from pcloud_sdk.config import Config
from pcloud_sdk.exceptions import PCloudException


class App:
    """Main App class for pCloud SDK"""

    def __init__(self) -> None:
        self.app_key = ""
        self.app_secret = ""
        self.redirect_uri = ""
        self.access_token = ""
        self.location_id = 1  # 1 = USA, 2 = EU
        self.curl_exec_timeout = 3600
        self.auth_type = "oauth2"  # "oauth2" ou "direct"

    def set_app_key(self, app_key: str) -> None:
        """Set App key (Client ID)"""
        self.app_key = app_key.strip()

    def get_app_key(self) -> str:
        """Get App key"""
        return self.app_key

    def set_app_secret(self, app_secret: str) -> None:
        """Set App secret (Client secret)"""
        self.app_secret = app_secret.strip()

    def get_app_secret(self) -> str:
        """Get App secret"""
        return self.app_secret

    def set_redirect_uri(self, redirect_uri: str) -> None:
        """Set redirect URI"""
        self.redirect_uri = redirect_uri.strip()

    def get_redirect_uri(self) -> str:
        """Get redirect URI"""
        return self.redirect_uri

    def set_access_token(self, access_token: str, auth_type: str = "oauth2") -> None:
        """Set access token and authentication type"""
        self.access_token = access_token.strip()
        self.auth_type = auth_type

    def get_access_token(self) -> str:
        """Get access token"""
        return self.access_token

    def get_auth_type(self) -> str:
        """Get authentication type"""
        return self.auth_type

    def set_location_id(self, location_id: Union[str, int]) -> None:
        """Set location ID"""
        self.location_id = int(location_id)

    def get_location_id(self) -> int:
        """Get location ID"""
        return self.location_id

    def set_curl_execution_timeout(self, timeout: int) -> None:
        """Set cURL execution timeout"""
        self.curl_exec_timeout = abs(timeout)

    def get_curl_execution_timeout(self) -> int:
        """Get cURL execution timeout"""
        return self.curl_exec_timeout

    def get_authorize_code_url(self) -> str:
        """Build OAuth2 authorization URL"""
        self._validate_params(["app_key"])

        params = {"client_id": self.app_key, "response_type": "code"}

        if self.redirect_uri:
            params["redirect_uri"] = self.redirect_uri

        return "https://my.pcloud.com/oauth2/authorize?" + urlencode(params)

    def get_token_from_code(
        self, code: str, location_id: Union[str, int]
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        self._validate_params(["app_key", "app_secret"])

        params = {
            "client_id": self.app_key,
            "client_secret": self.app_secret,
            "code": code,
        }

        host = Config.get_api_host_by_location_id(int(location_id))
        url = host + "oauth2_token?" + urlencode(params)

        response = requests.get(url, verify=False)

        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            if data.get("result") == 0:
                # Token OAuth2
                self.auth_type = "oauth2"
                return {
                    "access_token": data["access_token"],
                    "locationid": data["locationid"],
                }
            else:
                raise PCloudException(data.get("error", "Unknown error"))

        raise PCloudException("Invalid response format")

    def login_with_credentials(
        self, email: str, password: str, location_id: Union[str, int] = 1
    ) -> Dict[str, Any]:
        """
        Login directly with email and password to get access token
        This is simpler than OAuth2 flow for direct authentication

        Args:
            email: User's pCloud email
            password: User's pCloud password
            location_id: Server location (1=US, 2=EU)

        Returns:
            Dict containing access_token and other login info
        """
        if not email or not password:
            raise PCloudException("Email and password are required")

        email = email.strip()
        location_id = int(location_id)

        params = {"getauth": 1, "logout": 1, "username": email, "password": password}

        host = Config.get_api_host_by_location_id(location_id)
        url = host + "userinfo?" + urlencode(params)

        try:
            response = requests.get(url, verify=False, timeout=30)

            # Check HTTP status first
            if response.status_code != 200:
                raise PCloudException(f"HTTP error {response.status_code}")

            # Check content type
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise PCloudException("Invalid response format from server")

            data = response.json()
            result = data.get("result")

            if result == 0:
                # Success - extract auth token
                auth_token = data.get("auth")
                if not auth_token:
                    raise PCloudException(
                        "No authentication token received from pCloud API"
                    )

                # Set the obtained token and location + type d'auth
                self.access_token = auth_token
                self.location_id = location_id
                self.auth_type = (
                    "direct"  # Important: marquer comme authentification directe
                )

                return {
                    "access_token": auth_token,
                    "locationid": location_id,
                    "userid": data.get("userid"),
                    "email": data.get("email", email),
                    "quota": data.get("quota"),
                    "usedquota": data.get("usedquota"),
                }
            else:
                # Handle specific error codes and messages
                error_message = data.get("error", "Login failed")

                if (
                    "invalid" in error_message.lower()
                    or "wrong" in error_message.lower()
                ):
                    raise PCloudException(
                        "Invalid email or password. Please check your credentials."
                    )
                elif (
                    "rate" in error_message.lower() or "limit" in error_message.lower()
                ):
                    raise PCloudException(
                        "Too many login attempts. Please wait a few minutes and "
                        "try again."
                    )
                elif "account" in error_message.lower():
                    raise PCloudException(
                        "Account issue. Please check your pCloud account status."
                    )
                else:
                    # For unknown errors, suggest trying the other server
                    other_server = "EU" if location_id == 1 else "US"
                    raise PCloudException(
                        f"Login failed: {error_message}. Try using "
                        f"location_id={2 if location_id == 1 else 1} for "
                        f"{other_server} server."
                    )

        except requests.exceptions.Timeout:
            raise PCloudException(
                "Connection timeout. Please check your internet connection."
            )
        except requests.exceptions.ConnectionError:
            other_server = "EU" if location_id == 1 else "US"
            raise PCloudException(
                f"Cannot connect to pCloud servers. Try "
                f"location_id={2 if location_id == 1 else 1} for "
                f"{other_server} server."
            )
        except requests.exceptions.RequestException as e:
            raise PCloudException(f"Network error during login: {str(e)}")
        except json.JSONDecodeError:
            raise PCloudException("Invalid JSON response from server")

    def _validate_params(self, keys: List[str]) -> None:
        """Validate required parameters"""
        for key in keys:
            value = getattr(self, key, None)
            if not value:
                raise PCloudException(f"{key} not found")
