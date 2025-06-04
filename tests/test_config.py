"""
Test configuration module for pCloud SDK tests
Loads environment variables from .env file and provides test utilities
"""

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file in tests directory
tests_dir = Path(__file__).parent
env_file = tests_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

# Test credentials
PCLOUD_EMAIL = os.getenv("PCLOUD_EMAIL", "test@example.com")
PCLOUD_PASSWORD = os.getenv("PCLOUD_PASSWORD", "test_password")
PCLOUD_ACCESS_TOKEN = os.getenv("PCLOUD_ACCESS_TOKEN", "test_token_123")

# OAuth2 credentials
PCLOUD_CLIENT_ID = os.getenv("PCLOUD_CLIENT_ID", "test_client_id")
PCLOUD_CLIENT_SECRET = os.getenv("PCLOUD_CLIENT_SECRET", "test_client_secret")

# Test configuration
PCLOUD_LOCATION_ID = int(os.getenv("PCLOUD_LOCATION_ID", "2"))
PCLOUD_TEST_FOLDER_NAME = os.getenv("PCLOUD_TEST_FOLDER_NAME", "test_pcloud_sdk")
PCLOUD_API_BASE_URL = os.getenv("PCLOUD_API_BASE_URL", "https://eapi.pcloud.com")

# Test execution flags
RUN_INTEGRATION_TESTS = os.getenv("RUN_INTEGRATION_TESTS", "false").lower() == "true"
RUN_PERFORMANCE_TESTS = os.getenv("RUN_PERFORMANCE_TESTS", "false").lower() == "true"

def has_real_credentials():
    """Check if real pCloud credentials are available"""
    return (
        PCLOUD_EMAIL != "test@example.com" and
        PCLOUD_PASSWORD != "test_password" and
        "@" in PCLOUD_EMAIL
    )

def has_oauth2_credentials():
    """Check if OAuth2 credentials are available"""
    return (
        PCLOUD_CLIENT_ID != "test_client_id" and
        PCLOUD_CLIENT_SECRET != "test_client_secret"
    )

def get_test_credentials():
    """Get test credentials dictionary"""
    return {
        "email": PCLOUD_EMAIL,
        "password": PCLOUD_PASSWORD,
        "access_token": PCLOUD_ACCESS_TOKEN,
        "location_id": PCLOUD_LOCATION_ID
    }

def get_oauth2_credentials():
    """Get OAuth2 credentials dictionary"""
    return {
        "client_id": PCLOUD_CLIENT_ID,
        "client_secret": PCLOUD_CLIENT_SECRET,
        "location_id": PCLOUD_LOCATION_ID
    }

def requires_real_credentials(func):
    """Decorator to skip tests that require real credentials"""
    import pytest

    def wrapper(*args, **kwargs):
        if not has_real_credentials():
            pytest.skip("Requires real pCloud credentials in .env file")
        return func(*args, **kwargs)
    return wrapper

def requires_oauth2_credentials(func):
    """Decorator to skip tests that require OAuth2 credentials"""
    import pytest

    def wrapper(*args, **kwargs):
        if not has_oauth2_credentials():
            pytest.skip("Requires OAuth2 credentials in .env file")
        return func(*args, **kwargs)
    return wrapper

def skip_if_no_integration_tests(func):
    """Decorator to skip integration tests unless explicitly enabled"""
    import pytest

    def wrapper(*args, **kwargs):
        if not RUN_INTEGRATION_TESTS:
            pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=true in .env to enable")
        return func(*args, **kwargs)
    return wrapper


# Test cleanup utilities
def safe_remove_file(file_path):
    """Safely remove a file with proper error handling"""
    if not file_path:
        return

    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Handle read-only files
            try:
                os.chmod(file_path, 0o666)
            except (OSError, PermissionError):
                pass  # Ignore permission errors when changing permissions

            os.remove(file_path)
    except (OSError, PermissionError, FileNotFoundError) as e:
        # Silently ignore common cleanup errors
        # In tests, it's better to continue than to fail on cleanup
        pass
    except Exception:
        # Catch any other unexpected errors and continue
        pass


def safe_remove_directory(dir_path):
    """Safely remove a directory and all its contents with proper error handling"""
    if not dir_path:
        return

    try:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            # First try to make the directory and its contents writable
            try:
                for root, dirs, files in os.walk(dir_path):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), 0o777)
                        except (OSError, PermissionError):
                            pass
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), 0o666)
                        except (OSError, PermissionError):
                            pass
            except Exception:
                pass  # Continue even if chmod fails

            # Remove the directory tree
            shutil.rmtree(dir_path, ignore_errors=True)
    except Exception:
        # Fallback: try to remove individual files and directories
        try:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path, topdown=False):
                    for f in files:
                        safe_remove_file(os.path.join(root, f))
                    for d in dirs:
                        try:
                            os.rmdir(os.path.join(root, d))
                        except (OSError, PermissionError):
                            pass
                # Finally try to remove the root directory
                try:
                    os.rmdir(dir_path)
                except (OSError, PermissionError):
                    pass
        except Exception:
            pass  # Ultimate fallback: just continue


def safe_cleanup_temp_dir(temp_dir):
    """Safely cleanup a temporary directory used in tests"""
    if not temp_dir or not os.path.exists(temp_dir):
        return

    try:
        # Remove all files and subdirectories first
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            if os.path.isfile(item_path):
                safe_remove_file(item_path)
            elif os.path.isdir(item_path):
                safe_remove_directory(item_path)

        # Finally remove the temp directory itself
        try:
            os.rmdir(temp_dir)
        except (OSError, PermissionError):
            # If rmdir fails, try shutil.rmtree as a fallback
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        # Ultimate fallback: try shutil.rmtree
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass