"""
Comprehensive folder operations tests for pCloud SDK
Tests folder creation, deletion, navigation, listing, and error scenarios
"""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from pcloud_sdk import PCloudSDK
from pcloud_sdk.app import App
from pcloud_sdk.folder_operations import Folder
from pcloud_sdk.exceptions import PCloudException
from .test_config import (
    requires_real_credentials, skip_if_no_integration_tests, get_test_credentials,
    safe_remove_file, safe_cleanup_temp_dir
)


class TestFolderCreation:
    """Tests for folder creation functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_create_folder_in_root(self):
        """Test creating a folder in root directory"""
        folder_name = "TestFolder"
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": folder_name,
                    "isfolder": True,
                    "parentfolderid": 0
                }
            },
            status=200
        )

        result = self.folder_ops.create(folder_name, parent=0)
        
        assert result == 12345
        
        # Verify the request was made with correct parameters
        request = responses.calls[0].request
        assert f"name={folder_name}" in request.url
        assert "path=%2F" in request.url  # "/" encoded

    @responses.activate
    def test_create_folder_in_specific_parent(self):
        """Test creating a folder in a specific parent folder"""
        folder_name = "SubFolder"
        parent_id = 9876
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 54321,
                    "name": folder_name,
                    "isfolder": True,
                    "parentfolderid": parent_id
                }
            },
            status=200
        )

        result = self.folder_ops.create(folder_name, parent=parent_id)
        
        assert result == 54321
        
        # Verify the request was made with correct parent folder ID
        request = responses.calls[0].request
        assert f"name={folder_name}" in request.url
        assert f"folderid={parent_id}" in request.url

    def test_create_folder_empty_name(self):
        """Test creating folder with empty name"""
        with pytest.raises(PCloudException, match="Please provide valid folder name"):
            self.folder_ops.create("")

    def test_create_folder_none_name(self):
        """Test creating folder with None name"""
        with pytest.raises(PCloudException, match="Please provide valid folder name"):
            self.folder_ops.create(None)

    @responses.activate
    def test_create_folder_name_conflict(self):
        """Test creating folder with existing name"""
        folder_name = "ExistingFolder"
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 2004,
                "error": "Folder already exists"
            },
            status=200
        )

        with pytest.raises(PCloudException):
            self.folder_ops.create(folder_name)

    @responses.activate
    def test_create_folder_unicode_name(self):
        """Test creating folder with unicode characters"""
        folder_name = "TestFolder_ÉÀÇ_测试_Тест"
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": folder_name,
                    "isfolder": True
                }
            },
            status=200
        )

        result = self.folder_ops.create(folder_name)
        assert result == 12345


class TestFolderListing:
    """Tests for folder listing and navigation functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_list_root_folder(self):
        """Test listing root folder contents"""
        mock_contents = [
            {
                "folderid": 12345,
                "name": "Documents",
                "isfolder": True,
                "created": "2023-01-01T00:00:00Z",
                "modified": "2023-01-01T00:00:00Z"
            },
            {
                "fileid": 54321,
                "name": "test.txt",
                "isfolder": False,
                "size": 1024,
                "created": "2023-01-01T00:00:00Z",
                "modified": "2023-01-01T00:00:00Z"
            }
        ]
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 0,
                    "name": "/",
                    "contents": mock_contents
                }
            },
            status=200
        )

        result = self.folder_ops.list_root()
        
        assert "contents" in result
        assert "metadata" in result
        assert len(result["contents"]) == 2
        assert result["contents"][0]["name"] == "Documents"
        assert result["contents"][1]["name"] == "test.txt"

    @responses.activate
    def test_get_content_by_folder_id(self):
        """Test getting folder content by folder ID"""
        folder_id = 12345
        mock_contents = [
            {
                "fileid": 98765,
                "name": "document.pdf",
                "isfolder": False,
                "size": 2048
            }
        ]
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": "Documents",
                    "contents": mock_contents
                }
            },
            status=200
        )

        result = self.folder_ops.get_content(folder_id=folder_id)
        
        assert len(result) == 1
        assert result[0]["name"] == "document.pdf"
        
        # Verify correct API call
        request = responses.calls[0].request
        assert f"folderid={folder_id}" in request.url

    @responses.activate
    def test_get_content_by_path(self):
        """Test getting folder content by path"""
        folder_path = "/Documents/Projects"
        mock_contents = [
            {
                "folderid": 11111,
                "name": "ProjectA",
                "isfolder": True
            },
            {
                "folderid": 22222,
                "name": "ProjectB",
                "isfolder": True
            }
        ]
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "name": "Projects",
                    "contents": mock_contents
                }
            },
            status=200
        )

        result = self.folder_ops.get_content(path=folder_path)
        
        assert len(result) == 2
        assert result[0]["name"] == "ProjectA"
        assert result[1]["name"] == "ProjectB"
        
        # Verify correct API call
        request = responses.calls[0].request
        assert f"path={folder_path.replace('/', '%2F')}" in request.url

    @responses.activate
    def test_get_metadata_root_folder(self):
        """Test getting metadata for root folder"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 0,
                    "name": "/",
                    "isfolder": True,
                    "contents": []
                }
            },
            status=200
        )

        result = self.folder_ops.get_metadata(folder_id=0)
        
        assert result["metadata"]["name"] == "/"
        assert result["metadata"]["isfolder"] is True
        
        # Verify it uses path="/" for root folder
        request = responses.calls[0].request
        assert "path=%2F" in request.url

    @responses.activate
    def test_get_metadata_specific_folder(self):
        """Test getting metadata for specific folder"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": "TestFolder",
                    "isfolder": True,
                    "parentfolderid": 0,
                    "created": "2023-01-01T00:00:00Z",
                    "modified": "2023-01-01T00:00:00Z",
                    "contents": []
                }
            },
            status=200
        )

        result = self.folder_ops.get_metadata(folder_id=folder_id)
        
        assert result["metadata"]["folderid"] == folder_id
        assert result["metadata"]["name"] == "TestFolder"
        assert result["metadata"]["parentfolderid"] == 0

    @responses.activate
    def test_list_folder_by_string_path(self):
        """Test listing folder using string path"""
        # Test complex path navigation logic
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 0,
                    "name": "/",
                    "contents": [
                        {
                            "folderid": 12345,
                            "name": "Documents",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": "Documents",
                    "contents": [
                        {
                            "folderid": 54321,
                            "name": "Projects",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )

        result = self.folder_ops.list_folder("Documents/Projects")
        
        assert result is not None
        assert result["folderid"] == 54321
        assert result["name"] == "Projects"

    @responses.activate
    def test_search_folder(self):
        """Test folder search functionality"""
        search_path = "/Documents/Important"
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "name": "Documents",
                    "contents": [
                        {
                            "folderid": 99999,
                            "name": "Important",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )

        result = self.folder_ops.search(search_path)
        
        assert "metadata" in result
        assert result["metadata"]["name"] == "Documents"
        
        # Verify nofiles parameter is set
        request = responses.calls[0].request
        assert "nofiles=1" in request.url


class TestFolderManipulation:
    """Tests for folder manipulation operations (rename, move, delete)"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_rename_folder(self):
        """Test folder rename operation"""
        folder_id = 12345
        new_name = "RenamedFolder"
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": new_name,
                    "isfolder": True
                }
            },
            status=200
        )

        result = self.folder_ops.rename(folder_id, new_name)
        
        assert result == folder_id
        
        # Verify request parameters
        request = responses.calls[0].request
        assert f"folderid={folder_id}" in request.url
        assert f"toname={new_name}" in request.url

    def test_rename_folder_empty_name(self):
        """Test folder rename with empty name"""
        folder_id = 12345
        
        with pytest.raises(PCloudException, match="Please provide folder name"):
            self.folder_ops.rename(folder_id, "")

    def test_rename_folder_none_name(self):
        """Test folder rename with None name"""
        folder_id = 12345
        
        with pytest.raises(PCloudException, match="Please provide folder name"):
            self.folder_ops.rename(folder_id, None)

    @responses.activate
    def test_move_folder(self):
        """Test folder move operation"""
        folder_id = 12345
        new_parent_id = 9876
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "parentfolderid": new_parent_id,
                    "isfolder": True
                }
            },
            status=200
        )

        result = self.folder_ops.move(folder_id, new_parent_id)
        
        assert result == folder_id
        
        # Verify request parameters
        request = responses.calls[0].request
        assert f"folderid={folder_id}" in request.url
        assert f"tofolderid={new_parent_id}" in request.url

    @responses.activate
    def test_move_folder_to_root(self):
        """Test moving folder to root directory"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "parentfolderid": 0,
                    "isfolder": True
                }
            },
            status=200
        )

        result = self.folder_ops.move(folder_id, 0)
        
        assert result == folder_id

    @responses.activate
    def test_delete_folder(self):
        """Test folder delete operation"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefolder",
            json={
                "result": 0,
                "metadata": {
                    "isdeleted": True
                }
            },
            status=200
        )

        result = self.folder_ops.delete(folder_id)
        
        assert result is True
        
        # Verify request parameters
        request = responses.calls[0].request
        assert f"folderid={folder_id}" in request.url

    @responses.activate
    def test_delete_folder_recursive(self):
        """Test recursive folder delete operation"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefolderrecursive",
            json={
                "result": 0,
                "metadata": {
                    "isdeleted": True,
                    "deletedfiles": 5,
                    "deletedfolders": 2
                }
            },
            status=200
        )

        result = self.folder_ops.delete_recursive(folder_id)
        
        assert result["metadata"]["isdeleted"] is True
        assert result["metadata"]["deletedfiles"] == 5
        assert result["metadata"]["deletedfolders"] == 2
        
        # Verify correct API endpoint
        request = responses.calls[0].request
        assert "deletefolderrecursive" in request.url
        assert f"folderid={folder_id}" in request.url


