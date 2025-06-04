"""
Comprehensive authentication tests for pCloud SDK
Tests direct login, OAuth2 flow, token management, and error scenarios
"""

import json
import os
import tempfile
import time
from unittest.mock import Mock, patch, mock_open

import pytest
import requests
import responses

from pcloud_sdk import PCloudSDK
from pcloud_sdk.app import App
from pcloud_sdk.exceptions import PCloudException
from .test_config import (
    PCLOUD_EMAIL, PCLOUD_PASSWORD, PCLOUD_ACCESS_TOKEN,
    PCLOUD_CLIENT_ID, PCLOUD_CLIENT_SECRET, PCLOUD_LOCATION_ID,
    has_real_credentials, has_oauth2_credentials,
    requires_real_credentials, requires_oauth2_credentials,
    skip_if_no_integration_tests, get_test_credentials, get_oauth2_credentials,
    safe_remove_file, safe_cleanup_temp_dir
)


class TestDirectAuthentication:
    """Tests for direct email/password authentication"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        # Use mock data for unit tests with @responses.activate
        self.test_email = "test@example.com"
        self.test_password = "test_password"
        self.test_token = "test_token_123"

    @responses.activate
    def test_successful_direct_login(self):
        """Test successful direct login with email and password"""
        # Mock successful login response
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "auth": self.test_token,
                "userid": 12345,
                "email": self.test_email,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        login_info = self.app.login_with_credentials(
            self.test_email, self.test_password, location_id=2
        )

        assert login_info["access_token"] == self.test_token
        assert login_info["email"] == self.test_email
        assert login_info["userid"] == 12345
        assert login_info["locationid"] == 2
        assert self.app.get_access_token() == self.test_token
        assert self.app.get_auth_type() == "direct"

    @responses.activate
    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 2000,
                "error": "Invalid username or password."
            },
            status=200
        )

        with pytest.raises(PCloudException, match="Invalid email or password"):
            self.app.login_with_credentials(
                "wrong@example.com", "wrong_password", location_id=2
            )

    @responses.activate
    def test_rate_limiting(self):
        """Test rate limiting error handling"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 4000,
                "error": "Too many login attempts. Rate limited."
            },
            status=200
        )

        with pytest.raises(PCloudException, match="Too many login attempts"):
            self.app.login_with_credentials(
                self.test_email, self.test_password, location_id=2
            )

    def test_missing_credentials(self):
        """Test login without providing credentials"""
        with pytest.raises(PCloudException, match="Email and password are required"):
            self.app.login_with_credentials("", "", location_id=2)

        with pytest.raises(PCloudException, match="Email and password are required"):
            self.app.login_with_credentials(self.test_email, "", location_id=2)

    @responses.activate
    def test_connection_timeout(self):
        """Test connection timeout handling"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            body=requests.exceptions.Timeout("Connection timeout"),
            headers={'content-length': '0'}
        )

        with pytest.raises(PCloudException, match="Connection timeout"):
            self.app.login_with_credentials(
                self.test_email, self.test_password, location_id=2
            )

    @responses.activate
    def test_different_server_locations(self):
        """Test login to different server locations"""
        # Test EU server (location_id=2)
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "auth": "eu_token_123",
                "userid": 12345,
                "email": self.test_email,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        # Test US server (location_id=1)
        responses.add(
            responses.GET,
            "https://api.pcloud.com/userinfo",
            json={
                "result": 0,
                "auth": "us_token_123",
                "userid": 12345,
                "email": self.test_email,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        # Test EU login
        login_info_eu = self.app.login_with_credentials(
            self.test_email, self.test_password, location_id=2
        )
        assert login_info_eu["access_token"] == "eu_token_123"
        assert login_info_eu["locationid"] == 2

        # Reset app for US test
        self.app = App()
        login_info_us = self.app.login_with_credentials(
            self.test_email, self.test_password, location_id=1
        )
        assert login_info_us["access_token"] == "us_token_123"
        assert login_info_us["locationid"] == 1


class TestOAuth2Authentication:
    """Tests for OAuth2 authentication flow"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_app_key(PCLOUD_CLIENT_ID)
        self.app.set_app_secret(PCLOUD_CLIENT_SECRET)
        self.app.set_redirect_uri("http://localhost:8080/callback")

    def test_get_authorize_url(self):
        """Test OAuth2 authorization URL generation"""
        auth_url = self.app.get_authorize_code_url()
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert f"client_id={PCLOUD_CLIENT_ID}" in auth_url
        assert "response_type=code" in auth_url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback" in auth_url

    def test_get_authorize_url_without_redirect(self):
        """Test OAuth2 URL generation without redirect URI"""
        self.app.set_redirect_uri("")
        auth_url = self.app.get_authorize_code_url()
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert f"client_id={PCLOUD_CLIENT_ID}" in auth_url
        assert "response_type=code" in auth_url
        assert "redirect_uri" not in auth_url

    def test_missing_app_key_for_oauth(self):
        """Test OAuth2 URL generation without app key"""
        self.app.set_app_key("")
        
        with pytest.raises(PCloudException, match="app_key not found"):
            self.app.get_authorize_code_url()

    @responses.activate
    def test_successful_token_exchange(self):
        """Test successful OAuth2 code to token exchange"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/oauth2_token",
            json={
                "result": 0,
                "access_token": "oauth2_token_123",
                "locationid": 2
            },
            status=200
        )

        token_info = self.app.get_token_from_code("auth_code_123", location_id=2)
        
        assert token_info["access_token"] == "oauth2_token_123"
        assert token_info["locationid"] == 2
        assert self.app.get_auth_type() == "oauth2"

    @responses.activate
    def test_invalid_oauth_code(self):
        """Test OAuth2 token exchange with invalid code"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/oauth2_token",
            json={
                "result": 1000,
                "error": "Invalid authorization code"
            },
            status=200
        )

        with pytest.raises(PCloudException, match="Invalid authorization code"):
            self.app.get_token_from_code("invalid_code", location_id=2)

    def test_missing_credentials_for_token_exchange(self):
        """Test token exchange without app credentials"""
        self.app.set_app_key("")
        
        with pytest.raises(PCloudException, match="app_key not found"):
            self.app.get_token_from_code("auth_code_123", location_id=2)

        self.app.set_app_key("test_client_id")
        self.app.set_app_secret("")
        
        with pytest.raises(PCloudException, match="app_secret not found"):
            self.app.get_token_from_code("auth_code_123", location_id=2)


