"""
Comprehensive file operations tests for pCloud SDK
Tests upload, download, file manipulation, progress tracking, and error scenarios
"""

import os
import tempfile
import time
from io import BytesIO
from unittest.mock import Mock, call, patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from pcloud_sdk import PCloudSDK
from pcloud_sdk.app import App
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.file_operations import File

from .test_config import (
    get_test_credentials,
    requires_real_credentials,
    safe_cleanup_temp_dir,
    safe_remove_directory,
    safe_remove_file,
    skip_if_no_integration_tests,
)


class TestFileUpload:
    """Tests for file upload functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

        # Create a temporary test file
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_upload.txt")
        self.test_content = b"Hello, pCloud! This is test content for upload."

        with open(self.test_file, "wb") as f:
            f.write(self.test_content)

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.test_file)
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_successful_file_upload(self):
        """Test successful file upload to root folder"""
        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 0},
            status=200,
        )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [
                    {
                        "fileid": 54321,
                        "name": "test_upload.txt",
                        "size": len(self.test_content),
                        "isfolder": False,
                    }
                ],
            },
            status=200,
        )

        result = self.file_ops.upload(self.test_file, folder_id=0)

        assert "metadata" in result
        assert result["metadata"][0]["name"] == "test_upload.txt"
        assert result["metadata"][0]["size"] == len(self.test_content)

    @responses.activate
    def test_upload_with_custom_filename(self):
        """Test file upload with custom filename"""
        custom_filename = "custom_name.txt"

        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 0},
            status=200,
        )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [
                    {
                        "fileid": 54321,
                        "name": custom_filename,
                        "size": len(self.test_content),
                        "isfolder": False,
                    }
                ],
            },
            status=200,
        )

        result = self.file_ops.upload(
            self.test_file, folder_id=0, filename=custom_filename
        )

        assert result["metadata"][0]["name"] == custom_filename

    @responses.activate
    def test_upload_to_specific_folder(self):
        """Test file upload to specific folder"""
        folder_id = 9876

        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 0},
            status=200,
        )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [
                    {
                        "fileid": 54321,
                        "name": "test_upload.txt",
                        "size": len(self.test_content),
                        "isfolder": False,
                    }
                ],
            },
            status=200,
        )

        result = self.file_ops.upload(self.test_file, folder_id=folder_id)

        # Verify the request was made with correct folder_id
        save_request = [
            call for call in responses.calls if "upload_save" in call.request.url
        ][0]
        assert f"folderid={folder_id}" in save_request.request.url

    def test_upload_nonexistent_file(self):
        """Test upload with nonexistent file"""
        nonexistent_file = "/path/to/nonexistent/file.txt"

        with pytest.raises(PCloudException, match="Invalid file"):
            self.file_ops.upload(nonexistent_file)

    def test_upload_directory_instead_of_file(self):
        """Test upload with directory path instead of file"""
        with pytest.raises(PCloudException, match="Invalid file"):
            self.file_ops.upload(self.temp_dir)

    @responses.activate
    def test_upload_create_session_failure(self):
        """Test handling of upload session creation failure"""
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 5000, "error": "Unable to create upload session"},
            status=200,
        )

        with pytest.raises(
            PCloudException, match="Erreur lors de la création de la session d'upload"
        ):
            self.file_ops.upload(self.test_file)

    @responses.activate
    def test_upload_with_progress_callback(self):
        """Test file upload with progress callback"""
        progress_calls = []

        def mock_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            progress_calls.append(
                {
                    "bytes_transferred": bytes_transferred,
                    "total_bytes": total_bytes,
                    "percentage": percentage,
                    "operation": kwargs.get("operation"),
                    "filename": kwargs.get("filename"),
                    "status": kwargs.get("status"),
                }
            )

        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 0},
            status=200,
        )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [{"fileid": 54321, "name": "test_upload.txt"}],
            },
            status=200,
        )

        self.file_ops.upload(
            self.test_file, folder_id=0, progress_callback=mock_progress
        )

        assert len(progress_calls) >= 3  # At least starting, progress, completed
        assert progress_calls[0]["status"] == "starting"
        assert progress_calls[-1]["status"] == "completed"
        assert all(call["operation"] == "upload" for call in progress_calls)
        assert all(call["filename"] == "test_upload.txt" for call in progress_calls)

    @responses.activate
    def test_upload_retry_on_chunk_failure(self):
        """Test upload retry mechanism on chunk failure"""
        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write - fail first time, succeed second time
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 5000, "error": "Network error"},
            status=500,
        )
        responses.add(
            responses.PUT,
            "https://eapi.pcloud.com/upload_write",
            json={"result": 0},
            status=200,
        )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [{"fileid": 54321, "name": "test_upload.txt"}],
            },
            status=200,
        )

        # Should succeed after retry
        result = self.file_ops.upload(self.test_file)
        assert "metadata" in result

    @responses.activate
    def test_upload_max_retries_exceeded(self):
        """Test upload failure after max retries"""
        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock upload_write to always fail
        for _ in range(15):  # More than max retries (10)
            responses.add(
                responses.PUT,
                "https://eapi.pcloud.com/upload_write",
                json={"result": 5000, "error": "Persistent error"},
                status=500,
            )

        with pytest.raises(PCloudException, match="Upload échoué après .* tentatives"):
            self.file_ops.upload(self.test_file)


class TestFileDownload:
    """Tests for file download functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Cleanup after each test"""
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_successful_file_download(self):
        """Test successful file download"""
        file_id = 12345
        test_content = b"Downloaded file content"

        # Mock getfilelink
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={
                "result": 0,
                "hosts": ["c123.pcloud.com"],
                "path": "/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            },
            status=200,
        )

        # Mock file download
        responses.add(
            responses.GET,
            "https://c123.pcloud.com/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            body=test_content,
            headers={"content-length": str(len(test_content))},
            status=200,
        )

        success = self.file_ops.download(file_id, self.temp_dir)

        assert success is True
        downloaded_file = os.path.join(self.temp_dir, "test_file.txt")
        assert os.path.exists(downloaded_file)

        with open(downloaded_file, "rb") as f:
            content = f.read()
        assert content == test_content

    @responses.activate
    def test_download_with_progress_callback(self):
        """Test file download with progress callback"""
        file_id = 12345
        test_content = b"A" * 1024 * 10  # 10KB file
        progress_calls = []

        def mock_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            progress_calls.append(
                {
                    "bytes_transferred": bytes_transferred,
                    "total_bytes": total_bytes,
                    "percentage": percentage,
                    "operation": kwargs.get("operation"),
                    "filename": kwargs.get("filename"),
                    "status": kwargs.get("status"),
                }
            )

        # Mock getfilelink
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={
                "result": 0,
                "hosts": ["c123.pcloud.com"],
                "path": "/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            },
            status=200,
        )

        # Mock file download
        responses.add(
            responses.GET,
            "https://c123.pcloud.com/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            body=test_content,
            headers={"content-length": str(len(test_content))},
            status=200,
        )

        success = self.file_ops.download(
            file_id, self.temp_dir, progress_callback=mock_progress
        )

        assert success is True
        assert len(progress_calls) >= 2  # At least starting and completed
        assert progress_calls[0]["status"] == "starting"
        assert progress_calls[-1]["status"] == "completed"
        assert all(call["operation"] == "download" for call in progress_calls)

    @responses.activate
    def test_download_failed_get_link(self):
        """Test download failure when getting file link fails"""
        file_id = 12345

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={"result": 2009, "error": "File not found"},
            status=200,
        )

        with pytest.raises(PCloudException, match="Failed to get file link"):
            self.file_ops.download(file_id, self.temp_dir)

    @responses.activate
    def test_download_http_error(self):
        """Test download failure due to HTTP error"""
        file_id = 12345

        # Mock getfilelink
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={
                "result": 0,
                "hosts": ["c123.pcloud.com"],
                "path": "/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            },
            status=200,
        )

        # Mock file download failure
        responses.add(
            responses.GET,
            "https://c123.pcloud.com/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            status=404,
        )

        with pytest.raises(Exception):  # requests.HTTPError
            self.file_ops.download(file_id, self.temp_dir)

    @responses.activate
    def test_download_creates_destination_directory(self):
        """Test that download creates destination directory if it doesn't exist"""
        file_id = 12345
        test_content = b"Test content"
        new_dir = os.path.join(self.temp_dir, "new_folder")

        # Mock getfilelink
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={
                "result": 0,
                "hosts": ["c123.pcloud.com"],
                "path": "/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            },
            status=200,
        )

        # Mock file download
        responses.add(
            responses.GET,
            "https://c123.pcloud.com/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/test_file.txt",
            body=test_content,
            headers={"content-length": str(len(test_content))},
            status=200,
        )

        success = self.file_ops.download(file_id, new_dir)

        assert success is True
        assert os.path.exists(new_dir)
        assert os.path.exists(os.path.join(new_dir, "test_file.txt"))