class TestFolderHierarchy:
    """Tests for complex folder hierarchy operations"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_nested_folder_creation(self):
        """Test creating nested folders"""
        # First create parent folder
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": "Parent",
                    "isfolder": True,
                    "parentfolderid": 0
                }
            },
            status=200
        )

        # Then create child folder
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 54321,
                    "name": "Child",
                    "isfolder": True,
                    "parentfolderid": 12345
                }
            },
            status=200
        )

        parent_id = self.folder_ops.create("Parent", parent=0)
        child_id = self.folder_ops.create("Child", parent=parent_id)
        
        assert parent_id == 12345
        assert child_id == 54321

    @responses.activate
    def test_deep_folder_navigation(self):
        """Test navigating through deep folder structure"""
        # Mock root folder listing
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 0,
                    "contents": [
                        {
                            "folderid": 100,
                            "name": "Level1",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )

        # Mock level 1 folder listing
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 100,
                    "contents": [
                        {
                            "folderid": 200,
                            "name": "Level2",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )

        # Mock level 2 folder listing  
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 200,
                    "contents": [
                        {
                            "folderid": 300,
                            "name": "Level3",
                            "isfolder": True
                        }
                    ]
                }
            },
            status=200
        )

        result = self.folder_ops.list_folder("Level1/Level2/Level3")
        
        assert result is not None
        assert result["folderid"] == 300
        assert result["name"] == "Level3"

    @responses.activate
    def test_folder_tree_with_mixed_content(self):
        """Test folder containing both files and subfolders"""
        folder_id = 12345
        mixed_contents = [
            {
                "folderid": 111,
                "name": "Subfolder1",
                "isfolder": True,
                "created": "2023-01-01T00:00:00Z"
            },
            {
                "fileid": 222,
                "name": "file1.txt",
                "isfolder": False,
                "size": 1024,
                "created": "2023-01-01T00:00:00Z"
            },
            {
                "folderid": 333,
                "name": "Subfolder2", 
                "isfolder": True,
                "created": "2023-01-01T00:00:00Z"
            },
            {
                "fileid": 444,
                "name": "file2.pdf",
                "isfolder": False,
                "size": 2048,
                "created": "2023-01-01T00:00:00Z"
            }
        ]
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": "MixedFolder",
                    "contents": mixed_contents
                }
            },
            status=200
        )

        result = self.folder_ops.get_content(folder_id=folder_id)
        
        assert len(result) == 4
        
        # Verify we have both folders and files
        folders = [item for item in result if item.get("isfolder")]
        files = [item for item in result if not item.get("isfolder")]
        
        assert len(folders) == 2
        assert len(files) == 2
        
        assert folders[0]["name"] == "Subfolder1"
        assert folders[1]["name"] == "Subfolder2"
        assert files[0]["name"] == "file1.txt"
        assert files[1]["name"] == "file2.pdf"


class TestFolderErrorScenarios:
    """Tests for various error scenarios in folder operations"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_folder_not_found(self):
        """Test operations on non-existent folder"""
        folder_id = 99999
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 2005,
                "error": "Directory does not exist"
            },
            status=200
        )

        with pytest.raises(PCloudException):
            self.folder_ops.get_metadata(folder_id=folder_id)

    @responses.activate
    def test_access_denied(self):
        """Test folder operations with insufficient permissions"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefolder",
            json={
                "result": 2003,
                "error": "Access denied"
            },
            status=200
        )

        with pytest.raises(PCloudException):
            self.folder_ops.delete(folder_id)

    @responses.activate
    def test_folder_not_empty(self):
        """Test deleting non-empty folder (non-recursive)"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefolder",
            json={
                "result": 2007,
                "error": "Directory not empty"
            },
            status=200
        )

        with pytest.raises(PCloudException):
            self.folder_ops.delete(folder_id)

    @responses.activate
    def test_invalid_folder_name_characters(self):
        """Test creating folder with invalid characters"""
        invalid_names = ["folder/with/slash", "folder\\with\\backslash", "folder:with:colon"]
        
        for invalid_name in invalid_names:
            responses.add(
                responses.GET,
                "https://eapi.pcloud.com/createfolder",
                json={
                    "result": 2008,
                    "error": "Invalid name"
                },
                status=200
            )

        for invalid_name in invalid_names:
            with pytest.raises(PCloudException):
                self.folder_ops.create(invalid_name)

    @responses.activate
    def test_network_timeout_folder_operations(self):
        """Test folder operations with network timeout"""
        folder_id = 12345
        
        def timeout_callback(request):
            raise Timeout("Request timed out")
        
        responses.add_callback(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            callback=timeout_callback
        )
        
        with pytest.raises(Exception):  # Should propagate timeout error
            self.folder_ops.get_metadata(folder_id=folder_id)

    @responses.activate
    def test_connection_error_folder_operations(self):
        """Test folder operations with connection error"""
        folder_id = 12345
        
        def connection_error_callback(request):
            raise ConnectionError("Failed to connect")
        
        responses.add_callback(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            callback=connection_error_callback
        )
        
        with pytest.raises(Exception):  # Should propagate connection error
            self.folder_ops.get_metadata(folder_id=folder_id)

    def test_invalid_folder_ids(self):
        """Test operations with invalid folder IDs"""
        invalid_ids = [-1, "invalid", None]
        
        for invalid_id in invalid_ids:
            with pytest.raises((TypeError, ValueError, PCloudException)):
                self.folder_ops.get_content(folder_id=invalid_id)

    @responses.activate
    def test_malformed_api_response(self):
        """Test handling of malformed API responses"""
        folder_id = 12345
        
        # Response missing required fields
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0
                # Missing metadata field
            },
            status=200
        )

        result = self.folder_ops.get_content(folder_id=folder_id)
        
        # Should handle gracefully and return empty list
        assert result == []