class TestTokenManagement:
    """Tests for automatic token management functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_token_manager_enabled_by_default(self):
        """Test that token manager is enabled by default"""
        sdk = PCloudSDK(token_file=self.token_file)
        assert sdk.token_manager_enabled is True

    def test_token_manager_disabled(self):
        """Test disabling token manager"""
        sdk = PCloudSDK(token_manager=False, token_file=self.token_file)
        assert sdk.token_manager_enabled is False

    def test_save_credentials(self):
        """Test saving credentials to file"""
        sdk = PCloudSDK(token_file=self.token_file, auth_type="direct")
        
        test_credentials = {
            "email": "test@example.com",
            "access_token": "test_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "user_info": {
                "userid": 12345,
                "quota": 10737418240,
                "usedquota": 1073741824
            }
        }

        sdk._save_credentials(
            email=test_credentials["email"],
            token=test_credentials["access_token"],
            location_id=test_credentials["location_id"],
            user_info=test_credentials["user_info"]
        )

        assert os.path.exists(self.token_file)
        
        with open(self.token_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["email"] == test_credentials["email"]
        assert saved_data["access_token"] == test_credentials["access_token"]
        assert saved_data["location_id"] == test_credentials["location_id"]
        assert saved_data["auth_type"] == "direct"
        assert "saved_at" in saved_data

    def test_load_valid_credentials(self):
        """Test loading valid saved credentials"""
        # Create test credentials file
        test_credentials = {
            "email": "test@example.com",
            "access_token": "test_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "user_info": {
                "userid": 12345,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            "saved_at": time.time()  # Recent save
        }

        with open(self.token_file, 'w') as f:
            json.dump(test_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file)
        loaded = sdk._load_saved_credentials()

        assert loaded is True
        assert sdk.app.get_access_token() == test_credentials["access_token"]
        assert sdk.app.get_location_id() == test_credentials["location_id"]
        assert sdk.get_saved_email() == test_credentials["email"]

    def test_load_expired_credentials(self):
        """Test loading old/expired credentials"""
        # Create old credentials (older than 30 days)
        old_time = time.time() - (31 * 24 * 3600)  # 31 days ago
        test_credentials = {
            "email": "test@example.com",
            "access_token": "old_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "user_info": {},
            "saved_at": old_time
        }

        with open(self.token_file, 'w') as f:
            json.dump(test_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file)
        loaded = sdk._load_saved_credentials()

        assert loaded is False
        assert sdk.app.get_access_token() == ""

    def test_load_expired_credentials_custom_staleness(self):
        """Test loading old/expired credentials with custom staleness periods"""
        # Scenario 1: token_staleness_days = 0 (always stale unless saved_at is future/now)
        very_recent_time = time.time() - 1  # 1 second ago
        credentials_almost_now = {
            "email": "stale@example.com", "access_token": "stale_token_1",
            "location_id": 1, "auth_type": "direct", "user_info": {},
            "saved_at": very_recent_time
        }
        with open(self.token_file, 'w') as f:
            json.dump(credentials_almost_now, f)

        sdk_staleness_zero = PCloudSDK(token_file=self.token_file, token_staleness_days=0)
        loaded = sdk_staleness_zero._load_saved_credentials()
        assert loaded is False, "Token saved 1s ago should be stale with token_staleness_days=0"
        assert sdk_staleness_zero.app.get_access_token() == ""
        safe_remove_file(self.token_file) # Clean up for next scenario

        # Scenario 2: token_staleness_days = 1, token saved 2 days ago (should be stale)
        two_days_ago = time.time() - (2 * 24 * 3600)
        credentials_two_days_old = {
            "email": "stale@example.com", "access_token": "stale_token_2",
            "location_id": 1, "auth_type": "direct", "user_info": {},
            "saved_at": two_days_ago
        }
        with open(self.token_file, 'w') as f:
            json.dump(credentials_two_days_old, f)

        sdk_staleness_one_day = PCloudSDK(token_file=self.token_file, token_staleness_days=1)
        loaded = sdk_staleness_one_day._load_saved_credentials()
        assert loaded is False, "Token saved 2 days ago should be stale with token_staleness_days=1"
        assert sdk_staleness_one_day.app.get_access_token() == ""
        safe_remove_file(self.token_file)

        # Scenario 3: token_staleness_days = 60, token saved 31 days ago (should be valid)
        thirty_one_days_ago = time.time() - (31 * 24 * 3600)
        credentials_thirty_one_days_old = {
            "email": "valid@example.com", "access_token": "valid_token_long_staleness",
            "location_id": 1, "auth_type": "direct", "user_info": {},
            "saved_at": thirty_one_days_ago
        }
        with open(self.token_file, 'w') as f:
            json.dump(credentials_thirty_one_days_old, f)

        sdk_staleness_sixty_days = PCloudSDK(token_file=self.token_file, token_staleness_days=60)
        loaded = sdk_staleness_sixty_days._load_saved_credentials()
        assert loaded is True, "Token saved 31 days ago should be valid with token_staleness_days=60"
        assert sdk_staleness_sixty_days.app.get_access_token() == "valid_token_long_staleness"
        safe_remove_file(self.token_file)

    def test_clear_saved_credentials(self):
        """Test clearing saved credentials"""
        # Create test credentials file
        test_credentials = {
            "email": "test@example.com",
            "access_token": "test_token_123",
            "saved_at": time.time()
        }

        with open(self.token_file, 'w') as f:
            json.dump(test_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file)
        sdk._load_saved_credentials()
        
        # Clear credentials
        sdk.clear_saved_credentials()
        
        assert not os.path.exists(self.token_file)
        assert sdk._saved_credentials is None

    @responses.activate
    def test_test_existing_credentials_valid(self):
        """Test validation of existing credentials - valid case"""
        # Mock successful user info request
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "email": "test@example.com",
                "userid": 12345
            },
            status=200
        )

        sdk = PCloudSDK(token_file=self.token_file)
        sdk.app.set_access_token("valid_token", "direct")
        
        is_valid = sdk._test_existing_credentials()
        assert is_valid is True

    @responses.activate  
    def test_test_existing_credentials_invalid(self):
        """Test validation of existing credentials - invalid case"""
        # Mock failed user info request
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 2000,
                "error": "Invalid auth token"
            },
            status=200
        )

        sdk = PCloudSDK(token_file=self.token_file)
        sdk.app.set_access_token("invalid_token", "direct")
        
        is_valid = sdk._test_existing_credentials()
        assert is_valid is False


class TestSDKAuthentication:
    """Tests for PCloudSDK authentication integration"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_sdk_login_success(self):
        """Test successful SDK login with credential saving"""
        # Mock login response
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "auth": "test_token_123",
                "userid": 12345,
                "email": "test@example.com",
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        # Mock user info request for saving credentials
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "email": "test@example.com",
                "userid": 12345,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        sdk = PCloudSDK(token_file=self.token_file)
        login_info = sdk.login("test@example.com", "test_password", location_id=2)

        assert login_info["access_token"] == "test_token_123"
        assert login_info["email"] == "test@example.com"
        assert sdk.is_authenticated() is True
        assert os.path.exists(self.token_file)

    @responses.activate
    def test_sdk_oauth2_authentication(self):
        """Test SDK OAuth2 authentication flow"""
        # Mock OAuth2 token exchange
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/oauth2_token",
            json={
                "result": 0,
                "access_token": "oauth2_token_123",
                "locationid": 2
            },
            status=200
        )

        # Mock user info request for saving credentials
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "email": "test@example.com",
                "userid": 12345,
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        sdk = PCloudSDK(
            app_key="test_client_id",
            app_secret="test_client_secret",
            auth_type="oauth2",
            token_file=self.token_file
        )

        # Test getting authorization URL
        auth_url = sdk.get_auth_url("http://localhost:8080/callback")
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url

        # Test token exchange
        token_info = sdk.authenticate("auth_code_123", location_id=2) 
        
        assert token_info["access_token"] == "oauth2_token_123"
        assert sdk.is_authenticated() is True

    def test_sdk_logout(self):
        """Test SDK logout functionality"""
        sdk = PCloudSDK(token_file=self.token_file)
        sdk.app.set_access_token("test_token", "direct")
        
        assert sdk.is_authenticated() is True
        
        sdk.logout()
        
        assert sdk.is_authenticated() is False
        assert sdk.app.get_access_token() == ""

    def test_multi_authentication_methods(self):
        """Test switching between authentication methods"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Test direct token setting
        sdk.set_access_token("direct_token", "direct")
        assert sdk.app.get_access_token() == "direct_token"
        assert sdk.app.get_auth_type() == "direct"
        
        # Test OAuth2 token setting
        sdk.set_access_token("oauth2_token", "oauth2")
        assert sdk.app.get_access_token() == "oauth2_token"
        assert sdk.app.get_auth_type() == "oauth2"

    def test_credentials_info(self):
        """Test getting credentials information"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Test without saved credentials
        info = sdk.get_credentials_info()
        assert info["authenticated"] is False
        assert info["token_manager_enabled"] is True
        assert info["file"] == self.token_file

        # Test with saved credentials
        sdk._saved_credentials = {
            "email": "test@example.com",
            "location_id": 2,
            "auth_type": "direct",
            "saved_at": time.time()
        }
        
        info = sdk.get_credentials_info()
        assert info["email"] == "test@example.com"
        assert info["location_id"] == 2
        assert info["auth_type"] == "direct"
        assert "age_days" in info

    @responses.activate
    def test_login_or_load_deprecation_warning(self):
        """Test that login_or_load issues a DeprecationWarning and still functions."""
        # Mock login response (userinfo is called by login)
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",  # This is the endpoint for login
            json={
                "result": 0, "auth": "test_token_123", "userid": 12345,
                "email": "test@example.com", "quota": 10737418240, "usedquota": 1073741824
            },
            status=200
        )
        # Mock userinfo again for the _save_credentials part
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo", # This is the endpoint for get_user_info
            json={
                "result": 0, "email": "test@example.com", "userid": 12345,
                "quota": 10737418240, "usedquota": 1073741824
            },
            status=200
        )

        sdk = PCloudSDK(token_file=self.token_file)

        with pytest.warns(DeprecationWarning, match="The 'login_or_load' method is deprecated"):
            sdk.login_or_load("test@example.com", "test_password", location_id=2)

        assert sdk.app.get_access_token() == "test_token_123"
        assert sdk.get_saved_email() == "test@example.com"
        assert sdk.is_authenticated() is True
        assert os.path.exists(self.token_file) # Check if credentials were saved


