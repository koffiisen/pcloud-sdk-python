"""
Unit tests for multi-account logic in pcloud_sdk.core.PCloudSDK.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, Mock, MagicMock

from pcloud_sdk import PCloudSDK
from pcloud_sdk.account import Account
from pcloud_sdk.account_manager import AccountManager
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.user_operations import User
from pcloud_sdk.file_operations import File
from pcloud_sdk.folder_operations import Folder


class TestSelectAccountForUpload:
    """Tests for PCloudSDK.select_account_for_upload method."""

    def setup_method(self):
        self.sdk = PCloudSDK(token_manager=False) # Disable token manager for these unit tests
        # Mock AccountManager directly on the sdk instance for simplicity in controlling list_accounts
        self.sdk.account_manager = Mock(spec=AccountManager)

    def test_select_no_accounts(self):
        """Test selection when no accounts are managed."""
        self.sdk.account_manager.list_accounts.return_value = []
        with pytest.raises(PCloudException, match="No authenticated account found with sufficient space"):
            self.sdk.select_account_for_upload(file_size=1000)

    def test_select_no_authenticated_accounts(self):
        """Test selection when accounts exist but none are authenticated."""
        acc1 = Account(account_id="user1@example.com", is_authenticated=False)
        self.sdk.account_manager.list_accounts.return_value = [acc1]
        with pytest.raises(PCloudException, match="No authenticated account found with sufficient space"):
            self.sdk.select_account_for_upload(file_size=1000)

    def test_select_no_account_with_enough_space(self):
        """Test selection when authenticated accounts lack sufficient space."""
        acc1 = Account(account_id="user1@example.com", is_authenticated=True)

        mock_user_ops = Mock(spec=User)
        mock_user_ops.get_quota.return_value = 10000
        mock_user_ops.get_used_quota.return_value = 9500 # 500 free

        with patch.object(self.sdk, 'get_user_operations', return_value=mock_user_ops) as mock_get_user_ops:
            self.sdk.account_manager.list_accounts.return_value = [acc1]
            with pytest.raises(PCloudException, match="No authenticated account found with sufficient space"):
                self.sdk.select_account_for_upload(file_size=1000) # Needs 1000, has 500
            mock_get_user_ops.assert_called_once_with(acc1.account_id)


    def test_select_one_account_with_enough_space(self):
        """Test selection when one account has enough space."""
        acc1 = Account(account_id="user1@example.com", is_authenticated=True)
        mock_user_ops = Mock(spec=User)
        mock_user_ops.get_quota.return_value = 10000
        mock_user_ops.get_used_quota.return_value = 8000 # 2000 free

        with patch.object(self.sdk, 'get_user_operations', return_value=mock_user_ops):
            self.sdk.account_manager.list_accounts.return_value = [acc1]
            selected_account = self.sdk.select_account_for_upload(file_size=1000)
            assert selected_account == acc1

    def test_select_multiple_accounts_picks_one_with_most_space(self):
        """Test selection picks account with most free space from multiple suitable accounts."""
        acc1 = Account(account_id="user1@example.com", email="user1@example.com", is_authenticated=True)
        acc2 = Account(account_id="user2@example.com", email="user2@example.com", is_authenticated=True)
        acc3 = Account(account_id="user3@example.com", email="user3@example.com", is_authenticated=True) # Not enough space

        user_ops1 = Mock(spec=User)
        user_ops1.get_quota.return_value = 10000
        user_ops1.get_used_quota.return_value = 7000  # 3000 free

        user_ops2 = Mock(spec=User)
        user_ops2.get_quota.return_value = 20000
        user_ops2.get_used_quota.return_value = 15000 # 5000 free (most free)

        user_ops3 = Mock(spec=User)
        user_ops3.get_quota.return_value = 5000
        user_ops3.get_used_quota.return_value = 4800 # 200 free

        def mock_get_user_operations_logic(account_id):
            if account_id == acc1.account_id: return user_ops1
            if account_id == acc2.account_id: return user_ops2
            if account_id == acc3.account_id: return user_ops3
            raise PCloudException("Test setup error: unexpected account_id for get_user_operations")

        with patch.object(self.sdk, 'get_user_operations', side_effect=mock_get_user_operations_logic):
            self.sdk.account_manager.list_accounts.return_value = [acc1, acc2, acc3]
            selected_account = self.sdk.select_account_for_upload(file_size=1000)
            assert selected_account == acc2 # acc2 has most free space (5000)

    def test_select_account_handles_missing_quota_info(self):
        """Test that accounts with missing quota info (None) are skipped."""
        acc1 = Account(account_id="user1@example.com", email="user1@example.com", is_authenticated=True) # Missing quota
        acc2 = Account(account_id="user2@example.com", email="user2@example.com", is_authenticated=True) # Has quota

        user_ops1 = Mock(spec=User)
        user_ops1.get_quota.return_value = None # Simulate missing info
        user_ops1.get_used_quota.return_value = None

        user_ops2 = Mock(spec=User)
        user_ops2.get_quota.return_value = 10000
        user_ops2.get_used_quota.return_value = 5000 # 5000 free

        def mock_get_user_operations_logic(account_id):
            if account_id == acc1.account_id: return user_ops1
            if account_id == acc2.account_id: return user_ops2
            return Mock()

        with patch.object(self.sdk, 'get_user_operations', side_effect=mock_get_user_operations_logic):
            self.sdk.account_manager.list_accounts.return_value = [acc1, acc2]
            selected_account = self.sdk.select_account_for_upload(file_size=1000)
            assert selected_account == acc2 # acc1 should be skipped

    def test_select_account_handles_get_user_ops_exception(self):
        """Test that accounts where get_user_operations fails are skipped."""
        acc1 = Account(account_id="user1@example.com", is_authenticated=True) # Will fail
        acc2 = Account(account_id="user2@example.com", email="user2@example.com", is_authenticated=True) # OK

        user_ops2 = Mock(spec=User)
        user_ops2.get_quota.return_value = 10000
        user_ops2.get_used_quota.return_value = 5000

        def mock_get_user_operations_logic(account_id):
            if account_id == acc1.account_id: raise PCloudException("Simulated error getting user ops")
            if account_id == acc2.account_id: return user_ops2
            return Mock()

        with patch.object(self.sdk, 'get_user_operations', side_effect=mock_get_user_operations_logic):
            self.sdk.account_manager.list_accounts.return_value = [acc1, acc2]
            selected_account = self.sdk.select_account_for_upload(file_size=1000)
            assert selected_account == acc2 # acc1 should be skipped due to exception


@patch('os.path.getsize')
@patch('os.path.exists')
class TestUploadToSuitableAccount:
    """Tests for PCloudSDK.upload_to_suitable_account method."""

    def setup_method(self):
        self.sdk = PCloudSDK(token_manager=False)
        self.mock_selected_account = Account(account_id="uploader@example.com", email="uploader@example.com")
        self.mock_selected_account.is_authenticated = True # Ensure it's seen as authenticated

        self.mock_file_ops = Mock(spec=File)
        self.mock_upload_result = {"metadata": [{"fileid": 123, "name": "test.txt"}]}
        self.mock_file_ops.upload.return_value = self.mock_upload_result

        # Patch the SDK's internal methods
        self.select_account_patch = patch.object(self.sdk, 'select_account_for_upload', return_value=self.mock_selected_account)
        self.get_file_ops_patch = patch.object(self.sdk, 'get_file_operations', return_value=self.mock_file_ops)

        self.mock_select_account_for_upload = self.select_account_patch.start()
        self.mock_get_file_operations = self.get_file_ops_patch.start()

    def teardown_method(self):
        self.select_account_patch.stop()
        self.get_file_ops_patch.stop()

    def test_upload_successful(self, mock_os_path_exists, mock_os_path_getsize):
        """Test successful upload to a suitable account."""
        mock_os_path_exists.return_value = True
        mock_os_path_getsize.return_value = 5000

        file_path = "/fake/path/test.txt"
        folder_id = 0
        filename = "test_on_pcloud.txt"

        def cb(*args, **kwargs): pass

        result = self.sdk.upload_to_suitable_account(file_path, folder_id, filename, progress_callback=cb)

        mock_os_path_getsize.assert_called_once_with(file_path)
        self.mock_select_account_for_upload.assert_called_once_with(5000)
        self.mock_get_file_operations.assert_called_once_with(self.mock_selected_account.account_id)
        self.mock_file_ops.upload.assert_called_once_with(
            file_path=file_path, folder_id=folder_id, filename=filename, progress_callback=cb
        )

        assert result["metadata"] == self.mock_upload_result["metadata"]
        assert result["account_id_used"] == self.mock_selected_account.account_id
        assert result["account_email_used"] == self.mock_selected_account.email


    def test_upload_no_suitable_account_found(self, mock_os_path_exists, mock_os_path_getsize):
        """Test upload when no suitable account is found."""
        mock_os_path_exists.return_value = True
        mock_os_path_getsize.return_value = 10000

        self.mock_select_account_for_upload.side_effect = PCloudException("No space!")

        with pytest.raises(PCloudException, match="No space!"):
            self.sdk.upload_to_suitable_account("/fake/path/test.txt")

    def test_upload_file_not_found(self, mock_os_path_exists, mock_os_path_getsize):
        """Test upload when the local file does not exist."""
        mock_os_path_exists.return_value = False # File does not exist

        with pytest.raises(FileNotFoundError):
            self.sdk.upload_to_suitable_account("/fake/nonexistent.txt")
        mock_os_path_getsize.assert_not_called() # Should not be called if file doesn't exist


class TestFindFileInAccounts:
    """Tests for PCloudSDK.find_file_in_accounts method."""

    def setup_method(self):
        self.sdk = PCloudSDK(token_manager=False)
        self.sdk.account_manager = Mock(spec=AccountManager) # Mock AccountManager

        self.acc1 = Account(account_id="user1@example.com", email="user1@example.com", is_authenticated=True)
        self.acc2 = Account(account_id="user2@example.com", email="user2@example.com", is_authenticated=True)
        self.acc3_unauth = Account(account_id="user3@example.com", email="user3@example.com", is_authenticated=False)

        self.mock_folder_ops1 = Mock(spec=Folder)
        self.mock_folder_ops2 = Mock(spec=Folder)

    def test_find_file_no_accounts(self):
        """Test finding file when no accounts are managed."""
        self.sdk.account_manager.list_accounts.return_value = []
        results = self.sdk.find_file_in_accounts("testfile.txt")
        assert results == []

    def test_find_file_no_authenticated_accounts(self):
        """Test finding file when no accounts are authenticated."""
        self.sdk.account_manager.list_accounts.return_value = [self.acc3_unauth]
        results = self.sdk.find_file_in_accounts("testfile.txt")
        assert results == []

    def test_find_file_not_found_in_any_account(self):
        """Test when file is not found in any authenticated account."""
        self.mock_folder_ops1.get_content.return_value = [] # Account 1 has no such file
        self.mock_folder_ops2.get_content.return_value = [] # Account 2 has no such file

        def mock_get_folder_ops(account_id):
            if account_id == self.acc1.account_id: return self.mock_folder_ops1
            if account_id == self.acc2.account_id: return self.mock_folder_ops2
            return Mock()

        with patch.object(self.sdk, 'get_folder_operations', side_effect=mock_get_folder_ops):
            self.sdk.account_manager.list_accounts.return_value = [self.acc1, self.acc2]
            results = self.sdk.find_file_in_accounts("testfile.txt", folder_id=0)
            assert results == []
            self.mock_folder_ops1.get_content.assert_called_once_with(folder_id=0)
            self.mock_folder_ops2.get_content.assert_called_once_with(folder_id=0)

    def test_find_file_found_in_one_account(self):
        """Test when file is found in one authenticated account."""
        file_meta = {"name": "testfile.txt", "isfile": True, "fileid": 123, "size": 100}
        self.mock_folder_ops1.get_content.return_value = [file_meta]
        self.mock_folder_ops2.get_content.return_value = []

        def mock_get_folder_ops(account_id):
            if account_id == self.acc1.account_id: return self.mock_folder_ops1
            if account_id == self.acc2.account_id: return self.mock_folder_ops2
            return Mock()

        with patch.object(self.sdk, 'get_folder_operations', side_effect=mock_get_folder_ops):
            self.sdk.account_manager.list_accounts.return_value = [self.acc1, self.acc2]
            results = self.sdk.find_file_in_accounts("testfile.txt")

            assert len(results) == 1
            assert results[0]["name"] == "testfile.txt"
            assert results[0]["account_id_found_in"] == self.acc1.account_id
            assert results[0]["account_email_found_in"] == self.acc1.email

    def test_find_file_found_in_multiple_accounts(self):
        """Test when file is found in multiple authenticated accounts."""
        file_meta1 = {"name": "testfile.txt", "isfile": True, "fileid": 111, "size": 100}
        file_meta2 = {"name": "testfile.txt", "isfile": True, "fileid": 222, "size": 100} # Same name, different ID

        self.mock_folder_ops1.get_content.return_value = [file_meta1]
        self.mock_folder_ops2.get_content.return_value = [file_meta2]

        def mock_get_folder_ops(account_id):
            if account_id == self.acc1.account_id: return self.mock_folder_ops1
            if account_id == self.acc2.account_id: return self.mock_folder_ops2
            return Mock()

        with patch.object(self.sdk, 'get_folder_operations', side_effect=mock_get_folder_ops):
            self.sdk.account_manager.list_accounts.return_value = [self.acc1, self.acc2]
            results = self.sdk.find_file_in_accounts("testfile.txt")

            assert len(results) == 2
            assert results[0]["account_id_found_in"] == self.acc1.account_id
            assert results[1]["account_id_found_in"] == self.acc2.account_id


    def test_find_file_api_error_in_one_account(self):
        """Test search continues if one account throws PCloudException during list_folder."""
        file_meta2 = {"name": "testfile.txt", "isfile": True, "fileid": 222}

        self.mock_folder_ops1.get_content.side_effect = PCloudException("API error for acc1")
        self.mock_folder_ops2.get_content.return_value = [file_meta2]

        def mock_get_folder_ops(account_id):
            if account_id == self.acc1.account_id: return self.mock_folder_ops1
            if account_id == self.acc2.account_id: return self.mock_folder_ops2
            return Mock()

        with patch.object(self.sdk, 'get_folder_operations', side_effect=mock_get_folder_ops):
            self.sdk.account_manager.list_accounts.return_value = [self.acc1, self.acc2]
            results = self.sdk.find_file_in_accounts("testfile.txt")

            assert len(results) == 1 # Should find file in acc2
            assert results[0]["account_id_found_in"] == self.acc2.account_id
            assert results[0]["fileid"] == 222
            # Error for acc1 should have been caught and printed (not asserted here for simplicity)


class TestMultiAccountCredentialStorage:
    """Tests for saving and loading multiple accounts via PCloudSDK."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, ".test_pcloud_creds")
        # Ensure no pre-existing file from other tests
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        self.sdk = PCloudSDK(token_manager=True, token_file=self.token_file)

    def teardown_method(self):
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        os.rmdir(self.temp_dir)

    def test_save_and_load_multiple_accounts(self):
        """Test saving multiple accounts and loading them into a new SDK instance."""
        acc1 = Account(account_id="user1@example.com", email="user1@example.com", access_token="token1", is_authenticated=True, location_id=1)
        acc1.set_user_details("user1@example.com", 1, 1000, 100)
        acc2 = Account(account_id="user2@example.com", email="user2@example.com", access_token="token2", is_authenticated=True, location_id=2)
        acc2.set_user_details("user2@example.com", 2, 2000, 200)
        acc3_unauth = Account(account_id="user3@example.com", email="user3@example.com", is_authenticated=False)

        self.sdk.account_manager.add_account(acc1)
        self.sdk.account_manager.add_account(acc2)
        self.sdk.account_manager.add_account(acc3_unauth)

        self.sdk._save_all_accounts_credentials()
        assert os.path.exists(self.token_file)

        new_sdk = PCloudSDK(token_manager=True, token_file=self.token_file)
        # _load_saved_credentials is called in __init__ if token_manager=True

        loaded_accounts = new_sdk.account_manager.list_accounts()
        assert len(loaded_accounts) == 3

        loaded_acc1_info = new_sdk.account_manager.get_account("user1@example.com").get_info()
        original_acc1_info = acc1.get_info()
        # Compare relevant fields, ignore dynamic ones like 'saved_at' if not controlled
        for key in ["account_id", "email", "access_token", "is_authenticated", "user_id", "quota", "used_quota", "location_id"]:
            assert loaded_acc1_info[key] == original_acc1_info[key]

        loaded_acc2_info = new_sdk.account_manager.get_account("user2@example.com").get_info()
        original_acc2_info = acc2.get_info()
        for key in ["account_id", "email", "access_token", "is_authenticated", "user_id", "quota", "used_quota", "location_id"]:
            assert loaded_acc2_info[key] == original_acc2_info[key]

        loaded_acc3_info = new_sdk.account_manager.get_account("user3@example.com").get_info()
        assert loaded_acc3_info["is_authenticated"] is False
        assert loaded_acc3_info["access_token"] == ""


    def test_load_empty_credentials_file(self):
        """Test loading from an empty credentials file."""
        with open(self.token_file, "w") as f:
            f.write("") # Empty file

        new_sdk = PCloudSDK(token_manager=True, token_file=self.token_file)
        assert len(new_sdk.account_manager.list_accounts()) == 0

    def test_load_corrupted_json_credentials_file(self):
        """Test loading from a corrupted JSON credentials file."""
        with open(self.token_file, "w") as f:
            f.write("[{'account_id': 'bad@example.com', ...") # Corrupted JSON

        new_sdk = PCloudSDK(token_manager=True, token_file=self.token_file)
        # Expects error to be caught and logged, and no accounts loaded
        assert len(new_sdk.account_manager.list_accounts()) == 0

    def test_load_non_list_json_credentials_file(self):
        """Test loading from a JSON file that isn't a list."""
        with open(self.token_file, "w") as f:
            json.dump({"error": "this is not a list"}, f)

        new_sdk = PCloudSDK(token_manager=True, token_file=self.token_file)
        assert len(new_sdk.account_manager.list_accounts()) == 0

    def test_clear_all_credentials_works_with_multi_account_file(self):
        """Test clear_saved_credentials removes the file and clears manager."""
        acc1 = Account(account_id="user1@example.com", access_token="token1", is_authenticated=True)
        self.sdk.account_manager.add_account(acc1)
        self.sdk._save_all_accounts_credentials()
        assert os.path.exists(self.token_file)
        assert len(self.sdk.account_manager.list_accounts()) == 1

        self.sdk.clear_saved_credentials()

        assert not os.path.exists(self.token_file)
        assert len(self.sdk.account_manager.list_accounts()) == 0
        # Also verify that internal accounts dict in manager is empty
        assert self.sdk.account_manager.accounts == {}