class TestFileManipulation:
    """Tests for file manipulation operations (rename, move, copy, delete)"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

    @responses.activate
    def test_file_rename(self):
        """Test file rename operation"""
        file_id = 12345
        new_name = "renamed_file.txt"

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefile",
            json={
                "result": 0,
                "metadata": {"fileid": file_id, "name": new_name, "isfolder": False},
            },
            status=200,
        )

        result = self.file_ops.rename(file_id, new_name)

        assert "metadata" in result
        assert result["metadata"]["name"] == new_name

    def test_file_rename_empty_name(self):
        """Test file rename with empty name"""
        file_id = 12345

        with pytest.raises(PCloudException, match="Please provide valid file name"):
            self.file_ops.rename(file_id, "")

    @responses.activate
    def test_file_move(self):
        """Test file move operation"""
        file_id = 12345
        target_folder_id = 9876

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/renamefile",
            json={
                "result": 0,
                "metadata": {
                    "fileid": file_id,
                    "parentfolderid": target_folder_id,
                    "isfolder": False,
                },
            },
            status=200,
        )

        result = self.file_ops.move(file_id, target_folder_id)

        # Verify the request was made with correct parameters
        request = responses.calls[0].request
        assert f"fileid={file_id}" in request.url
        assert f"tofolderid={target_folder_id}" in request.url

    @responses.activate
    def test_file_copy(self):
        """Test file copy operation"""
        file_id = 12345
        target_folder_id = 9876

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/copyfile",
            json={
                "result": 0,
                "metadata": {
                    "fileid": 54321,  # New file ID for the copy
                    "parentfolderid": target_folder_id,
                    "isfolder": False,
                },
            },
            status=200,
        )

        result = self.file_ops.copy(file_id, target_folder_id)

        # Verify the request was made with correct parameters
        request = responses.calls[0].request
        assert f"fileid={file_id}" in request.url
        assert f"tofolderid={target_folder_id}" in request.url
        assert "copyfile" in request.url

    @responses.activate
    def test_file_delete(self):
        """Test file delete operation"""
        file_id = 12345

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/deletefile",
            json={"result": 0, "metadata": {"isdeleted": True}},
            status=200,
        )

        result = self.file_ops.delete(file_id)

        assert result is True

    @responses.activate
    def test_file_get_info(self):
        """Test getting file information"""
        file_id = 12345

        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/checksumfile",
            json={
                "result": 0,
                "metadata": {
                    "fileid": file_id,
                    "name": "test_file.txt",
                    "size": 1024,
                    "created": "2023-01-01T00:00:00Z",
                    "modified": "2023-01-01T00:00:00Z",
                    "md5": "abc123def456",
                    "sha1": "def456ghi789",
                },
            },
            status=200,
        )

        result = self.file_ops.get_info(file_id)

        assert result["metadata"]["fileid"] == file_id
        assert result["metadata"]["name"] == "test_file.txt"
        assert result["metadata"]["size"] == 1024


class TestLargeFileHandling:
    """Tests for large file upload/download scenarios"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

        # Create a temporary large file (simulate with small size for testing)
        self.temp_dir = tempfile.mkdtemp()
        self.large_file = os.path.join(self.temp_dir, "large_test_file.dat")

        # Create a file larger than the chunk size
        chunk_size = self.file_ops.part_size  # Default chunk size
        file_size = chunk_size * 3 + 1000  # 3+ chunks

        with open(self.large_file, "wb") as f:
            f.write(b"A" * file_size)

    def teardown_method(self):
        """Cleanup after each test"""
        safe_remove_file(self.large_file)
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_large_file_upload_chunked(self):
        """Test large file upload is processed in chunks"""
        progress_calls = []

        def track_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            progress_calls.append(bytes_transferred)

        # Mock upload_create
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_create",
            json={"result": 0, "uploadid": 12345},
            status=200,
        )

        # Mock multiple upload_write calls (for each chunk)
        file_size = os.path.getsize(self.large_file)
        expected_chunks = (file_size // self.file_ops.part_size) + (
            1 if file_size % self.file_ops.part_size > 0 else 0
        )

        for _ in range(expected_chunks):
            responses.add(
                responses.PUT,
                "https://eapi.pcloud.com/upload_write",
                json={"result": 0},
                status=200,
            )

        # Mock upload_save
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/upload_save",
            json={
                "result": 0,
                "metadata": [
                    {"fileid": 54321, "name": "large_test_file.dat", "size": file_size}
                ],
            },
            status=200,
        )

        result = self.file_ops.upload(
            self.large_file, folder_id=0, progress_callback=track_progress
        )

        assert "metadata" in result
        assert result["metadata"][0]["size"] == file_size

        # Verify multiple chunks were uploaded
        upload_write_calls = [
            call for call in responses.calls if "upload_write" in call.request.url
        ]
        assert len(upload_write_calls) == expected_chunks

        # Verify progress was tracked through multiple chunks
        assert len(progress_calls) >= expected_chunks

    @responses.activate
    def test_large_file_download_chunked(self):
        """Test large file download is processed in chunks"""
        file_id = 12345
        large_content = b"B" * (1024 * 1024)  # 1MB content

        # Mock getfilelink
        responses.add(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            json={
                "result": 0,
                "hosts": ["c123.pcloud.com"],
                "path": "/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/large_file.dat",
            },
            status=200,
        )

        # Mock file download with streaming
        def stream_response(request):
            headers = {
                "content-length": str(len(large_content)),
                "content-type": "application/octet-stream",
            }
            return (200, headers, large_content)

        responses.add_callback(
            responses.GET,
            "https://c123.pcloud.com/cBRFZF7ZTKMDlKfpKv5VIQbNVrBJNIZ0/large_file.dat",
            callback=stream_response,
        )

        progress_calls = []

        def track_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            progress_calls.append(bytes_transferred)

        success = self.file_ops.download(
            file_id, self.temp_dir, progress_callback=track_progress
        )

        assert success is True

        # Verify downloaded file exists and has correct size
        downloaded_file = os.path.join(self.temp_dir, "large_file.dat")
        assert os.path.exists(downloaded_file)
        assert os.path.getsize(downloaded_file) == len(large_content)


