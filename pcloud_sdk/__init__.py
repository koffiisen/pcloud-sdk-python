"""
pCloud SDK for Python v2.0
Modern Python SDK for pCloud API with automatic token management and progress tracking
"""
from .app import App
from .config import Config
# Main SDK class
from .core import PCloudSDK
from .exceptions import PCloudException
from .file_operations import File
from .folder_operations import Folder
from .progress_utils import (
    create_progress_bar, create_detailed_progress,
    create_minimal_progress, create_silent_progress,
    SimpleProgressBar, DetailedProgress, MinimalProgress, SilentProgress
)
from .request import Request, HttpClient
from .response import Response
from .user_operations import User

__version__ = "2.0.0"
__author__ = "Converted from pCloud PHP SDK"
__license__ = "MIT"

__all__ = [
    # Main SDK
    "PCloudSDK",

    # Core classes
    "App", "Request", "Response", "HttpClient", "Config", "PCloudException",

    # Operation classes
    "File", "Folder", "User",

    # Progress utilities
    "create_progress_bar", "create_detailed_progress",
    "create_minimal_progress", "create_silent_progress",
    "SimpleProgressBar", "DetailedProgress", "MinimalProgress", "SilentProgress"
]
