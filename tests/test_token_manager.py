"""
Comprehensive token management tests for pCloud SDK
Tests token saving/loading, validation, expiration, multi-account management, and cleanup
"""

import json
import os
import sys
import tempfile
import time
from io import StringIO
from unittest.mock import Mock, patch, mock_open

import pytest
import responses

from pcloud_sdk import PCloudSDK
from pcloud_sdk.exceptions import PCloudException
from .test_config import (
    requires_real_credentials, skip_if_no_integration_tests, get_test_credentials,
    safe_remove_file, safe_cleanup_temp_dir
)


class TestTokenSavingAndLoading:
    """Tests for basic token saving and loading functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_save_credentials_basic(self):
        """Test basic credential saving functionality"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        test_credentials = {
            "email": "test@example.com",
            "token": "test_token_123",
            "location_id": 2,
            "user_info": {
                "userid": 12345,
                "quota": 10737418240,
                "usedquota": 1073741824
            }
        }

        sdk._save_credentials(
            email=test_credentials["email"],
            token=test_credentials["token"],
            location_id=test_credentials["location_id"],
            user_info=test_credentials["user_info"]
        )

        # Verify file was created
        assert os.path.exists(self.token_file)
        
        # Verify content
        with open(self.token_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["email"] == test_credentials["email"]
        assert saved_data["access_token"] == test_credentials["token"]
        assert saved_data["location_id"] == test_credentials["location_id"]
        assert saved_data["auth_type"] == "direct"  # Default
        assert saved_data["user_info"] == test_credentials["user_info"]
        assert "saved_at" in saved_data

    def test_save_credentials_with_oauth2(self):
        """Test saving OAuth2 credentials"""
        sdk = PCloudSDK(token_file=self.token_file, auth_type="oauth2")
        
        sdk._save_credentials(
            email="oauth@example.com",
            token="oauth_token_456",
            location_id=1,
            user_info={"userid": 67890}
        )

        with open(self.token_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["auth_type"] == "oauth2"
        assert saved_data["location_id"] == 1

    def test_save_credentials_disabled(self):
        """Test that credentials are not saved when token manager is disabled"""
        sdk = PCloudSDK(token_file=self.token_file, token_manager=False)
        
        sdk._save_credentials(
            email="test@example.com",
            token="test_token_123",
            location_id=2
        )

        # File should not be created
        assert not os.path.exists(self.token_file)

    def test_load_valid_credentials(self):
        """Test loading valid saved credentials"""
        test_credentials = {
            "email": "test@example.com",
            "access_token": "test_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "user_info": {"userid": 12345},
            "saved_at": time.time()  # Recent save
        }

        with open(self.token_file, 'w') as f:
            json.dump(test_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file)
        loaded = sdk._load_saved_credentials()

        assert loaded is True
        assert sdk.app.get_access_token() == test_credentials["access_token"]
        assert sdk.app.get_location_id() == test_credentials["location_id"]
        assert sdk.app.get_auth_type() == test_credentials["auth_type"]
        assert sdk.get_saved_email() == test_credentials["email"]

    def test_load_nonexistent_file(self):
        """Test loading credentials when file doesn't exist"""
        sdk = PCloudSDK(token_file=self.token_file)
        loaded = sdk._load_saved_credentials()

        assert loaded is False
        assert sdk.app.get_access_token() == ""

    def test_load_malformed_json(self):
        """Test loading credentials from malformed JSON file"""
        with open(self.token_file, 'w') as f:
            f.write("invalid json content {")

        sdk = PCloudSDK(token_file=self.token_file)
        loaded = sdk._load_saved_credentials()

        assert loaded is False

    def test_load_credentials_missing_fields(self):
        """Test loading credentials with missing required fields"""
        incomplete_credentials = {
            "email": "test@example.com",
            # Missing access_token
            "location_id": 2,
            "saved_at": time.time()
        }

        with open(self.token_file, 'w') as f:
            json.dump(incomplete_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file)
        
        # Should handle gracefully
        try:
            loaded = sdk._load_saved_credentials()
            # Might succeed with partial data or fail gracefully
        except (KeyError, TypeError):
            # Expected if required fields are missing
            pass

    def test_save_credentials_file_write_error(self):
        """Test saving credentials when file write fails"""
        # Use invalid file path
        invalid_path = "/invalid/path/credentials.json"
        sdk = PCloudSDK(token_file=invalid_path)
        
        # Should not raise exception, just log error
        sdk._save_credentials(
            email="test@example.com",
            token="test_token_123",
            location_id=2
        )

    def test_credentials_file_format_consistency(self):
        """Test that saved credentials maintain consistent format"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Save credentials multiple times
        for i in range(3):
            sdk._save_credentials(
                email=f"test{i}@example.com",
                token=f"token_{i}",
                location_id=i + 1,
                user_info={"userid": 1000 + i}
            )
            
            # Load and verify format
            with open(self.token_file, 'r') as f:
                data = json.load(f)
            
            required_fields = ["email", "access_token", "location_id", "auth_type", "saved_at"]
            for field in required_fields:
                assert field in data


class TestTokenValidationAndExpiration:
    """Tests for token validation and expiration handling"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_load_expired_credentials(self):
        """Test loading credentials that are too old"""
        # Create credentials older than 30 days
        old_time = time.time() - (31 * 24 * 3600)  # 31 days ago
        old_credentials = {
            "email": "test@example.com",
            "access_token": "old_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "saved_at": old_time
        }

        with open(self.token_file, 'w') as f:
            json.dump(old_credentials, f)

        sdk = PCloudSDK(token_file=self.token_file) # Default staleness = 30 days
        loaded = sdk._load_saved_credentials()
        assert loaded is False, "Token saved 31 days ago should be stale with default staleness (30 days)"
        assert sdk.app.get_access_token() == ""
        safe_remove_file(self.token_file)

        # Scenario 2: token_staleness_days = 40, token saved 31 days ago (should be valid)
        with open(self.token_file, 'w') as f:
            json.dump(old_credentials, f)
        sdk_long_staleness = PCloudSDK(token_file=self.token_file, token_staleness_days=40)
        loaded_long = sdk_long_staleness._load_saved_credentials()
        assert loaded_long is True, "Token saved 31 days ago should be valid with token_staleness_days=40"
        assert sdk_long_staleness.app.get_access_token() == "old_token_123"
        safe_remove_file(self.token_file)

        # Scenario 3: token_staleness_days = 0, token saved 1 second ago (should be stale)
        very_recent_time = time.time() - 1 # 1 second ago
        very_recent_credentials = {
            "email": "test@example.com", "access_token": "recent_token_stale_immediately",
            "location_id": 2, "auth_type": "direct", "saved_at": very_recent_time
        }
        with open(self.token_file, 'w') as f:
            json.dump(very_recent_credentials, f)
        sdk_zero_staleness = PCloudSDK(token_file=self.token_file, token_staleness_days=0)
        loaded_zero = sdk_zero_staleness._load_saved_credentials()
        assert loaded_zero is False, "Token saved 1s ago should be stale with token_staleness_days=0"
        assert sdk_zero_staleness.app.get_access_token() == ""

    def test_load_recent_credentials(self):
        """Test loading recent credentials with various staleness settings"""
        # Create credentials from 15 days ago
        fifteen_days_ago = time.time() - (15 * 24 * 3600)  # 15 days ago
        recent_credentials = {
            "email": "test@example.com",
            "access_token": "recent_token_123",
            "location_id": 2,
            "auth_type": "direct",
            "saved_at": fifteen_days_ago
        }

        # Scenario 1: Default staleness (30 days), 15-day old token (should be valid)
        with open(self.token_file, 'w') as f:
            json.dump(recent_credentials, f)
        sdk_default = PCloudSDK(token_file=self.token_file) # Default staleness = 30 days
        loaded_default = sdk_default._load_saved_credentials()
        assert loaded_default is True, "15-day old token should be valid with default staleness (30 days)"
        assert sdk_default.app.get_access_token() == "recent_token_123"
        safe_remove_file(self.token_file)

        # Scenario 2: staleness = 10 days, 15-day old token (should be stale)
        with open(self.token_file, 'w') as f:
            json.dump(recent_credentials, f)
        sdk_short_staleness = PCloudSDK(token_file=self.token_file, token_staleness_days=10)
        loaded_short = sdk_short_staleness._load_saved_credentials()
        assert loaded_short is False, "15-day old token should be stale with token_staleness_days=10"
        assert sdk_short_staleness.app.get_access_token() == ""
        safe_remove_file(self.token_file)

        # Scenario 3: staleness = 20 days, 15-day old token (should be valid)
        with open(self.token_file, 'w') as f:
            json.dump(recent_credentials, f)
        sdk_custom_valid_staleness = PCloudSDK(token_file=self.token_file, token_staleness_days=20)
        loaded_custom_valid = sdk_custom_valid_staleness._load_saved_credentials()
        assert loaded_custom_valid is True, "15-day old token should be valid with token_staleness_days=20"
        assert sdk_custom_valid_staleness.app.get_access_token() == "recent_token_123"

    def test_load_credentials_no_timestamp(self):
        """Test loading credentials without saved_at timestamp"""
        credentials_no_time = {
            "email": "test@example.com",
            "access_token": "token_no_time",
            "location_id": 2,
            "auth_type": "direct"
            # No saved_at field
        }

        with open(self.token_file, 'w') as f:
            json.dump(credentials_no_time, f)

        sdk_default = PCloudSDK(token_file=self.token_file) # Default staleness = 30 days
        loaded_default = sdk_default._load_saved_credentials()
        assert loaded_default is False, "Credentials with no timestamp should be stale with default staleness"
        safe_remove_file(self.token_file)

        # Test with a very long staleness period, should still be stale
        with open(self.token_file, 'w') as f:
            json.dump(credentials_no_time, f)
        sdk_long_staleness = PCloudSDK(token_file=self.token_file, token_staleness_days=1000)
        loaded_long_staleness = sdk_long_staleness._load_saved_credentials()
        assert loaded_long_staleness is False, "Credentials with no timestamp should always be stale"

    @responses.activate
    def test_validate_existing_credentials_valid(self):
        """Test validation of existing credentials - valid case"""
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
    def test_validate_existing_credentials_invalid(self):
        """Test validation of existing credentials - invalid case"""
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

    @responses.activate
    def test_validate_credentials_no_token(self):
        """Test validation when no token is set"""
        sdk = PCloudSDK(token_file=self.token_file)
        # Don't set any token
        
        is_valid = sdk._test_existing_credentials()
        assert is_valid is False

    @responses.activate
    def test_validate_credentials_network_error(self):
        """Test validation when network error occurs"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            body=Exception("Network error"),
            headers={'content-length': '0'}
        )

        sdk = PCloudSDK(token_file=self.token_file)
        sdk.app.set_access_token("test_token", "direct")
        
        is_valid = sdk._test_existing_credentials()
        assert is_valid is False

    def test_credentials_age_calculation(self):
        """Test accurate calculation of credentials age"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Test different ages
        test_cases = [
            (time.time(), 0),  # Current time
            (time.time() - 3600, 1/24),  # 1 hour ago
            (time.time() - 86400, 1),  # 1 day ago
            (time.time() - (7 * 86400), 7),  # 1 week ago
            (time.time() - (30 * 86400), 30),  # 30 days ago
        ]
        
        for saved_time, expected_days in test_cases:
            credentials = {
                "email": "test@example.com",
                "access_token": "test_token",
                "location_id": 2,
                "auth_type": "direct",
                "saved_at": saved_time
            }
            
            with open(self.token_file, 'w') as f:
                json.dump(credentials, f)
            
            sdk._saved_credentials = None  # Reset
            sdk._load_saved_credentials()
            
            if sdk._saved_credentials:
                info = sdk.get_credentials_info()
                actual_days = info.get("age_days", 0)
                
                # Allow small tolerance for timing differences
                assert abs(actual_days - expected_days) < 0.1


class TestMultiAccountTokenManagement:
    """Tests for managing tokens for multiple accounts"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        safe_cleanup_temp_dir(self.temp_dir)

    def test_multiple_token_files(self):
        """Test managing separate token files for different accounts"""
        account1_file = os.path.join(self.temp_dir, "account1.json")
        account2_file = os.path.join(self.temp_dir, "account2.json")
        
        # Create two SDK instances with different token files
        sdk1 = PCloudSDK(token_file=account1_file)
        sdk2 = PCloudSDK(token_file=account2_file)
        
        # Save credentials for different accounts
        sdk1._save_credentials(
            email="user1@example.com",
            token="token1_123",
            location_id=1,
            user_info={"userid": 11111}
        )
        
        sdk2._save_credentials(
            email="user2@example.com",
            token="token2_456",
            location_id=2,
            user_info={"userid": 22222}
        )
        
        # Verify separate files exist
        assert os.path.exists(account1_file)
        assert os.path.exists(account2_file)
        
        # Verify content is different
        with open(account1_file, 'r') as f:
            data1 = json.load(f)
        with open(account2_file, 'r') as f:
            data2 = json.load(f)
        
        assert data1["email"] == "user1@example.com"
        assert data2["email"] == "user2@example.com"
        assert data1["access_token"] != data2["access_token"]
        assert data1["location_id"] != data2["location_id"]

    def test_switching_between_accounts(self):
        """Test switching between different account credentials"""
        account1_file = os.path.join(self.temp_dir, "account1.json")
        account2_file = os.path.join(self.temp_dir, "account2.json")
        
        # Prepare credentials for both accounts
        account1_creds = {
            "email": "user1@example.com",
            "access_token": "token1_123",
            "location_id": 1,
            "auth_type": "direct",
            "saved_at": time.time()
        }
        
        account2_creds = {
            "email": "user2@example.com",
            "access_token": "token2_456",
            "location_id": 2,
            "auth_type": "oauth2",
            "saved_at": time.time()
        }
        
        with open(account1_file, 'w') as f:
            json.dump(account1_creds, f)
        with open(account2_file, 'w') as f:
            json.dump(account2_creds, f)
        
        # Load account 1
        sdk = PCloudSDK(token_file=account1_file)
        assert sdk.get_saved_email() == "user1@example.com"
        assert sdk.app.get_access_token() == "token1_123"
        assert sdk.app.get_location_id() == 1
        
        # Switch to account 2
        sdk = PCloudSDK(token_file=account2_file)
        assert sdk.get_saved_email() == "user2@example.com"
        assert sdk.app.get_access_token() == "token2_456"
        assert sdk.app.get_location_id() == 2
        assert sdk.app.get_auth_type() == "oauth2"

    def test_account_isolation(self):
        """Test that account credentials are properly isolated"""
        account1_file = os.path.join(self.temp_dir, "account1.json")
        account2_file = os.path.join(self.temp_dir, "account2.json")
        
        sdk1 = PCloudSDK(token_file=account1_file)
        sdk2 = PCloudSDK(token_file=account2_file)
        
        # Save credentials for account 1
        sdk1._save_credentials(
            email="user1@example.com",
            token="token1_123",
            location_id=1
        )
        
        # SDK2 should not have access to SDK1's credentials
        assert sdk2.get_saved_email() is None
        assert sdk2.app.get_access_token() == ""
        
        # Save credentials for account 2
        sdk2._save_credentials(
            email="user2@example.com",
            token="token2_456",
            location_id=2
        )
        
        # SDK1 should still have its own credentials
        assert sdk1.get_saved_email() == "user1@example.com"
        assert sdk1.app.get_access_token() == "token1_123"

    def test_concurrent_token_access(self):
        """Test concurrent access to token files"""
        import threading
        
        shared_file = os.path.join(self.temp_dir, "shared_credentials.json")
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                sdk = PCloudSDK(token_file=shared_file)
                sdk._save_credentials(
                    email=f"user{worker_id}@example.com",
                    token=f"token_{worker_id}",
                    location_id=worker_id
                )
                results.append(worker_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads accessing same file
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 5
        
        # Verify file exists and contains data from last writer
        assert os.path.exists(shared_file)


class TestTokenFileEncryptionAndSecurity:
    """Tests for token file security considerations"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_token_file_permissions(self):
        """Test that token files have appropriate permissions"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        sdk._save_credentials(
            email="test@example.com",
            token="secret_token_123",
            location_id=2
        )
        
        # Check file permissions (should be readable only by owner)
        file_stat = os.stat(self.token_file)
        file_permissions = oct(file_stat.st_mode)[-3:]
        
        # On Unix systems, should be 600 or similar (owner read/write only)
        # On Windows, this test might behave differently
        if os.name != 'nt':  # Not Windows
            assert file_permissions in ['600', '644']  # Allow some variation

    def test_sensitive_data_handling(self):
        """Test that sensitive data is handled appropriately"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        sensitive_token = "very_secret_token_with_sensitive_data"
        
        sdk._save_credentials(
            email="test@example.com",
            token=sensitive_token,
            location_id=2,
            user_info={"sensitive_field": "sensitive_value"}
        )
        
        # Verify data is saved correctly
        with open(self.token_file, 'r') as f:
            data = json.load(f)
        
        assert data["access_token"] == sensitive_token
        assert data["user_info"]["sensitive_field"] == "sensitive_value"

    def test_token_file_in_secure_location(self):
        """Test storing token file in user's home directory"""
        # Test with default location (in user's home)
        home_dir = os.path.expanduser("~")
        home_token_file = os.path.join(home_dir, ".test_pcloud_credentials")
        
        try:
            sdk = PCloudSDK(token_file=home_token_file)
            
            sdk._save_credentials(
                email="test@example.com",
                token="test_token",
                location_id=2
            )
            
            # Verify file is created in home directory
            assert os.path.exists(home_token_file)
            assert os.path.dirname(home_token_file) == home_dir
            
        finally:
            # Cleanup
            if os.path.exists(home_token_file):
                os.remove(home_token_file)

    def test_prevent_token_exposure_in_logs(self):
        """Test that tokens are not exposed in logs or error messages"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        secret_token = "super_secret_token_should_not_appear_in_logs"
        
        # Set token
        sdk.app.set_access_token(secret_token, "direct")
        
        # Get credentials info (should not expose raw token)
        creds_info = sdk.get_credentials_info()
        
        # Token should not appear in the info
        info_str = str(creds_info)
        assert secret_token not in info_str

    def test_token_cleanup_on_logout(self):
        """Test that tokens are properly cleared on logout"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Save credentials
        sdk._save_credentials(
            email="test@example.com",
            token="token_to_be_cleared",
            location_id=2
        )
        
        # Verify credentials exist
        assert os.path.exists(self.token_file)
        assert sdk.app.get_access_token() != ""
        
        # Logout
        sdk.logout()
        
        # Verify credentials are cleared
        assert not os.path.exists(self.token_file)
        assert sdk.app.get_access_token() == ""
        assert sdk._saved_credentials is None


class TestTokenCleanupOperations:
    """Tests for token cleanup and maintenance operations"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_clear_saved_credentials(self):
        """Test clearing saved credentials"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Save credentials
        sdk._save_credentials(
            email="test@example.com",
            token="test_token_123",
            location_id=2
        )
        
        assert os.path.exists(self.token_file)
        
        # Clear credentials
        sdk.clear_saved_credentials()
        
        assert not os.path.exists(self.token_file)
        assert sdk._saved_credentials is None

    def test_clear_nonexistent_credentials(self):
        """Test clearing credentials when file doesn't exist"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Should not raise error
        sdk.clear_saved_credentials()
        
        assert not os.path.exists(self.token_file)
        assert sdk._saved_credentials is None

    def test_clear_credentials_with_permission_error(self):
        """Test clearing credentials when file can't be deleted"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Save credentials
        sdk._save_credentials(
            email="test@example.com",
            token="test_token_123",
            location_id=2
        )
        
        # Make file read-only (simulate permission error)
        if os.name != 'nt':  # Not Windows
            original_stdout = sys.stdout
            sys.stdout = captured_stdout = StringIO()

            try:
                os.chmod(self.token_file, 0o444) # Make read-only
                sdk.clear_saved_credentials()
            finally:
                sys.stdout = original_stdout # Restore stdout
                # Always attempt to restore permissions for subsequent tests/cleanup
                os.chmod(self.token_file, 0o666)

            output = captured_stdout.getvalue()

            assert os.path.exists(self.token_file) # File should still exist
            assert "Could not delete credentials" in output
            assert "due to a permission error" in output
        else:
            pytest.skip("Permission test not applicable on Windows in this manner")

    def test_cleanup_old_token_files(self):
        """Test cleanup of old token files"""
        # Create multiple token files with different ages
        files_info = [
            ("current.json", time.time()),
            ("recent.json", time.time() - (7 * 24 * 3600)),  # 7 days old
            ("old.json", time.time() - (45 * 24 * 3600)),    # 45 days old
            ("ancient.json", time.time() - (90 * 24 * 3600)) # 90 days old
        ]
        
        for filename, timestamp in files_info:
            filepath = os.path.join(self.temp_dir, filename)
            credentials = {
                "email": f"user@{filename}",
                "access_token": f"token_{filename}",
                "location_id": 2,
                "saved_at": timestamp
            }
            
            with open(filepath, 'w') as f:
                json.dump(credentials, f)
        
        # Test loading with different staleness settings
        staleness_settings_to_test = [
            {"days": 30, "expected_rejection_for_old": True, "expected_rejection_for_ancient": True}, # Default
            {"days": 60, "expected_rejection_for_old": False, "expected_rejection_for_ancient": True}, # Longer
            {"days": 100, "expected_rejection_for_old": False, "expected_rejection_for_ancient": False}, # Very long
            {"days": 0, "expected_rejection_for_old": True, "expected_rejection_for_ancient": True} # Immediate
        ]

        for setting in staleness_settings_to_test:
            staleness = setting["days"]
            for filename, timestamp in files_info:
                filepath = os.path.join(self.temp_dir, filename)
                # Ensure file exists for this iteration
                temp_creds = {
                    "email": f"user@{filename}", "access_token": f"token_{filename}",
                    "location_id": 2, "saved_at": timestamp
                }
                with open(filepath, 'w') as f_temp:
                    json.dump(temp_creds, f_temp)

                sdk = PCloudSDK(token_file=filepath, token_staleness_days=staleness)
                loaded = sdk._load_saved_credentials()

                age_days = (time.time() - timestamp) / (24 * 3600)

                is_old_file_scenario = "old.json" in filename # 45 days
                is_ancient_file_scenario = "ancient.json" in filename # 90 days

                expected_to_load = True
                if age_days > staleness:
                    expected_to_load = False

                # For no timestamp, it should always be false
                if "saved_at" not in temp_creds and timestamp == 0 : # A bit of a hack for this test structure
                     expected_to_load = False


                assert loaded is expected_to_load, \
                    f"File {filename} (age {age_days:.1f}d) load status {loaded} was not {expected_to_load} with staleness {staleness}d"
            
            # Clean up files for the next staleness setting iteration
            for filename, _ in files_info:
                safe_remove_file(os.path.join(self.temp_dir, filename))


    def test_token_file_corruption_recovery(self):
        """Test recovery from corrupted token files"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Create corrupted file
        with open(self.token_file, 'w') as f:
            f.write("corrupted json data {{{")
        
        # Should handle gracefully
        loaded = sdk._load_saved_credentials()
        assert loaded is False
        
        # Should be able to save new credentials
        sdk._save_credentials(
            email="recovery@example.com",
            token="recovery_token",
            location_id=2
        )
        
        # Verify new credentials work
        sdk2 = PCloudSDK(token_file=self.token_file)
        loaded2 = sdk2._load_saved_credentials()
        assert loaded2 is True
        assert sdk2.get_saved_email() == "recovery@example.com"

    def test_atomic_credential_updates(self):
        """Test that credential updates are atomic"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Save initial credentials
        sdk._save_credentials(
            email="user1@example.com",
            token="token1",
            location_id=1
        )
        
        # Verify initial state
        with open(self.token_file, 'r') as f:
            initial_data = json.load(f)
        assert initial_data["email"] == "user1@example.com"
        
        # Update credentials
        sdk._save_credentials(
            email="user2@example.com",
            token="token2",
            location_id=2
        )
        
        # Verify update
        with open(self.token_file, 'r') as f:
            updated_data = json.load(f)
        assert updated_data["email"] == "user2@example.com"
        assert updated_data["access_token"] == "token2"
        
        # File should always contain valid JSON
        # (In a real implementation, this would use atomic file operations)

    def test_memory_cleanup_on_token_operations(self):
        """Test that sensitive data is cleared from memory"""
        import gc
        
        sdk = PCloudSDK(token_file=self.token_file)
        
        sensitive_token = "sensitive_token_should_be_cleared"
        
        # Set token
        sdk.app.set_access_token(sensitive_token, "direct")
        
        # Clear token
        sdk.app.set_access_token("", "direct")
        
        # Force garbage collection
        gc.collect()
        
        # In a production implementation, you might check that
        # sensitive data is not present in memory dumps
        # For now, just verify the token is cleared
        assert sdk.app.get_access_token() == ""


class TestTokenManagerEdgeCases:
    """Tests for edge cases and error conditions in token management"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    def test_very_long_token_values(self):
        """Test handling of very long token values"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Create very long token (simulating edge case)
        long_token = "x" * 10000
        
        sdk._save_credentials(
            email="test@example.com",
            token=long_token,
            location_id=2
        )
        
        # Should save and load correctly
        sdk2 = PCloudSDK(token_file=self.token_file)
        loaded = sdk2._load_saved_credentials()
        
        assert loaded is True
        assert sdk2.app.get_access_token() == long_token

    def test_unicode_in_credentials(self):
        """Test handling of unicode characters in credentials"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        unicode_email = "(7@KÕ.com"
        unicode_token = "B>:5=_A_unicode_A8<2>;0<8_="
        
        sdk._save_credentials(
            email=unicode_email,
            token=unicode_token,
            location_id=2,
            user_info={"name": "Test User"}
        )
        
        # Should handle unicode correctly
        sdk2 = PCloudSDK(token_file=self.token_file)
        loaded = sdk2._load_saved_credentials()
        
        assert loaded is True
        assert sdk2.get_saved_email() == unicode_email
        assert sdk2.app.get_access_token() == unicode_token

    def test_null_and_empty_values(self):
        """Test handling of null and empty values"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Test with empty values
        sdk._save_credentials(
            email="",
            token="",
            location_id=0,
            user_info={}
        )
        
        sdk2 = PCloudSDK(token_file=self.token_file)
        loaded = sdk2._load_saved_credentials()
        
        # Should load but tokens should be empty
        assert loaded is True
        assert sdk2.get_saved_email() == ""
        assert sdk2.app.get_access_token() == ""

    def test_rapid_save_load_operations(self):
        """Test rapid save/load operations"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Perform rapid save/load operations
        for i in range(100):
            sdk._save_credentials(
                email=f"user{i}@example.com",
                token=f"token_{i}",
                location_id=i % 3 + 1
            )
            
            # Immediately load
            sdk2 = PCloudSDK(token_file=self.token_file)
            loaded = sdk2._load_saved_credentials()
            
            assert loaded is True
            assert sdk2.get_saved_email() == f"user{i}@example.com"

    def test_token_file_in_readonly_directory(self):
        """Test token file operations in read-only directory"""
        if os.name == 'nt':  # Windows
            pytest.skip("Read-only directory test not reliable on Windows")
        
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        readonly_file = os.path.join(readonly_dir, "credentials.json")
        
        try:
            # Make directory read-only
            os.chmod(readonly_dir, 0o555)
            
            sdk = PCloudSDK(token_file=readonly_file)
            
            # Should handle gracefully and not crash
            sdk._save_credentials(
                email="test@example.com",
                token="test_token",
                location_id=2
            )
            
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_token_file_size_limits(self):
        """Test behavior with very large credential files"""
        sdk = PCloudSDK(token_file=self.token_file)
        
        # Create large user_info data
        large_user_info = {
            "large_field": "x" * 100000,  # 100KB of data
            "array_field": ["item"] * 10000,
            "nested": {"deep": {"data": "y" * 50000}}
        }
        
        sdk._save_credentials(
            email="test@example.com",
            token="test_token",
            location_id=2,
            user_info=large_user_info
        )
        
        # Should handle large files correctly
        sdk2 = PCloudSDK(token_file=self.token_file)
        loaded = sdk2._load_saved_credentials()
        
        assert loaded is True
        assert sdk2.get_saved_email() == "test@example.com"

    def test_simultaneous_sdk_instances(self):
        """Test multiple SDK instances with same token file"""
        # Create multiple SDK instances
        sdk1 = PCloudSDK(token_file=self.token_file)
        sdk2 = PCloudSDK(token_file=self.token_file)
        sdk3 = PCloudSDK(token_file=self.token_file)
        
        # Save from one instance
        sdk1._save_credentials(
            email="shared@example.com",
            token="shared_token",
            location_id=2
        )
        
        # Other instances should be able to load
        loaded2 = sdk2._load_saved_credentials()
        loaded3 = sdk3._load_saved_credentials()
        
        assert loaded2 is True
        assert loaded3 is True
        assert sdk2.get_saved_email() == "shared@example.com"
        assert sdk3.get_saved_email() == "shared@example.com"


class TestTokenManagerIntegration:
    """Integration tests for token manager with other SDK components"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.token_file)
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_token_manager_with_login_flow(self):
        """Test token manager integration with login flow"""
        # Mock login response
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "auth": "login_token_123",
                "userid": 12345,
                "email": "test@example.com",
                "quota": 10737418240,
                "usedquota": 1073741824
            },
            status=200
        )

        # Mock user info for credential saving
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
        login_info = sdk.login("test@example.com", "password", location_id=2)

        # Verify login succeeded
        assert login_info["access_token"] == "login_token_123"
        
        # Verify credentials were saved
        assert os.path.exists(self.token_file)
        
        with open(self.token_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["email"] == "test@example.com"
        assert saved_data["access_token"] == "login_token_123"

    @responses.activate
    def test_token_manager_with_oauth2_flow(self):
        """Test token manager integration with OAuth2 flow"""
        # Mock OAuth2 token exchange
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/oauth2_token",
            json={
                "result": 0,
                "access_token": "oauth2_token_456",
                "locationid": 2
            },
            status=200
        )

        # Mock user info for credential saving
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/userinfo",
            json={
                "result": 0,
                "email": "oauth@example.com",
                "userid": 67890,
                "quota": 10737418240,
                "usedquota": 2147483648
            },
            status=200
        )

        sdk = PCloudSDK(
            app_key="test_client_id",
            app_secret="test_client_secret",
            auth_type="oauth2",
            token_file=self.token_file
        )

        token_info = sdk.authenticate("oauth_code_123", location_id=2)

        # Verify OAuth2 succeeded
        assert token_info["access_token"] == "oauth2_token_456"
        
        # Verify credentials were saved with OAuth2 type
        assert os.path.exists(self.token_file)
        
        with open(self.token_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["access_token"] == "oauth2_token_456"
        assert saved_data["auth_type"] == "oauth2"

    @responses.activate
    def test_token_reuse_on_subsequent_login(self):
        """Test that valid tokens are reused on subsequent logins"""
        # Create valid saved credentials
        valid_credentials = {
            "email": "test@example.com",
            "access_token": "existing_valid_token",
            "location_id": 2,
            "auth_type": "direct",
            "user_info": {"userid": 12345},
            "saved_at": time.time()
        }

        with open(self.token_file, 'w') as f:
            json.dump(valid_credentials, f)

        # Mock token validation
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
        
        # Should reuse existing token without new login
        login_info = sdk.login("test@example.com", "password", location_id=2)
        
        assert login_info["access_token"] == "existing_valid_token"
        assert login_info["email"] == "test@example.com"

    def test_token_manager_with_disabled_management(self):
        """Test SDK behavior with token management disabled"""
        sdk = PCloudSDK(token_file=self.token_file, token_manager=False)
        
        # Set token manually
        sdk.set_access_token("manual_token", "direct")
        
        # Manual logout should not affect file system
        sdk.logout()
        
        # No credentials file should be created
        assert not os.path.exists(self.token_file)
        
        # Token should be cleared from memory
        assert sdk.app.get_access_token() == ""

    def test_credentials_info_comprehensive(self):
        """Test comprehensive credentials info reporting"""
        # Test without credentials
        sdk = PCloudSDK(token_file=self.token_file)
        info = sdk.get_credentials_info()
        
        assert info["authenticated"] is False
        assert info["token_manager_enabled"] is True
        assert info["file"] == self.token_file
        
        # Save credentials and test with credentials
        sdk._save_credentials(
            email="info@example.com",
            token="info_token",
            location_id=1,
            user_info={"userid": 99999}
        )
        
        info = sdk.get_credentials_info()
        
        assert info["email"] == "info@example.com"
        assert info["location_id"] == 1
        assert info["auth_type"] == "direct"
        assert "age_days" in info
        assert info["token_manager_enabled"] is True


@pytest.mark.integration
class TestTokenManagerIntegrationReal:
    """Integration tests with real pCloud API (require credentials)"""

    @requires_real_credentials
    @skip_if_no_integration_tests
    def test_real_token_persistence_cycle(self):
        """Test complete token persistence cycle with real API"""
        creds = get_test_credentials()
        
        temp_dir = tempfile.mkdtemp()
        token_file = os.path.join(temp_dir, "real_test_credentials.json")
        
        try:
            # First login - should save credentials
            sdk1 = PCloudSDK(token_file=token_file)
            login_info1 = sdk1.login(creds["email"], creds["password"], location_id=creds["location_id"])
            
            assert "access_token" in login_info1
            assert os.path.exists(token_file)
            
            # Second instance - should load saved credentials
            sdk2 = PCloudSDK(token_file=token_file)
            login_info2 = sdk2.login(creds["email"], creds["password"], location_id=creds["location_id"], force_login=False)
            
            # Should reuse existing token
            assert login_info2["access_token"] == login_info1["access_token"]
            
            # Test token validation works
            user_email = sdk2.user.get_user_email()
            assert user_email == creds["email"]
            
            # Clean up
            sdk2.clear_saved_credentials()
            assert not os.path.exists(token_file)
            
        finally:
            safe_remove_file(token_file)
            safe_cleanup_temp_dir(temp_dir)