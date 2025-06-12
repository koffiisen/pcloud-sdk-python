"""
Unit tests for the refactored pcloud_sdk.user_operations.User class,
focusing on on-demand userinfo fetching and caching.
"""

import pytest
import responses
import requests # Added import

from pcloud_sdk.account import Account
from pcloud_sdk.user_operations import User
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.request import Request # Though we mock at a higher level via responses
from pcloud_sdk.config import Config # For API host resolution by Request

# Sample userinfo API response
SAMPLE_USER_INFO_RESPONSE = {
    "result": 0,
    "userid": 12345,
    "email": "test@example.com",
    "emailverified": True,
    "usedquota": 1000000,
    "quota": 10000000,
    "publiclinkquota": 50000000,
    "registered": "Thu, 01 Jan 2015 00:00:00 +0000",
    # ... other fields
}

SAMPLE_USER_INFO_RESPONSE_UPDATED = {
    "result": 0,
    "userid": 12345, # Same userid
    "email": "updated_test@example.com", # Email changed
    "emailverified": True,
    "usedquota": 2000000, # Quota used changed
    "quota": 10000000,
    "publiclinkquota": 50000000,
    "registered": "Thu, 01 Jan 2015 00:00:00 +0000",
}


class TestUserOperations:
    """Tests for the User class with on-demand userinfo fetching."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_account = Account(account_id="user_test@example.com")
        # Account needs to be "authenticated" for Request to include token,
        # though for userinfo, it might not be strictly necessary if getauth=1 is used.
        # However, User ops are typically used with an authenticated account.
        self.mock_account.set_credentials(access_token="fake_test_token", location_id=1, auth_type="direct")
        self.user_ops = User(self.mock_account)

        # Determine the API host that Request will use based on account's location_id
        self.api_host = Config.get_api_host_by_location_id(self.mock_account.location_id)


    @responses.activate
    def test_initialization_is_lightweight(self):
        """Assert that no API call is made upon User instantiation."""
        # responses.calls will be empty if no HTTP request is made
        assert len(responses.calls) == 0
        assert self.user_ops._user_info is None

    @responses.activate
    def test_get_user_info_fetches_on_first_call_and_caches(self):
        """Test get_user_info() fetches from API on first call and caches the result."""
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            json=SAMPLE_USER_INFO_RESPONSE,
            status=200
        )

        # First call
        info1 = self.user_ops.get_user_info()
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f"{self.api_host}userinfo?auth={self.mock_account.access_token}"
        assert self.user_ops._user_info == SAMPLE_USER_INFO_RESPONSE
        assert info1 == SAMPLE_USER_INFO_RESPONSE

        # Second call
        info2 = self.user_ops.get_user_info()
        assert len(responses.calls) == 1  # API should not be called again
        assert info2 == SAMPLE_USER_INFO_RESPONSE # Should return cached data

    @responses.activate
    def test_getters_use_cached_user_info(self):
        """Test that individual getter methods use cached user_info after first fetch."""
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            json=SAMPLE_USER_INFO_RESPONSE,
            status=200
        )

        # Call a getter, e.g., get_user_id()
        user_id = self.user_ops.get_user_id()
        assert len(responses.calls) == 1 # API called for the first getter
        assert user_id == SAMPLE_USER_INFO_RESPONSE["userid"]
        assert self.user_ops._user_info is not None # Cache should be populated

        # Call another getter, e.g., get_email()
        email = self.user_ops.get_user_email()
        assert len(responses.calls) == 1 # API should NOT be called again
        assert email == SAMPLE_USER_INFO_RESPONSE["email"]

        # Call other getters to confirm
        assert self.user_ops.get_quota() == SAMPLE_USER_INFO_RESPONSE["quota"]
        assert self.user_ops.get_used_quota() == SAMPLE_USER_INFO_RESPONSE["usedquota"]
        assert self.user_ops.get_public_link_quota() == SAMPLE_USER_INFO_RESPONSE["publiclinkquota"]
        assert len(responses.calls) == 1 # Still only one API call

    @responses.activate
    def test_refresh_user_info_forces_api_call(self):
        """Test that refresh_user_info() forces a new API call and updates cache."""
        # Initial API response
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            json=SAMPLE_USER_INFO_RESPONSE,
            status=200,
            match_querystring=False # Allow multiple GETs to same URL with different responses
        )

        # First call to populate cache
        info1 = self.user_ops.get_user_info()
        assert len(responses.calls) == 1
        assert info1["email"] == SAMPLE_USER_INFO_RESPONSE["email"]
        assert self.user_ops._user_info["email"] == SAMPLE_USER_INFO_RESPONSE["email"]

        # Update mock to return different data for the next call
        # responses.reset() # Clear previous mocks if using unique URLs per call
        # For same URL, need to ensure responses handles this. Often it's FIFO.
        # Or, explicitly remove and re-add if responses library requires it for same URL.
        # For this test, let's assume responses.add just adds to a list of potential matches
        # and the last added one that matches is used, or it's FIFO.
        # A safer way if responses are sequential for the same URL:
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo", # Same URL
            json=SAMPLE_USER_INFO_RESPONSE_UPDATED, # Different response
            status=200,
            match_querystring=False
        )

        # Call refresh_user_info()
        refreshed_info = self.user_ops.refresh_user_info()
        assert len(responses.calls) == 2 # API should be called again
        assert self.user_ops._user_info == SAMPLE_USER_INFO_RESPONSE_UPDATED
        assert refreshed_info == SAMPLE_USER_INFO_RESPONSE_UPDATED
        assert refreshed_info["email"] == SAMPLE_USER_INFO_RESPONSE_UPDATED["email"]


        # Call get_user_info() again to ensure it returns the new cached data
        info3 = self.user_ops.get_user_info()
        assert len(responses.calls) == 2 # API should NOT be called a third time
        assert info3 == SAMPLE_USER_INFO_RESPONSE_UPDATED

    @responses.activate
    def test_get_user_info_api_error(self):
        """Test get_user_info() when API returns an error."""
        error_response = {"result": 2000, "error": "User not logged in."}
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            json=error_response,
            status=200 # pCloud API often returns 200 OK with error in JSON body
        )

        with pytest.raises(PCloudException, match="User not logged in."):
            self.user_ops.get_user_info()

        assert self.user_ops._user_info is None # Cache should remain None on error

    @responses.activate
    def test_get_user_info_network_error(self):
        """Test get_user_info() when a network error occurs."""
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            body=requests.exceptions.ConnectionError("Simulated network failure")
        )

        with pytest.raises(PCloudException, match="Network error during API request"): # Assuming Request class wraps this
            self.user_ops.get_user_info()
        assert self.user_ops._user_info is None

    @responses.activate
    def test_get_user_info_bad_json(self):
        """Test get_user_info() when API returns malformed JSON."""
        responses.add(
            responses.GET,
            f"{self.api_host}userinfo",
            body="This is not JSON",
            status=200,
            content_type="application/json"
        )
        with pytest.raises(PCloudException, match="Failed to decode JSON response from API"): # Assuming Request class wraps this
            self.user_ops.get_user_info()
        assert self.user_ops._user_info is None