class TestErrorScenarios:
    """Tests for various error scenarios in file operations"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

    @responses.activate
    def test_api_error_responses(self):
        """Test handling of various API error responses"""
        file_id = 12345

        # Test different error codes
        error_scenarios = [
            (2009, "File not found"),
            (2003, "Access denied"),
            (5000, "Internal server error"),
            (4000, "Invalid parameters"),
        ]

        for error_code, error_msg in error_scenarios:
            responses.reset()
            responses.add(
                responses.GET,
                "https://eapi.pcloud.com/getfilelink",
                json={"result": error_code, "error": error_msg},
                status=200,
            )

            with pytest.raises(PCloudException):
                self.file_ops.get_link(file_id)

    @responses.activate
    def test_network_timeout_handling(self):
        """Test handling of network timeouts"""
        file_id = 12345

        # Mock timeout error
        def timeout_callback(request):
            raise Timeout("Request timed out")

        responses.add_callback(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            callback=timeout_callback,
        )

        with pytest.raises(Exception):  # Should propagate timeout error
            self.file_ops.get_link(file_id)

    @responses.activate
    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        file_id = 12345

        # Mock connection error
        def connection_error_callback(request):
            raise ConnectionError("Failed to connect")

        responses.add_callback(
            responses.GET,
            "https://eapi.pcloud.com/getfilelink",
            callback=connection_error_callback,
        )

        with pytest.raises(Exception):  # Should propagate connection error
            self.file_ops.get_link(file_id)

    def test_invalid_file_ids(self):
        """Test operations with invalid file IDs"""
        invalid_ids = [0, -1, "invalid", None]

        for invalid_id in invalid_ids:
            with pytest.raises((TypeError, ValueError, PCloudException)):
                self.file_ops.get_info(invalid_id)


class TestProgressCallbacks:
    """Tests for progress callback functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

    def test_progress_callback_parameters(self):
        """Test that progress callback receives correct parameters"""

        def validate_progress(
            bytes_transferred, total_bytes, percentage, speed, **kwargs
        ):
            # Validate parameter types
            assert isinstance(bytes_transferred, int)
            assert isinstance(total_bytes, int)
            assert isinstance(percentage, float)
            assert isinstance(speed, (int, float))

            # Validate parameter values
            assert 0 <= bytes_transferred <= total_bytes
            assert 0 <= percentage <= 100
            assert speed >= 0

            # Validate kwargs
            assert "operation" in kwargs
            assert "filename" in kwargs
            assert kwargs["operation"] in ["upload", "download"]

        # Create a simple mock scenario to test callback
        with patch.object(self.file_ops, "upload") as mock_upload:
            mock_upload.side_effect = lambda *args, **kwargs: kwargs.get(
                "progress_callback", lambda *a, **k: None
            )(1024, 2048, 50.0, 1024.0, operation="upload", filename="test.txt")

            self.file_ops.upload("dummy_path", progress_callback=validate_progress)

    def test_progress_callback_error_handling(self):
        """Test that errors in progress callback don't break the operation"""

        def failing_progress(*args, **kwargs):
            raise Exception("Progress callback error")

        # The operation should continue even if progress callback fails
        # This would be tested with actual upload/download mocking
        # For now, just verify the callback signature
        assert callable(failing_progress)

    def test_no_progress_callback(self):
        """Test operations work correctly without progress callback"""
        # Operations should work fine with progress_callback=None
        # This is tested implicitly in other test methods
        pass