class TestFolderOperationsIntegration:
    """Integration tests for folder operations with PCloudSDK"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_sdk_folder_operations_workflow(self):
        """Test complete folder operations workflow through SDK"""
        # Mock login
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

        # Initialize SDK
        sdk = PCloudSDK(token_file=self.token_file)
        sdk.login("test@example.com", "password", location_id=2)
        
        # Test that folder operations are accessible through SDK
        assert sdk.folder is not None
        assert hasattr(sdk.folder, 'create')
        assert hasattr(sdk.folder, 'delete')
        assert hasattr(sdk.folder, 'rename')
        assert hasattr(sdk.folder, 'move')
        assert hasattr(sdk.folder, 'list_folder')
        assert hasattr(sdk.folder, 'get_content')

    @responses.activate
    def test_complete_folder_lifecycle(self):
        """Test complete folder lifecycle: create, list, rename, move, delete"""
        sdk = PCloudSDK(token_file=self.token_file, token_manager=False)
        sdk.set_access_token("test_token", "direct")
        
        # Mock folder creation
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": "TestFolder",
                    "isfolder": True,
                    "parentfolderid": 0
                }
            },
            status=200
        )

        # Mock folder listing after creation
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": "TestFolder",
                    "contents": []
                }
            },
            status=200
        )

        # Mock folder rename
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": 12345,
                    "name": "RenamedFolder",
                    "isfolder": True
                }
            },
            status=200
        )

        # Mock folder delete
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefolder",
            json={
                "result": 0,
                "metadata": {
                    "isdeleted": True
                }
            },
            status=200
        )

        # Execute complete lifecycle
        folder_id = sdk.folder.create("TestFolder", parent=0)
        assert folder_id == 12345
        
        content = sdk.folder.get_content(folder_id=folder_id)
        assert content == []
        
        renamed_id = sdk.folder.rename(folder_id, "RenamedFolder")
        assert renamed_id == folder_id
        
        deleted = sdk.folder.delete(folder_id)
        assert deleted is True


class TestFolderOperationsEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.folder_ops = Folder(self.app)

    @responses.activate
    def test_very_long_folder_name(self):
        """Test creating folder with very long name"""
        long_name = "A" * 1000  # 1000 character folder name
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/createfolder",
            json={
                "result": 2008,
                "error": "Folder name too long"
            },
            status=200
        )

        with pytest.raises(PCloudException):
            self.folder_ops.create(long_name)

    @responses.activate
    def test_folder_with_special_characters(self):
        """Test folder operations with special characters"""
        special_names = [
            "folder with spaces",
            "folder.with.dots",
            "folder-with-dashes",
            "folder_with_underscores",
            "folder (with parentheses)",
            "folder [with brackets]",
            "folder {with braces}",
            "🚀 emoji folder 📁"
        ]
        
        for i, name in enumerate(special_names):
            responses.add(
                responses.GET,
                "https://eapi.pcloud.com/createfolder",
                json={
                    "result": 0,
                    "metadata": {
                        "folderid": 10000 + i,
                        "name": name,
                        "isfolder": True
                    }
                },
                status=200
            )

        for i, name in enumerate(special_names):
            result = self.folder_ops.create(name)
            assert result == 10000 + i

    @responses.activate
    def test_empty_folder_listing(self):
        """Test listing completely empty folder"""
        folder_id = 12345
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": "EmptyFolder",
                    "contents": []
                }
            },
            status=200
        )

        result = self.folder_ops.get_content(folder_id=folder_id)
        
        assert result == []
        assert isinstance(result, list)

    @responses.activate
    def test_folder_with_thousands_of_items(self):
        """Test folder with large number of items"""
        folder_id = 12345
        
        # Generate 1000 mock items
        large_contents = []
        for i in range(1000):
            large_contents.append({
                "fileid": 20000 + i,
                "name": f"file_{i:04d}.txt",
                "isfolder": False,
                "size": 1024
            })
        
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/listfolder",
            json={
                "result": 0,
                "metadata": {
                    "folderid": folder_id,
                    "name": "LargeFolder",
                    "contents": large_contents
                }
            },
            status=200
        )

        result = self.folder_ops.get_content(folder_id=folder_id)
        
        assert len(result) == 1000
        assert result[0]["name"] == "file_0000.txt"
        assert result[999]["name"] == "file_0999.txt"

    def test_folder_operations_without_authentication(self):
        """Test folder operations without setting authentication token"""
        unauthenticated_app = App()
        folder_ops = Folder(unauthenticated_app)
        
        # This should fail during the actual API call
        # The behavior depends on the Request class implementation
        # For now, just verify the folder_ops instance is created
        assert folder_ops is not None

    @responses.activate
    def test_concurrent_folder_operations(self):
        """Test that multiple folder operations can be performed in sequence"""
        # This tests that the Folder class maintains proper state
        # between multiple operations
        
        # Mock multiple folder creations
        for i in range(5):
            responses.add(
                responses.GET,
                "https://eapi.pcloud.com/createfolder",
                json={
                    "result": 0,
                    "metadata": {
                        "folderid": 30000 + i,
                        "name": f"Folder_{i}",
                        "isfolder": True
                    }
                },
                status=200
            )

        results = []
        for i in range(5):
            result = self.folder_ops.create(f"Folder_{i}")
            results.append(result)
        
        assert results == [30000, 30001, 30002, 30003, 30004]


@pytest.mark.integration
class TestFolderOperationsIntegrationReal:
    """Integration tests with real pCloud API (require credentials)"""

    @requires_real_credentials
    @skip_if_no_integration_tests
    def test_real_folder_operations_lifecycle(self):
        """Test real folder operations lifecycle"""
        creds = get_test_credentials()
        
        sdk = PCloudSDK()
        sdk.login(creds["email"], creds["password"], location_id=creds["location_id"])
        
        try:
            # Create test folder
            folder_id = sdk.folder.create("SDK_Test_Folder", parent=0)
            assert isinstance(folder_id, int)
            
            # List root to verify creation
            root_content = sdk.folder.list_root()
            folder_names = [item["name"] for item in root_content["contents"] if item.get("isfolder")]
            assert "SDK_Test_Folder" in folder_names
            
            # Rename folder
            renamed_id = sdk.folder.rename(folder_id, "SDK_Test_Folder_Renamed")
            assert renamed_id == folder_id
            
            # Create subfolder
            subfolder_id = sdk.folder.create("SubFolder", parent=folder_id)
            assert isinstance(subfolder_id, int)
            
            # List folder content
            folder_content = sdk.folder.get_content(folder_id=folder_id)
            assert len(folder_content) == 1
            assert folder_content[0]["name"] == "SubFolder"
            
            # Delete subfolder
            deleted_sub = sdk.folder.delete(subfolder_id)
            assert deleted_sub is True
            
            # Delete main folder
            deleted_main = sdk.folder.delete(folder_id)
            assert deleted_main is True
            
        except Exception as e:
            # Cleanup on error
            try:
                sdk.folder.delete_recursive(folder_id)
            except:
                pass
            raise e

    @requires_real_credentials
    @skip_if_no_integration_tests
    def test_real_deep_folder_structure(self):
        """Test creating and navigating deep folder structure"""
        creds = get_test_credentials()
        
        sdk = PCloudSDK()
        sdk.login(creds["email"], creds["password"], location_id=creds["location_id"])
        
        folder_ids = []
        try:
            # Create nested folder structure: Level1/Level2/Level3
            level1_id = sdk.folder.create("Level1", parent=0)
            folder_ids.append(level1_id)
            
            level2_id = sdk.folder.create("Level2", parent=level1_id)
            folder_ids.append(level2_id)
            
            level3_id = sdk.folder.create("Level3", parent=level2_id)
            folder_ids.append(level3_id)
            
            # Verify navigation
            result = sdk.folder.list_folder("Level1/Level2/Level3")
            assert result is not None
            assert result["folderid"] == level3_id
            
        finally:
            # Cleanup - delete in reverse order
            for folder_id in reversed(folder_ids):
                try:
                    sdk.folder.delete(folder_id)
                except:
                    pass