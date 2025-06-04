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
import responses

from pcloud_sdk import PCloudSDK
from pcloud_sdk.app import App
from pcloud_sdk.exceptions import PCloudException


class TestDirectAuthentication:
    """Tests for direct email/password authentication"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.test_email = "test@example.com"
        self.test_password = "test_password"
        self.test_token = "test_auth_token_123"

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
            body=Exception("Connection timeout")
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
        self.app.set_app_key("test_client_id")
        self.app.set_app_secret("test_client_secret")
        self.app.set_redirect_uri("http://localhost:8080/callback")

    def test_get_authorize_url(self):
        """Test OAuth2 authorization URL generation"""
        auth_url = self.app.get_authorize_code_url()
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert "client_id=test_client_id" in auth_url
        assert "response_type=code" in auth_url
        assert "redirect_uri=http%3A//localhost%3A8080/callback" in auth_url

    def test_get_authorize_url_without_redirect(self):
        """Test OAuth2 URL generation without redirect URI"""
        self.app.set_redirect_uri("")
        auth_url = self.app.get_authorize_code_url()
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert "client_id=test_client_id" in auth_url
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
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        os.rmdir(self.temp_dir)

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
        sdk = PCloudSDK(token_file=self.token_file)
        
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
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        os.rmdir(self.temp_dir)

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
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(PCloudException):
                app.login_with_credentials("test@example.com", "password", 2)


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication (require real credentials)"""

    @pytest.mark.skip(reason="Requires real pCloud credentials")
    def test_real_login(self):
        """Test real login - only run with actual credentials"""
        # This test would be run with real credentials in CI/CD
        email = os.getenv("PCLOUD_EMAIL")
        password = os.getenv("PCLOUD_PASSWORD")
        
        if not email or not password:
            pytest.skip("Real credentials not provided")
        
        sdk = PCloudSDK()
        login_info = sdk.login(email, password, location_id=2)
        
        assert "access_token" in login_info
        assert sdk.is_authenticated() is True

    @pytest.mark.skip(reason="Requires real OAuth2 setup")
    def test_real_oauth2_flow(self):
        """Test real OAuth2 flow - only run with actual app credentials"""
        app_key = os.getenv("PCLOUD_APP_KEY")
        app_secret = os.getenv("PCLOUD_APP_SECRET")
        
        if not app_key or not app_secret:
            pytest.skip("Real OAuth2 credentials not provided")
        
        sdk = PCloudSDK(app_key=app_key, app_secret=app_secret, auth_type="oauth2")
        auth_url = sdk.get_auth_url("http://localhost:8080/callback")
        
        assert "https://my.pcloud.com/oauth2/authorize" in auth_url
        assert app_key in auth_url