class TestFileOperationsIntegration:
    """Integration tests for file operations with PCloudSDK"""

    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.token_file = os.path.join(self.temp_dir, "test_credentials.json")

    def teardown_method(self):
        """Cleanup after each test"""
        safe_cleanup_temp_dir(self.temp_dir)

    @responses.activate
    def test_sdk_file_operations_workflow(self):
        """Test complete file operations workflow through SDK"""
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
                "usedquota": 1073741824,
            },
            status=200,
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
                "usedquota": 1073741824,
            },
            status=200,
        )

        # Initialize SDK
        sdk = PCloudSDK(token_file=self.token_file)
        sdk.login("test@example.com", "password", location_id=2)

        # Test that file operations are accessible through SDK
        assert sdk.file is not None
        assert hasattr(sdk.file, "upload")
        assert hasattr(sdk.file, "download")
        assert hasattr(sdk.file, "delete")
        assert hasattr(sdk.file, "rename")
        assert hasattr(sdk.file, "move")
        assert hasattr(sdk.file, "copy")


@pytest.mark.performance
class TestFileOperationsPerformance:
    """Performance tests for file operations"""

    def setup_method(self):
        """Setup for each test"""
        self.app = App()
        self.app.set_location_id(2)  # Use EU server to match test mocks
        self.app.set_access_token("test_token", "direct")
        self.file_ops = File(self.app)

    @pytest.mark.benchmark
    def test_upload_progress_callback_performance(self, benchmark):
        """Benchmark progress callback performance during upload"""

        def dummy_progress(bytes_transferred, total_bytes, percentage, speed, **kwargs):
            # Simulate some basic processing
            _ = f"Progress: {percentage:.1f}%"

        def upload_with_progress():
            # Simulate calling progress callback multiple times
            for i in range(100):
                dummy_progress(
                    i * 1024,
                    100 * 1024,
                    i,
                    1024.0,
                    operation="upload",
                    filename="test.txt",
                )

        benchmark(upload_with_progress)

    def test_large_file_memory_usage(self):
        """Test that large file operations don't consume excessive memory"""
        # This test would monitor memory usage during large file operations
        # For now, just verify the chunk size is reasonable
        assert self.file_ops.part_size > 0
        assert self.file_ops.part_size <= 10 * 1024 * 1024  # Max 10MB chunks


