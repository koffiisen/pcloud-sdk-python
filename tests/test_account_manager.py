"""
Unit tests for the pcloud_sdk.account_manager.AccountManager class.
"""

import pytest

from pcloud_sdk.account_manager import AccountManager
from pcloud_sdk.account import Account


class TestAccountManagerInitialization:
    """Tests for AccountManager initialization."""

    def test_initialization_empty(self):
        """Test AccountManager initialization with no arguments."""
        manager = AccountManager()
        assert manager.accounts == {}
        assert manager.app_key == ""
        assert manager.app_secret == ""

    def test_initialization_with_app_credentials(self):
        """Test AccountManager initialization with app_key and app_secret."""
        app_key = "test_app_key"
        app_secret = "test_app_secret"
        manager = AccountManager(app_key=app_key, app_secret=app_secret)
        assert manager.accounts == {}
        assert manager.app_key == app_key
        assert manager.app_secret == app_secret

    def test_set_get_global_app_credentials(self):
        """Test setting and getting global app credentials after initialization."""
        manager = AccountManager()
        assert manager.app_key == ""
        assert manager.app_secret == ""

        new_app_key = "new_key"
        new_app_secret = "new_secret"
        manager.set_global_app_credentials(app_key=new_app_key, app_secret=new_app_secret)

        assert manager.app_key == new_app_key
        assert manager.app_secret == new_app_secret

        creds = manager.get_global_app_credentials()
        assert creds["app_key"] == new_app_key
        assert creds["app_secret"] == new_app_secret


class TestAccountManagementOperations:
    """Tests for account management operations in AccountManager."""

    def setup_method(self):
        """Setup for each test method."""
        self.manager = AccountManager()
        self.account1 = Account(account_id="user1@example.com", email="user1@example.com")
        self.account2 = Account(account_id="user2@example.com", email="user2@example.com")

    def test_add_account_success(self):
        """Test adding a new account successfully."""
        self.manager.add_account(self.account1)
        assert self.account1.account_id in self.manager.accounts
        assert self.manager.accounts[self.account1.account_id] == self.account1

    def test_add_account_duplicate_id(self):
        """Test adding an account with an account_id that already exists."""
        self.manager.add_account(self.account1)
        with pytest.raises(ValueError, match=f"Account with ID '{self.account1.account_id}' already exists."):
            self.manager.add_account(self.account1) # Adding the same account instance

        # Also test with a different account instance but same ID
        account1_duplicate = Account(account_id=self.account1.account_id, email="another_user1@example.com")
        with pytest.raises(ValueError, match=f"Account with ID '{self.account1.account_id}' already exists."):
            self.manager.add_account(account1_duplicate)


    def test_get_account_success(self):
        """Test retrieving an existing account."""
        self.manager.add_account(self.account1)
        retrieved_account = self.manager.get_account(self.account1.account_id)
        assert retrieved_account == self.account1

    def test_get_account_not_found(self):
        """Test retrieving a non-existent account_id."""
        non_existent_id = "nonexistent@example.com"
        with pytest.raises(KeyError, match=f"Account with ID '{non_existent_id}' not found."):
            self.manager.get_account(non_existent_id)

    def test_remove_account_success(self):
        """Test removing an existing account."""
        self.manager.add_account(self.account1)
        assert self.account1.account_id in self.manager.accounts

        self.manager.remove_account(self.account1.account_id)
        assert self.account1.account_id not in self.manager.accounts

    def test_remove_account_not_found(self):
        """Test removing a non-existent account_id."""
        non_existent_id = "nonexistent@example.com"
        with pytest.raises(KeyError, match=f"Account with ID '{non_existent_id}' not found."):
            self.manager.remove_account(non_existent_id)

    def test_list_accounts_empty(self):
        """Test list_accounts when no accounts have been added."""
        accounts_list = self.manager.list_accounts()
        assert isinstance(accounts_list, list)
        assert len(accounts_list) == 0

    def test_list_accounts_with_accounts(self):
        """Test list_accounts after adding multiple accounts."""
        self.manager.add_account(self.account1)
        self.manager.add_account(self.account2)

        accounts_list = self.manager.list_accounts()
        assert isinstance(accounts_list, list)
        assert len(accounts_list) == 2
        # Check if the actual Account objects are in the list
        assert self.account1 in accounts_list
        assert self.account2 in accounts_list
        # Verify they are not the same object if that's a concern (not here, they are distinct)
        assert accounts_list[0] is not accounts_list[1] if len(accounts_list) > 1 else True

    def test_list_accounts_after_removal(self):
        """Test list_accounts after adding and then removing an account."""
        self.manager.add_account(self.account1)
        self.manager.add_account(self.account2)
        self.manager.remove_account(self.account1.account_id)

        accounts_list = self.manager.list_accounts()
        assert len(accounts_list) == 1
        assert self.account1 not in accounts_list
        assert self.account2 in accounts_list
