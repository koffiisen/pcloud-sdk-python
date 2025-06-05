"""
pCloud SDK for Python
Converted from the PHP SDK

This package provides a Python interface to the pCloud API.
"""

import os
import time
import warnings
import json
from typing import Any, Dict, Optional, List, Callable # Added Callable
from urllib.parse import urlencode

from pcloud_sdk.account import Account
from pcloud_sdk.account_manager import AccountManager
from pcloud_sdk.config import Config # Added for get_auth_url (API host)
from pcloud_sdk.exceptions import PCloudException
# File, Folder, User imports are fine for now, will be addressed when operation access is refactored
from pcloud_sdk.file_operations import File
from pcloud_sdk.folder_operations import Folder
from pcloud_sdk.user_operations import User


class PCloudSDK:
    """
    Convenient wrapper class for the pCloud SDK with integrated token management
    """

    def __init__(
        self,
        app_key: str = "", # Retained for AccountManager
        app_secret: str = "", # Retained for AccountManager
        token_manager: bool = True,
        token_file: str = ".pcloud_accounts", # Renamed for clarity
        token_staleness_days: int = 30, # This might become per-account later
    ):
        """
        Initialize the pCloud SDK for multi-account management.

        Args:
            app_key: Your pCloud app key (Client ID). Global for the SDK.
            app_secret: Your pCloud app secret (Client Secret). Global for the SDK.
            token_manager: Enable automatic token management (default True).
            token_file: File to store account credentials (default .pcloud_accounts).
            token_staleness_days: Number of days after which saved credentials
                are considered stale (default 30). This is a general setting;
                staleness might be checked per account.
        """
        self.account_manager = AccountManager(app_key=app_key, app_secret=app_secret)

        # Token management
        self.token_manager_enabled = token_manager
        self.token_file = token_file
        self.token_staleness_days = token_staleness_days # Keep for now

        if token_manager:
            self._load_saved_credentials()

        # Remove self._user, self._folder, self._file initializations
        # self._user = None
        # self._folder = None
        # self._file = None

    def _save_all_accounts_credentials(self) -> None:
        """Save all managed account credentials to file if token manager is enabled."""
        if not self.token_manager_enabled:
            return

        accounts_data = []
        for account in self.account_manager.list_accounts():
            accounts_data.append(account.get_info())

        try:
            with open(self.token_file, "w") as f:
                json.dump(accounts_data, f, indent=2)
            print(f"✅ All account credentials saved in {self.token_file}")
        except (IOError, OSError) as e:
            print(f"⚠️ Could not save account credentials to {self.token_file}: {e}")

    def _load_saved_credentials(self) -> bool:
        """Load account credentials from file if available."""
        if not self.token_manager_enabled or not os.path.exists(self.token_file):
            return False

        try:
            with open(self.token_file, "r") as f:
                accounts_data = json.load(f)

            if not isinstance(accounts_data, list):
                print(f"⚠️ Credentials file {self.token_file} does not contain a list of accounts. Skipping load.")
                return False

            loaded_count = 0
            for account_info in accounts_data:
                if not isinstance(account_info, dict):
                    print(f"⚠️ Skipping non-dictionary item in credentials file.")
                    continue

                # Use email as account_id if present, otherwise skip or generate one (simplifying for now)
                account_id = account_info.get("email") or account_info.get("account_id")
                if not account_id:
                    print(f"⚠️ Skipping account data with missing 'email' or 'account_id'. {account_info}")
                    continue

                # Staleness check (optional, can be enhanced per account)
                saved_at = account_info.get("saved_at", 0) # Assuming get_info() could provide this
                if saved_at: # Only check if saved_at is present
                    age_days = (time.time() - saved_at) / (24 * 3600)
                    if age_days > self.token_staleness_days:
                        print(
                            f"⚠️ Credentials for account {account_id} ({age_days:.1f} days old) "
                            f"might be stale (limit is {self.token_staleness_days} days)."
                        )
                        # Decide if stale credentials should prevent loading or just warn
                        # For now, we'll load them and they can be re-authenticated later.

                # Create and populate account object
                acc = Account(
                    account_id=account_id,
                    access_token=account_info.get("access_token", ""),
                    location_id=account_info.get("location_id", 1), # Default to US or make it mandatory
                    auth_type=account_info.get("auth_type", "oauth2"),
                    app_key=account_info.get("app_key", self.account_manager.app_key), # Use global or per-account
                    app_secret=account_info.get("app_secret", self.account_manager.app_secret),
                    redirect_uri=account_info.get("redirect_uri", ""),
                    email=account_info.get("email", ""),
                    user_id=account_info.get("user_id"),
                    quota=account_info.get("quota"),
                    used_quota=account_info.get("used_quota"),
                    is_authenticated=bool(account_info.get("access_token")), # True if token exists
                    curl_exec_timeout=account_info.get("curl_exec_timeout", 3600)
                )

                try:
                    self.account_manager.add_account(acc)
                    loaded_count +=1
                except ValueError as e: # Account already exists
                    print(f"⚠️ While loading: {e}")


            if loaded_count > 0:
                print(f"🔄 Loaded {loaded_count} account(s) from {self.token_file}")
            return True

        except FileNotFoundError:
            return False # Not an error, just no saved credentials
        except (IOError, OSError) as e:
            print(f"⚠️ Could not read credentials from {self.token_file}: {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"⚠️ Error decoding JSON from {self.token_file}: {e}")
            return False
        return False

    # def _test_existing_credentials(self) -> bool: # Obsolete or needs account_id
    #     """Test if existing credentials still work"""
    #     # This needs to be adapted for a specific account
    #     print("⚠️ _test_existing_credentials needs to be adapted for multi-account")
    #     return False

    def get_file_operations(self, account_id: str) -> File:
        """
        Get a File operations handler for the specified account.

        Args:
            account_id: The ID of the account to use.

        Returns:
            A File object initialized for the given account.

        Raises:
            PCloudException: If the account is not found or not authenticated.
        """
        try:
            account = self.account_manager.get_account(account_id)
        except KeyError:
            raise PCloudException(f"Account with ID '{account_id}' not found.")

        if not account.is_authenticated:
            raise PCloudException(f"Account '{account_id}' is not authenticated. Please login first.")
        return File(account)

    def get_folder_operations(self, account_id: str) -> Folder:
        """
        Get a Folder operations handler for the specified account.

        Args:
            account_id: The ID of the account to use.

        Returns:
            A Folder object initialized for the given account.

        Raises:
            PCloudException: If the account is not found or not authenticated.
        """
        try:
            account = self.account_manager.get_account(account_id)
        except KeyError:
            raise PCloudException(f"Account with ID '{account_id}' not found.")

        if not account.is_authenticated:
            raise PCloudException(f"Account '{account_id}' is not authenticated. Please login first.")
        return Folder(account)

    def get_user_operations(self, account_id: str) -> User:
        """
        Get a User operations handler for the specified account.
        Note: Instantiating User currently fetches userinfo immediately.

        Args:
            account_id: The ID of the account to use.

        Returns:
            A User object initialized for the given account.

        Raises:
            PCloudException: If the account is not found or not authenticated.
        """
        try:
            account = self.account_manager.get_account(account_id)
        except KeyError:
            raise PCloudException(f"Account with ID '{account_id}' not found.")

        if not account.is_authenticated:
            raise PCloudException(f"Account '{account_id}' is not authenticated. Please login first.")
        return User(account)

    def clear_saved_credentials(self) -> None:
        """Clear saved credentials file and all managed accounts."""
        if self.token_manager_enabled and os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
                print(f"🧹 Credentials file {self.token_file} deleted.")
            except PermissionError as e:
                print(
                    f"⚠️ Could not delete credentials from {self.token_file} "
                    f"due to a permission error: {e}"
                )
            except OSError as e:
                print(f"⚠️ Error deleting credentials from {self.token_file}: {e}")
            except Exception as e:
                print(
                    f"⚠️ An unexpected error occurred while deleting "
                    f"credentials: {e}"
                )
        # Clear accounts from the manager
        self.account_manager.accounts = {}
        print("🧹 All accounts cleared from manager.")

    # get_saved_email is obsolete, access email via Account object

    # Old properties for user, folder, file are removed. Use get_xxx_operations(account_id) instead.

    # @property
    # def user(self) -> User:
    #     """Get User instance"""
    #     # This is replaced by get_user_operations(account_id)
    #     raise NotImplementedError("Use get_user_operations(account_id) instead.")

    # @property
    # def folder(self) -> Folder:
    #     """Get Folder instance"""
    #     # This is replaced by get_folder_operations(account_id)
    #     raise NotImplementedError("Use get_folder_operations(account_id) instead.")

    # @property
    # def file(self) -> File:
    #     """Get File instance"""
    #     # This is replaced by get_file_operations(account_id)
    #     raise NotImplementedError("Use get_file_operations(account_id) instead.")

    def get_auth_url(self, redirect_uri: str = "") -> str:
        """
        Get OAuth2 authorization URL.

        Args:
            redirect_uri: Optional specific redirect URI for this authorization request.
                          If not provided, a globally configured one on AccountManager might be used
                          by pCloud, or pCloud's default for the app.

        Returns:
            The pCloud OAuth2 authorization URL.

        Raises:
            PCloudException: If the app_key (client_id) is not set.
        """
        if not self.account_manager.app_key:
            raise PCloudException(
                "Cannot generate OAuth URL: App Key (Client ID) is not configured."
            )

        # pCloud OAuth2 authorize endpoint. EU is default, but this endpoint is global.
        # Location for API calls is distinct from OAuth endpoint host.
        # Standard pCloud OAuth URL:
        oauth_host = "https://my.pcloud.com/oauth2/authorize" # This is a fixed pCloud URL

        params = {
            "client_id": self.account_manager.app_key,
            "response_type": "code",
        }

        final_redirect_uri = redirect_uri
        # Potentially: if not redirect_uri and self.account_manager.default_redirect_uri:
        #    final_redirect_uri = self.account_manager.default_redirect_uri

        if final_redirect_uri:
            params["redirect_uri"] = final_redirect_uri

        return f"{oauth_host}?{urlencode(params)}"

    def authenticate(self, code: str, location_id: int, account_id: str) -> Account:
        """
        Exchange authorization code for access token and associate with an account.

        Args:
            code: The authorization code from pCloud OAuth callback.
            location_id: The server location ID for the account.
            account_id: The identifier for the account being authenticated. This could be
                        an email or a temporary ID used to track the OAuth flow.

        Returns:
            The authenticated Account object.

        Raises:
            PCloudException: If authentication fails or app credentials are not set.
        """
        if not self.account_manager.app_key or not self.account_manager.app_secret:
            raise PCloudException(
                "OAuth authentication failed: App Key or App Secret is not configured."
            )

        try:
            account = self.account_manager.get_account(account_id)
        except KeyError:
            # If account_id was a temporary ID, we might want to update it to the email later
            # For now, use the provided account_id. The email will be set by perform_oauth_exchange.
            print(f"Creating new account for OAuth authentication with ID: {account_id}")
            account = Account(account_id=account_id)
            # If redirect_uri was part of the initial get_auth_url call and stored temporarily
            # it could be set on the account here, e.g. account.redirect_uri = pre_stored_redirect_uri

        account.perform_oauth_exchange(
            code,
            location_id,
            self.account_manager.app_key,
            self.account_manager.app_secret,
        )

        # Ensure the account is in the manager, especially if it was new
        # or if account_id might change (e.g. from temp ID to email after auth)
        # For now, assume account_id remains consistent or perform_oauth_exchange updates it.
        self.account_manager.add_account(account) # add_account handles if it already exists by ID

        if self.token_manager_enabled:
            self._save_all_accounts_credentials()

        print(f"✅ Account {account.account_id} (Email: {account.email or 'N/A'}) authenticated via OAuth.")
        return account

    def login(
        self, email: str, password: str, location_id: int = 1, force_login: bool = False
    ) -> Account:
        """
        Login with email/password for a specific account.

        Args:
            email: pCloud email (acts as account_id).
            password: pCloud password.
            location_id: Server location (1=US, 2=EU). Default is 1 (US).
            force_login: Force new login even if credentials seem valid.

        Returns:
            The authenticated Account object.

        Raises:
            PCloudException: If login fails.
        """
        account_id = email  # Use email as the primary account identifier

        try:
            account = self.account_manager.get_account(account_id)
            if not force_login and account.is_authenticated:
                # TODO: Add staleness check here if desired
                # e.g., if account.get_info().get("saved_at") and not self._is_token_stale(...)
                print(f"Account {account_id} is already authenticated. Skipping new login unless forced.")
                return account
            print(f"Attempting to re-authenticate or force login for account: {account_id}")
        except KeyError:
            print(f"Creating new account for login: {account_id}")
            account = Account(account_id=account_id, email=email)
            # No need to add to manager yet, do it after successful login

        try:
            account.perform_direct_login(email, password, location_id)
            # Login successful, add/update in manager
            self.account_manager.add_account(account) # Handles update if account was fetched

            if self.token_manager_enabled:
                self._save_all_accounts_credentials()
            print(f"✅ Account {account.account_id} logged in successfully.")
            return account
        except PCloudException as e:
            print(f"⚠️ Login failed for account {account.account_id}: {e}")
            raise # Re-raise the exception after logging

    # login_or_load is deprecated and removed.

    # set_access_token (global) is obsolete.

    # is_authenticated (global) is obsolete. Check per account.

    def logout(self, account_id: str) -> None:
        """
        Logs out a specific account by clearing its credentials.
        The account object remains in the manager but will be marked as not authenticated.
        Its credentials (token etc.) are cleared.

        Args:
            account_id: The ID of the account to logout.

        Raises:
            KeyError: If the account_id is not found in the AccountManager.
        """
        try:
            account = self.account_manager.get_account(account_id)
            account.clear_credentials()
            print(f"🚪 Account {account_id} credentials cleared (logged out).")

            if self.token_manager_enabled:
                self._save_all_accounts_credentials()
        except KeyError:
            print(f"⚠️ Logout failed: Account with ID '{account_id}' not found.")
            raise # Or handle more gracefully depending on desired behavior

    # def get_credentials_info(self) -> Dict[str, Any]: # Needs to be account specific or list all
    #     """Get information about managed accounts."""
    #     # Could list all accounts and their status, or info for a specific one.
    #     print("⚠️ get_credentials_info needs refactoring for multi-account.")
    #     all_accounts_info = []
    #     for acc_id, acc in self.account_manager.accounts.items():
    #         all_accounts_info.append({
    #             "account_id": acc_id,
    #             "email": acc.email,
    #             "is_authenticated": acc.is_authenticated,
    #             "location_id": acc.location_id,
    #         })
    #     if not all_accounts_info:
    #         return {"message": "No accounts managed or loaded."}
    #     return {"managed_accounts": all_accounts_info}

    def find_file_in_accounts(self, filename: str, folder_id: Optional[int] = 0) -> List[Dict[str, Any]]:
        """
        Searches for a file by its name within a specific folder ID across all authenticated accounts.
        This search is non-recursive for the specified folder_id.

        Args:
            filename: The name of the file to search for.
            folder_id: The ID of the folder to search within. Defaults to 0 (root folder).

        Returns:
            A list of dictionaries, where each dictionary is the metadata of a found file,
            augmented with 'account_id_found_in' and 'account_email_found_in'.
            Returns an empty list if the file is not found in any account or if no
            accounts are authenticated.
        """
        found_files_results: List[Dict[str, Any]] = []

        for account in self.account_manager.list_accounts():
            if not account.is_authenticated:
                print(f"Skipping account {account.account_id} (Email: {account.email or 'N/A'}) as it is not authenticated.")
                continue

            print(f"Searching for '{filename}' in folder ID {folder_id} of account: {account.account_id} (Email: {account.email or 'N/A'})")
            try:
                folder_ops = self.get_folder_operations(account.account_id)
                # Use get_content to directly get the list of items in the folder
                contents = folder_ops.get_content(folder_id=folder_id if folder_id is not None else 0)

                for item in contents:
                    if item.get('isfile', False) and item.get('name') == filename:
                        found_info = item.copy()
                        found_info['account_id_found_in'] = account.account_id
                        found_info['account_email_found_in'] = account.email
                        found_files_results.append(found_info)
                        print(f"  Found '{filename}' in account {account.account_id}.")

            except PCloudException as e:
                print(f"⚠️ Could not search in account {account.account_id} (Email: {account.email or 'N/A'}): {e}")
            except Exception as e: # Catch any other unexpected error for this account
                print(f"⚠️ An unexpected error occurred while searching in account {account.account_id} (Email: {account.email or 'N/A'}): {e}")

        if not found_files_results:
            print(f"File '{filename}' not found in folder ID {folder_id} across any authenticated accounts.")

        return found_files_results

    def select_account_for_upload(self, file_size: int) -> Account:
        """
        Selects an authenticated account with sufficient free space for a file.

        Args:
            file_size: The size of the file to be uploaded, in bytes.

        Returns:
            An Account object that can accommodate the file.

        Raises:
            PCloudException: If no authenticated account has enough free space.
        """
        suitable_accounts = []
        for account in self.account_manager.list_accounts():
            if account.is_authenticated:
                try:
                    # Ensure User operations can be fetched for quota check
                    user_ops = self.get_user_operations(account.account_id)
                    total_quota = user_ops.get_quota() # Assuming this is already fetched by User.__init__ or is cheap
                    used_quota = user_ops.get_used_quota()

                    # Ensure quota and used_quota are not None
                    if total_quota is None or used_quota is None:
                        print(f"⚠️ Account {account.account_id} has missing quota information. Skipping.")
                        continue

                    free_space = total_quota - used_quota
                    if free_space >= file_size:
                        suitable_accounts.append((account, free_space))
                except PCloudException as e:
                    # This might happen if get_user_operations fails (e.g. account became unauth)
                    print(f"Could not get user operations for account {account.account_id}: {e}")
                    continue # Skip this account

        if not suitable_accounts:
            raise PCloudException("No authenticated account found with sufficient space for the upload.")

        # Optional: Select the account with the most free space, or just the first one.
        # For now, let's pick the one with most free space to be 'smarter'.
        suitable_accounts.sort(key=lambda x: x[1], reverse=True)
        selected_account, _ = suitable_accounts[0]

        print(f"Selected account {selected_account.account_id} (Email: {selected_account.email}) for upload.")
        return selected_account

    def upload_to_suitable_account(
        self,
        file_path: str,
        folder_id: int = 0,
        filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Uploads a file to a suitable pCloud account that has enough space.
        The account is selected automatically based on available quota.

        Args:
            file_path: The local path to the file to be uploaded.
            folder_id: The destination folder ID on pCloud (default is 0 for root).
            filename: Optional name for the file on pCloud. If None, uses local filename.
            progress_callback: Optional callback function for progress updates.
                               (e.g., def callback(current, total, percentage, speed, status, filename, error=None))

        Returns:
            A dictionary containing the API response from the upload operation,
            augmented with 'account_id' and 'account_email' of the account used.

        Raises:
            PCloudException: If no suitable account is found or if the upload fails.
            FileNotFoundError: If the local file_path does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local file not found: {file_path}")

        file_size = os.path.getsize(file_path)

        selected_account = self.select_account_for_upload(file_size)

        print(f"Attempting upload of '{file_path}' to account: {selected_account.account_id} (Email: {selected_account.email})")

        file_ops = self.get_file_operations(selected_account.account_id)

        upload_result = file_ops.upload(
            file_path=file_path,
            folder_id=folder_id,
            filename=filename,
            progress_callback=progress_callback,
        )

        # Augment the result
        upload_result["account_id_used"] = selected_account.account_id
        upload_result["account_email_used"] = selected_account.email

        return upload_result
