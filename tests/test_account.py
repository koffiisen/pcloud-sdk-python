"""
Unit tests for the pcloud_sdk.account.Account class.
"""

import pytest
import responses
import requests # For requests.exceptions

from pcloud_sdk.account import Account
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.config import Config # Required for API host resolution in Account methods


class TestAccountInitialization:
    """Tests for Account class initialization and basic attribute handling."""

    def test_initialization_defaults(self):
        """Test Account initialization with only account_id and default values."""
        account_id = "test_user@example.com"
        acc = Account(account_id=account_id)

        assert acc.account_id == account_id
        assert acc.access_token == ""
        assert acc.location_id == 1  # Default US
        assert acc.auth_type == "oauth2" # Default auth_type
        assert acc.app_key == ""
        assert acc.app_secret == ""
        assert acc.redirect_uri == ""
        assert acc.email == ""
        assert acc.user_id is None
        assert acc.quota is None
        assert acc.used_quota is None
        assert acc.is_authenticated is False
        assert acc.curl_exec_timeout == 3600 # Default timeout

    def test_get_info(self):
        """Test get_info() method returns all relevant attributes."""
        acc = Account(
            account_id="info_user@example.com",
            access_token="test_token",
            location_id=2,
            auth_type="direct",
            app_key="test_app_key",
            app_secret="test_app_secret",
            redirect_uri="http://localhost/callback",
            email="info_user@example.com",
            user_id=12345,
            quota=10000,
            used_quota=500,
            is_authenticated=True,
            curl_exec_timeout=120
        )
        info = acc.get_info()

        expected_keys = [
            "account_id", "access_token", "location_id", "auth_type",
            "app_key", "app_secret", "redirect_uri", "email", "user_id",
            "quota", "used_quota", "is_authenticated", "curl_exec_timeout"
        ]
        for key in expected_keys:
            assert key in info

        assert info["account_id"] == "info_user@example.com"
        assert info["access_token"] == "test_token"
        assert info["location_id"] == 2
        assert info["auth_type"] == "direct"
        assert info["email"] == "info_user@example.com"
        assert info["user_id"] == 12345
        assert info["is_authenticated"] is True
        assert info["curl_exec_timeout"] == 120


    def test_set_curl_exec_timeout(self):
        """Test set_curl_exec_timeout method and its reflection in get_info."""
        acc = Account(account_id="timeout_user@example.com")
        acc.set_curl_exec_timeout(60)
        assert acc.curl_exec_timeout == 60
        assert acc.get_info()["curl_exec_timeout"] == 60


class TestAccountCredentialManagement:
    """Tests for credential and user detail management methods."""

    def setup_method(self):
        self.acc = Account(account_id="mgmt_user@example.com")

    def test_set_credentials(self):
        """Test set_credentials method."""
        self.acc.set_credentials(access_token="new_token", location_id=2, auth_type="oauth2_test")
        assert self.acc.access_token == "new_token"
        assert self.acc.location_id == 2
        assert self.acc.auth_type == "oauth2_test"
        assert self.acc.is_authenticated is True

    def test_set_user_details(self):
        """Test set_user_details method."""
        self.acc.set_user_details(email="details@example.com", user_id=54321, quota=20000, used_quota=1000)
        assert self.acc.email == "details@example.com"
        assert self.acc.user_id == 54321
        assert self.acc.quota == 20000
        assert self.acc.used_quota == 1000

    def test_clear_credentials(self):
        """Test clear_credentials method."""
        # Set some initial values
        self.acc.set_credentials(access_token="token_to_clear", location_id=1, auth_type="direct")
        self.acc.set_user_details(email="clear@example.com", user_id=789, quota=300, used_quota=30)
        self.acc.is_authenticated = True # Explicitly set for test clarity

        self.acc.clear_credentials()

        assert self.acc.access_token == ""
        assert self.acc.email == ""
        assert self.acc.user_id is None
        assert self.acc.quota is None
        assert self.acc.used_quota is None
        assert self.acc.is_authenticated is False
        assert self.acc.auth_type == "oauth2" # Resets to default


