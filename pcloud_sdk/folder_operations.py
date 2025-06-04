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
            params["path"] = path
        elif folder_id == 0:
            # Pour le dossier racine, utiliser path="/" au lieu de folderid=0
            params["path"] = "/"
        else:
            # Dossier racine par défaut
            params["path"] = "/"

        return self.request.get("listfolder", params)

    def search(self, path: str) -> Dict[str, Any]:
        """Search for folder by path"""
        path = os.path.dirname(path)
        print(f"Searching for folder: {path}")

        params = {"nofiles": 1, "path": path}
        return self.request.get("listfolder", params)

    def list_folder(
        self, folder: Optional[Union[str, int]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """List folder contents"""
        if folder is None:
            return self.get_content()  # Dossier racine

        if isinstance(folder, str):
            # Handle path-based folder listing
            extension = os.path.splitext(folder)[1]
            if extension:
                folder = os.path.dirname(folder)

            path_parts = folder.split(os.sep)
            path_parts.reverse()

            current_folder_id = None
            current_path = "/"
            directory = None

            while path_parts:
                folder_name = path_parts.pop()
                if current_folder_id is not None:
                    folder_items = self.get_content(current_folder_id)
                else:
                    folder_items = self.get_content(path=current_path)

                for item in folder_items:
                    if item.get("isfolder") and item.get("name", "").startswith(
                        folder_name
                    ):
                        current_folder_id = item["folderid"]
                        directory = item
                        break

            return directory

        return self.get_content(int(folder))

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
            return folder_metadata["metadata"].get("contents", [])
        else:
            # Parfois la réponse est directement le contenu
            return folder_metadata.get("contents", [])

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
        return response.get("metadata", {}).get("folderid", response)

    def rename(self, folder_id: int, name: str) -> Union[int, Dict[str, Any]]:
        """Rename folder"""
        if not name:
            raise PCloudException("Please provide folder name")

        params = {"toname": name, "folderid": folder_id}

        response = self.request.get("renamefolder", params)
        return response.get("metadata", {}).get("folderid", response)

    def move(self, folder_id: int, new_parent: int) -> Union[int, Dict[str, Any]]:
        """Move folder"""
        params = {"tofolderid": new_parent, "folderid": folder_id}

        response = self.request.get("renamefolder", params)
        return response.get("metadata", {}).get("folderid", response)

    def delete(self, folder_id: int) -> Dict[str, Any]:
        """Delete folder"""
        response = self.request.get("deletefolder", {"folderid": folder_id})
        return response.get("metadata", {}).get("isdeleted", response)

    def delete_recursive(self, folder_id: int) -> Dict[str, Any]:
        """Delete folder recursively"""
        return self.request.get("deletefolderrecursive", {"folderid": folder_id})