class TestErrorHandling:
    """Tests for various error scenarios"""

    def test_invalid_json_response(self):
        """Test handling of invalid JSON responses"""
        app = App()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response
            
            with pytest.raises(PCloudException, match="Invalid JSON response"):
                app.login_with_credentials("test@example.com", "password", 2)

    def test_http_error_response(self):
        """Test handling of HTTP error responses"""
        app = App()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            with pytest.raises(PCloudException, match="HTTP error 500"):
                app.login_with_credentials("test@example.com", "password", 2)

    def test_network_error_handling(self):
        """Test handling of network errors"""
        app = App()
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network error")
            
            with pytest.raises(PCloudException):
                app.login_with_credentials("test@example.com", "password", 2)


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication (require real credentials)"""

    @requires_real_credentials
    @skip_if_no_integration_tests
    def test_real_login(self):
        """Test real login - only run with actual credentials"""
        creds = get_test_credentials()
        
        sdk = PCloudSDK()
        login_info = sdk.login(creds["email"], creds["password"], location_id=creds["location_id"])
        
        assert "access_token" in login_info
        assert sdk.is_authenticated() is True

    @requires_oauth2_credentials
    @skip_if_no_integration_tests
    def test_real_oauth2_flow(self):
        """Test real OAuth2 flow - only run with actual app credentials"""
        oauth_creds = get_oauth2_credentials()
        
        sdk = PCloudSDK(
            app_key=oauth_creds["client_id"], 
            app_secret=oauth_creds["client_secret"], 
            auth_type="oauth2"
        )
        auth_url = sdk.get_auth_url("http://localhost:8080/callback")
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert oauth_creds["client_id"] in auth_url