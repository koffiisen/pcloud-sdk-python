from typing import Any, Dict, Optional # Added Optional

from pcloud_sdk.account import Account
from pcloud_sdk.request import Request


class User:
    """User class for user information"""

    def __init__(self, account: Account):
        """
        Initializes User operations for a specific pCloud account.
        User information is fetched on demand.

        Args:
            account: The Account object to use for API requests.
        """
        self.request = Request(account)
        self.account = account  # Store account for potential future use
        self._user_info: Optional[Dict[str, Any]] = None  # Cache for user_info

    def get_user_info(self) -> Dict[str, Any]:
        """
        Retrieves full user information for the account.
        Fetches from API if not already cached for this instance.
        """
        if self._user_info is None:
            print(f"Fetching userinfo for account: {self.account.account_id}")
            self._user_info = self.request.get("userinfo")

        if self._user_info is None: # Should not happen if request.get works or raises
            raise Exception("Failed to retrieve user_info.")
        return self._user_info

    def refresh_user_info(self) -> Dict[str, Any]:
        """
        Forces a refresh of the cached user information from the API.

        Returns:
            The newly fetched user information dictionary.
        """
        self._user_info = None
        return self.get_user_info()

    def get_user_id(self) -> int:
        """Get user ID from cached user info."""
        user_info = self.get_user_info()
        return int(user_info["userid"])

    def get_user_email(self) -> str:
        """Get user email from cached user info."""
        user_info = self.get_user_info()
        return str(user_info["email"])

    def get_used_quota(self) -> int:
        """Get used quota in bytes from cached user info."""
        user_info = self.get_user_info()
        return int(user_info["usedquota"])

    def get_quota(self) -> int:
        """Get total quota in bytes from cached user info."""
        user_info = self.get_user_info()
        return int(user_info["quota"])

    def get_public_link_quota(self) -> int:
        """Get public link quota from cached user info."""
        user_info = self.get_user_info()
        # Ensure the key exists, providing a default if it might be missing
        return int(user_info.get("publiclinkquota", 0))