class TestAccountDirectLogin:
    """Tests for perform_direct_login method."""

    def setup_method(self):
        self.account = Account(account_id="direct_login_user@example.com")
        # Ensure Config resolves API hosts correctly based on location_id
        # Default location_id in Account is 1 (US - api.pcloud.com)
        # If tests mock eapi.pcloud.com, ensure location_id matches or mock Config.get_api_host_by_location_id

    @responses.activate
    def test_perform_direct_login_success(self):
        """Test successful direct login."""
        login_email = "direct_login_user@example.com"
        login_password = "password123"
        login_location_id = 2 # EU for eapi.pcloud.com

        mock_response_data = {
            "result": 0,
            "auth": "test_auth_token",
            "userid": 123456,
            "email": login_email,
            "quota": 10737418240, # 10 GB
            "usedquota": 1073741824, # 1 GB
        }

        api_host = Config.get_api_host_by_location_id(login_location_id)
        responses.add(
            responses.GET,
            f"{api_host}userinfo",
            json=mock_response_data,
            status=200
        )

        result = self.account.perform_direct_login(login_email, login_password, login_location_id)

        assert result == mock_response_data
        assert self.account.access_token == "test_auth_token"
        assert self.account.email == login_email
        assert self.account.user_id == 123456
        assert self.account.quota == 10737418240
        assert self.account.used_quota == 1073741824
        assert self.account.location_id == login_location_id
        assert self.account.auth_type == "direct"
        assert self.account.is_authenticated is True

    @responses.activate
    def test_perform_direct_login_api_error_invalid_credentials(self):
        """Test direct login failure due to invalid credentials (API error 2009)."""
        login_location_id = 1 # US
        api_host = Config.get_api_host_by_location_id(login_location_id)
        responses.add(
            responses.GET,
            f"{api_host}userinfo",
            json={"result": 2009, "error": "Invalid username or password."},
            status=200
        )
        with pytest.raises(PCloudException, match="Login failed: Invalid email or password"):
            self.account.perform_direct_login("user@example.com", "wrongpass", login_location_id)
        assert self.account.is_authenticated is False

    @responses.activate
    def test_perform_direct_login_api_error_other(self):
        """Test direct login failure due to other API error."""
        login_location_id = 1
        api_host = Config.get_api_host_by_location_id(login_location_id)
        responses.add(
            responses.GET,
            f"{api_host}userinfo",
            json={"result": 2000, "error": "Some other API error."}, # Example: Login required (though getauth=1 is for login)
            status=200
        )
        with pytest.raises(PCloudException, match="Login failed: Some other API error."):
            self.account.perform_direct_login("user@example.com", "password", login_location_id)
        assert self.account.is_authenticated is False

    @responses.activate
    def test_perform_direct_login_network_error(self):
        """Test direct login failure due to network error."""
        login_location_id = 1
        api_host = Config.get_api_host_by_location_id(login_location_id)
        responses.add(
            responses.GET,
            f"{api_host}userinfo",
            body=requests.exceptions.Timeout("Simulated network timeout")
        )
        with pytest.raises(PCloudException, match="Network error during direct login"):
            self.account.perform_direct_login("user@example.com", "password", login_location_id)
        assert self.account.is_authenticated is False

    @responses.activate
    def test_perform_direct_login_json_decode_error(self):
        """Test direct login failure due to invalid JSON response."""
        login_location_id = 1
        api_host = Config.get_api_host_by_location_id(login_location_id)
        responses.add(
            responses.GET,
            f"{api_host}userinfo",
            body="This is not valid JSON",
            status=200,
            content_type="application/json" # To force json parsing attempt
        )
        with pytest.raises(PCloudException, match="Failed to decode JSON response from direct login"):
            self.account.perform_direct_login("user@example.com", "password", login_location_id)
        assert self.account.is_authenticated is False


class TestAccountOAuthExchange:
    """Tests for perform_oauth_exchange method."""

    def setup_method(self):
        self.account = Account(account_id="oauth_user@example.com", email="oauth_user@example.com")
        self.app_key = "test_client_id"
        self.app_secret = "test_client_secret"
        # Default location_id for Account is 1 (US - api.pcloud.com)

    @responses.activate
    def test_perform_oauth_exchange_success(self):
        """Test successful OAuth code exchange."""
        auth_code = "sample_auth_code"
        exchange_location_id = 2 # EU for eapi.pcloud.com

        mock_response_data = {
            "access_token": "oauth_access_token_123",
            "token_type": "bearer",
            "expires_in": 315360000, # Example value
            "userid": 789012,
            "locationid": exchange_location_id, # API confirms which location this token is for
            "email": "oauth_user_api@example.com" # API might return the confirmed email
        }
        api_host = Config.get_api_host_by_location_id(exchange_location_id)
        responses.add(
            responses.GET,
            f"{api_host}oauth2_token",
            json=mock_response_data,
            status=200
        )

        result = self.account.perform_oauth_exchange(
            auth_code, exchange_location_id, self.app_key, self.app_secret
        )

        assert result == mock_response_data
        assert self.account.access_token == "oauth_access_token_123"
        assert self.account.location_id == exchange_location_id
        assert self.account.auth_type == "oauth2"
        assert self.account.is_authenticated is True
        assert self.account.user_id == 789012
        assert self.account.email == "oauth_user_api@example.com" # Email updated from API response

    @responses.activate
    def test_perform_oauth_exchange_api_error(self):
        """Test OAuth exchange failure due to API error."""
        exchange_location_id = 1
        api_host = Config.get_api_host_by_location_id(exchange_location_id)
        responses.add(
            responses.GET,
            f"{api_host}oauth2_token",
            json={"error": "invalid_grant", "error_description": "Invalid authorization code."},
            status=400 # OAuth errors often come with 400 or 401
        )
        with pytest.raises(PCloudException, match="OAuth exchange failed: Invalid authorization code."):
            self.account.perform_oauth_exchange("invalid_code", exchange_location_id, self.app_key, self.app_secret)
        assert self.account.is_authenticated is False

    @responses.activate
    def test_perform_oauth_exchange_network_error(self):
        """Test OAuth exchange failure due to network error."""
        exchange_location_id = 1
        api_host = Config.get_api_host_by_location_id(exchange_location_id)
        responses.add(
            responses.GET,
            f"{api_host}oauth2_token",
            body=requests.exceptions.ConnectionError("Simulated network connection error")
        )
        with pytest.raises(PCloudException, match="Network error during OAuth exchange"):
            self.account.perform_oauth_exchange("any_code", exchange_location_id, self.app_key, self.app_secret)
        assert self.account.is_authenticated is False

    @responses.activate
    def test_perform_oauth_exchange_json_decode_error(self):
        """Test OAuth exchange failure due to invalid JSON response."""
        exchange_location_id = 1
        api_host = Config.get_api_host_by_location_id(exchange_location_id)
        responses.add(
            responses.GET,
            f"{api_host}oauth2_token",
            body="Malformed JSON",
            status=200,
            content_type="application/json"
        )
        with pytest.raises(PCloudException, match="Failed to decode JSON response from OAuth exchange"):
            self.account.perform_oauth_exchange("any_code", exchange_location_id, self.app_key, self.app_secret)
        assert self.account.is_authenticated is False