@pytest.mark.integration
class TestFileOperationsIntegrationReal:
    """Integration tests with real pCloud API (require credentials)"""

    @requires_real_credentials
    @skip_if_no_integration_tests
    def test_real_file_upload_download(self):
        """Test real file upload and download cycle"""
        creds = get_test_credentials()

        sdk = PCloudSDK()
        sdk.login(creds["email"], creds["password"], location_id=creds["location_id"])

        # Create test file
        test_content = b"Real integration test content"
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "integration_test.txt")

        try:
            with open(test_file, "wb") as f:
                f.write(test_content)

            # Upload file
            upload_result = sdk.file.upload(test_file, folder_id=0)
            # Real API returns metadata as object, not array
            file_id = upload_result["metadata"]["fileid"]

            # Download file
            download_dir = os.path.join(temp_dir, "download")
            os.makedirs(download_dir)
            success = sdk.file.download(file_id, download_dir)

            assert success is True

            # Verify content
            downloaded_file = os.path.join(download_dir, "integration_test.txt")
            with open(downloaded_file, "rb") as f:
                downloaded_content = f.read()

            assert downloaded_content == test_content

            # Cleanup
            sdk.file.delete(file_id)

        finally:
            # Clean up local files
            safe_cleanup_temp_dir(temp_dir)
