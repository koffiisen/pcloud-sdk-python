import os
from typing import Any, Dict, List, Optional, Union

from pcloud_sdk.app import App
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.request import Request


class Folder:
    """Folder class for folder operations"""

    def __init__(self, app: App):
        self.request = Request(app)

    def get_metadata(
        self, folder_id: Optional[int] = None, path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get folder metadata"""
        params = {}

        if folder_id is not None and folder_id > 0:
            params["folderid"] = folder_id
        elif path is not None:
            # Normalize path to use forward slashes for the API
            normalized_path = path.replace("\\", "/") # For literal escaped backslashes
            normalized_path = normalized_path.replace(os.sep, "/") # For os-specific separators
            params["path"] = normalized_path
        elif folder_id == 0: # Root folder by ID
            # API expects path="/" for root folder metadata via listfolder
            params["path"] = "/"
        else: # Default to root if no identifier given
            params["path"] = "/"

        return self.request.get("listfolder", params)

    def search(self, path: str) -> Dict[str, Any]:
        """
        Lists the content of the parent of the specified `path` to find the folder.
        The `path` is expected to be the full path to the target folder.
        """
        if not path:
            # If path is empty, consider parent as root. Or raise PCloudException as in list_folder.
            # For consistency with previous dirname behavior on empty string, leads to effectively asking for root content.
            # os.path.dirname('') is '', which if fed to API might be issue. API needs '/'.
            parent_api_path = "/"
        else:
            # Normalize input path to use forward slashes
            normalized_path = path.replace("\\", "/")
            normalized_path = normalized_path.replace(os.sep, "/")

            # Create a temporary path that 'looks' absolute for os.path.dirname
            # This ensures consistent behavior of os.path.dirname across platforms
            temp_path_for_dirname = normalized_path
            if not temp_path_for_dirname.startswith('/'):
                temp_path_for_dirname = '/' + temp_path_for_dirname

            # Standardize: remove trailing slashes, unless it's the root path itself
            # e.g., "/foo/bar/" becomes "/foo/bar", but "/" remains "/"
            if len(temp_path_for_dirname) > 1:
                temp_path_for_dirname = temp_path_for_dirname.rstrip('/')

            # Get the parent directory using os.path.dirname
            # os.path.dirname("/foo/bar") returns "/foo"
            # os.path.dirname("/foo") returns "/"
            # os.path.dirname("/") returns "/"
            parent_dir = os.path.dirname(temp_path_for_dirname)

            # Ensure the path is absolute, which os.path.dirname on an absolute temp_path_for_dirname should provide.
            # If parent_dir somehow ended up empty (e.g. if input path was just "file" and dirname logic was different),
            # it should default to root "/". But with current logic, it should be "/".
            parent_api_path = parent_dir

        params = {"nofiles": 1, "path": parent_api_path}
        return self.request.get("listfolder", params)

    def list_folder(
        self, folder: Optional[Union[str, int]] = None
    ) -> Optional[Dict[str, Any]]: # Return type is Dict or None, not List
        """
        Lists folder information.
        If folder is a path string, returns metadata of the target folder.
        If folder is an ID, returns metadata of that folder.
        If folder is None, returns metadata of the root folder.
        Returns None if the path or ID is invalid or not found.
        """
        if folder is None:
            # Corresponds to listing the root folder itself, so return its metadata
            root_meta_response = self.get_metadata(path="/")
            return root_meta_response.get("metadata")

        if isinstance(folder, str):
            # Handle path-based folder listing
            normalized_path = folder.replace("\\", "/") # For literal double backslashes
            normalized_path = normalized_path.replace(os.sep, "/") # For os.sep

            # Remove leading/trailing slashes that might cause empty parts or misinterpretation
            normalized_path = normalized_path.strip("/")

            if not normalized_path:  # Path was effectively "/" or empty
                root_meta_response = self.get_metadata(path="/")
                return root_meta_response.get("metadata")

            path_parts = normalized_path.split('/')

            # Start with root folder's metadata
            # Ensure get_metadata and its response["metadata"] are valid
            current_folder_meta_response = self.get_metadata(path="/")
            if not current_folder_meta_response or "metadata" not in current_folder_meta_response:
                return None # Unable to fetch root metadata
            current_folder_metadata = current_folder_meta_response["metadata"]

            for i, part_name in enumerate(path_parts):
                if not part_name: # Should not happen if strip("/") and split('/') are correct
                    continue

                found_next_folder = False
                contents = current_folder_metadata.get("contents", [])
                if not isinstance(contents, list):
                    return None  # Current folder has no contents or malformed metadata

                for item in contents:
                    if item.get("isfolder") and item.get("name") == part_name:
                        # This item is the metadata summary of the folder named part_name
                        # If it's the last part of the path, we've found our target folder.
                        if i == len(path_parts) - 1:
                            return item  # Return the metadata of the target folder
                        else:
                            # It's an intermediate folder. We need its full metadata (including its contents)
                            # to continue traversing.
                            folder_id = item.get("folderid")
                            if folder_id is None:
                                return None  # Malformed item, no folderid

                            next_folder_meta_response = self.get_metadata(folder_id=folder_id)
                            if not next_folder_meta_response or "metadata" not in next_folder_meta_response:
                                return None # Unable to fetch metadata for the next folder part
                            current_folder_metadata = next_folder_meta_response["metadata"]
                            found_next_folder = True
                            break  # Move to the next part_name

                if not found_next_folder:
                    return None  # Path part (part_name) not found in current_folder_metadata's contents

            # If the loop finishes, it means all parts were processed.
            # This state should ideally be caught by returning `item` when `i == len(path_parts) - 1`.
            # If path_parts was empty (e.g. folder was "/"), it's handled before the loop.
            # If loop completes, it implies path was valid and target found and returned.
            # If path was valid but structure was unexpected (e.g. file at end of path), this might be an issue.
            # However, tests expect metadata of the folder.
            # This return is a fallback, should ideally not be reached if logic is perfect.
            return None


        # Handle integer folder ID
        if isinstance(folder, int):
            folder_id = folder
            metadata_response = self.get_metadata(folder_id=folder_id)
            return metadata_response.get("metadata")

        # Fallback for unexpected folder type, though typing suggests str or int
        return None

    def list_root(self) -> Dict[str, Any]:
        """List root folder"""
        root_metadata = self.get_metadata(path="/")
        return {
            "contents": root_metadata.get("metadata", {}).get("contents", []),
            "metadata": root_metadata.get("metadata", {}),
        }

    def get_content(
        self, folder_id: Optional[int] = None, path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get folder content"""
        if folder_id is None and path is None:
            # Dossier racine par défaut
            folder_metadata = self.get_metadata(path="/")
        elif folder_id is not None:
            folder_metadata = self.get_metadata(folder_id=folder_id)
        else:
            folder_metadata = self.get_metadata(path=path)

        # Extraire le contenu de la réponse
        if "metadata" in folder_metadata:
            contents = folder_metadata["metadata"].get("contents", [])
            return contents if isinstance(contents, list) else []
        else:
            # Parfois la réponse est directement le contenu
            contents = folder_metadata.get("contents", [])
            return contents if isinstance(contents, list) else []

    def create(self, name: str, parent: int = 0) -> Union[int, Dict[str, Any]]:
        """Create new folder"""
        if not name:
            raise PCloudException("Please provide valid folder name")

        params = {"name": name}

        if parent >= 0:
            # Use folderid for both root (0) and other folders
            params["folderid"] = parent
        else:
            # Only use path if parent is not specified or negative
            params["path"] = "/"

        response = self.request.get("createfolder", params)
        folder_id = response.get("metadata", {}).get("folderid")
        return folder_id if folder_id is not None else response

    def rename(self, folder_id: int, name: str) -> Union[int, Dict[str, Any]]:
        """Rename folder"""
        if not name:
            raise PCloudException("Please provide folder name")

        params = {"toname": name, "folderid": folder_id}

        response = self.request.get("renamefolder", params)
        result_folder_id = response.get("metadata", {}).get("folderid")
        return result_folder_id if result_folder_id is not None else response

    def move(self, folder_id: int, new_parent: int) -> Union[int, Dict[str, Any]]:
        """Move folder"""
        params = {"tofolderid": new_parent, "folderid": folder_id}

        response = self.request.get("renamefolder", params)
        moved_folder_id = response.get("metadata", {}).get("folderid")
        return moved_folder_id if moved_folder_id is not None else response

    def delete(self, folder_id: int) -> Dict[str, Any]:
        """Delete folder"""
        response = self.request.get("deletefolder", {"folderid": folder_id})
        is_deleted = response.get("metadata", {}).get("isdeleted")
        return is_deleted if is_deleted is not None else response

    def delete_recursive(self, folder_id: int) -> Dict[str, Any]:
        """Delete folder recursively"""
        return self.request.get("deletefolderrecursive", {"folderid": folder_id})
