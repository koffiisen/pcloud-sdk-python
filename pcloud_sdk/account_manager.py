from typing import Dict, List
from pcloud_sdk.account import Account

class AccountManager:
    """Manages multiple pCloud accounts and global application settings."""

    def __init__(self, app_key: str = "", app_secret: str = ""):
        """
        Initializes an AccountManager instance.

        Args:
            app_key: The global application key for OAuth.
            app_secret: The global application secret for OAuth.
        """
        self.accounts: Dict[str, Account] = {}
        self.app_key = app_key
        self.app_secret = app_secret

    def add_account(self, account: Account) -> None:
        """
        Adds an Account object to the manager.

        Args:
            account: The Account object to add.

        Raises:
            ValueError: If an account with the same account_id already exists.
        """
        if account.account_id in self.accounts:
            raise ValueError(
                f"Account with ID '{account.account_id}' already exists."
            )
        self.accounts[account.account_id] = account

    def remove_account(self, account_id: str) -> None:
        """
        Removes an account by its account_id.

        Args:
            account_id: The ID of the account to remove.

        Raises:
            KeyError: If the account with the given ID does not exist.
        """
        if account_id not in self.accounts:
            raise KeyError(f"Account with ID '{account_id}' not found.")
        del self.accounts[account_id]

    def get_account(self, account_id: str) -> Account:
        """
        Retrieves an account by its account_id.

        Args:
            account_id: The ID of the account to retrieve.

        Returns:
            The Account object.

        Raises:
            KeyError: If the account with the given ID does not exist.
        """
        if account_id not in self.accounts:
            raise KeyError(f"Account with ID '{account_id}' not found.")
        return self.accounts[account_id]

    def list_accounts(self) -> List[Account]:
        """
        Returns a list of all managed Account objects.

        Returns:
            A list of Account objects.
        """
        return list(self.accounts.values())

    def set_global_app_credentials(self, app_key: str, app_secret: str) -> None:
        """
        Sets or updates the global application credentials.

        Args:
            app_key: The global application key.
            app_secret: The global application secret.
        """
        self.app_key = app_key
        self.app_secret = app_secret

    def get_global_app_credentials(self) -> Dict[str, str]:
        """
        Retrieves the global application credentials.

        Returns:
            A dictionary containing 'app_key' and 'app_secret'.
        """
        return {"app_key": self.app_key, "app_secret": self.app_secret}
