import os
import time
from typing import Any, Dict, Optional

import requests

from pcloud_sdk.app import App
from pcloud_sdk.config import Config
from pcloud_sdk.exceptions import PCloudException
from pcloud_sdk.request import Request


class File:
    """File class for file operations"""

    def __init__(self, app: App):
        self.request = Request(app)
        self.part_size = Config.FILE_PART_SIZE

    def get_link(self, file_id: int) -> str:
        """Get download link for file"""
        params = {"fileid": file_id}
        try:
            response = self.request.get("getfilelink", params)
            # Assuming self.request.get raises PCloudException if response['result'] != 0
            if "hosts" in response:
                return f"https://{response['hosts'][0]}{response['path']}"
            else:
                # Handles cases where the API call might 'succeed' (result=0) but not return 'hosts'
                raise PCloudException("Failed to get file link!")
        except PCloudException:
            # Catches PCloudException from self.request.get (e.g. API error like "File not found")
            # or from the 'else' block above. Re-raises with the consistent message.
            raise PCloudException("Failed to get file link!")

    def download(
        self,
        file_id: int,
        destination: str = "",
        progress_callback: Optional[callable] = None,
    ) -> bool:
        """Download file to local destination"""
        file_link = self.get_link(file_id)

        if destination:
            destination = destination.replace("\\", os.sep).replace("/", os.sep)
            if not destination.endswith(os.sep):
                destination += os.sep

        if destination and not os.path.exists(destination):
            os.makedirs(destination)

        # Extract filename from URL
        filename = file_link.split("/")[-1]
        file_path = destination + filename

        # Download file in chunks
        response = requests.get(file_link, stream=True, verify=False)
        response.raise_for_status()

        # Get file size from headers
        total_size = int(response.headers.get("content-length", 0))
        downloaded_bytes = 0
        start_time = time.time()

        # Initialize progress callback
        if progress_callback:
            progress_callback(
                0,
                total_size,
                0.0,
                0.0,
                operation="download",
                filename=filename,
                status="starting",
            )

        temp_path = file_path + ".download"
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.part_size):
                if chunk:
                    f.write(chunk)
                    downloaded_bytes += len(chunk)

                    # Update progress
                    if progress_callback and total_size > 0:
                        elapsed = time.time() - start_time
                        speed = downloaded_bytes / elapsed if elapsed > 0 else 0
                        percentage = (downloaded_bytes / total_size) * 100
                        progress_callback(
                            downloaded_bytes,
                            total_size,
                            percentage,
                            speed,
                            operation="download",
                            filename=filename,
                        )

        # Final progress update
        if progress_callback:
            elapsed = time.time() - start_time
            speed = downloaded_bytes / elapsed if elapsed > 0 else 0
            progress_callback(
                downloaded_bytes,
                total_size,
                100.0,
                speed,
                operation="download",
                filename=filename,
                status="completed",
            )

        # Rename temp file to final name
        os.rename(temp_path, file_path)
        return True

    def upload(
        self,
        file_path: str,
        folder_id: int = 0,
        filename: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Upload file to pCloud"""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise PCloudException("Invalid file")

        if not filename:
            filename = os.path.basename(file_path)

        print(f"🔄 Démarrage de l'upload: {filename}")

        # Create upload session
        try:
            upload_info = self._create_upload()
            upload_id = upload_info["uploadid"]
            print(f"✅ Session d'upload créée: {upload_id}")
        except Exception as e:
            raise PCloudException(
                f"Erreur lors de la création de la session d'upload: {e}"
            )

        # Upload file in chunks
        file_size = os.path.getsize(file_path)
        uploaded_bytes = 0
        start_time = time.time()

        params = {"uploadid": upload_id, "uploadoffset": 0}

        # Initialize progress callback
        if progress_callback:
            progress_callback(
                0,
                file_size,
                0.0,
                0.0,
                operation="upload",
                filename=filename,
                status="starting",
            )
        else:
            print(f"📤 Upload en cours... ({file_size:,} bytes)")

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(self.part_size)
                if not chunk:
                    break

                # Retry logic for chunk upload
                num_failures = 0
                while num_failures < 10:
                    try:
                        self._write(chunk, params)
                        uploaded_bytes += len(chunk)
                        params["uploadoffset"] = uploaded_bytes

                        # Progress update
                        elapsed = time.time() - start_time
                        speed = uploaded_bytes / elapsed if elapsed > 0 else 0
                        percentage = (uploaded_bytes / file_size) * 100

                        if progress_callback:
                            progress_callback(
                                uploaded_bytes,
                                file_size,
                                percentage,
                                speed,
                                operation="upload",
                                filename=filename,
                            )
                        else:
                            print(
                                f"  📊 Progression: {percentage:.1f}% ({uploaded_bytes:,}/{file_size:,} bytes)"
                            )
                        break
                    except Exception as e:
                        num_failures += 1
                        if num_failures < 10:
                            if not progress_callback:
                                print(
                                    f"  ⚠️ Retry {num_failures}/10 for this chunk: {e}"
                                )
                            time.sleep(3)
                        else:
                            if progress_callback:
                                progress_callback(
                                    uploaded_bytes,
                                    file_size,
                                    percentage,
                                    speed,
                                    operation="upload",
                                    filename=filename,
                                    status="error",
                                    error=f"Upload échoué après {num_failures} tentatives: {e}",
                                )
                            raise PCloudException(
                                f"Upload échoué après {num_failures} tentatives: {e}"
                            )

        # Update progress for saving phase
        if progress_callback:
            elapsed = time.time() - start_time
            speed = uploaded_bytes / elapsed if elapsed > 0 else 0
            progress_callback(
                uploaded_bytes,
                file_size,
                100.0,
                speed,
                operation="upload",
                filename=filename,
                status="saving",
            )
        else:
            print(f"✅ Upload completed, saving...")

        # Save uploaded file
        try:
            result = self._save(upload_id, filename, folder_id)

            # Final progress update
            if progress_callback:
                elapsed = time.time() - start_time
                speed = uploaded_bytes / elapsed if elapsed > 0 else 0
                progress_callback(
                    uploaded_bytes,
                    file_size,
                    100.0,
                    speed,
                    operation="upload",
                    filename=filename,
                    status="completed",
                )
            else:
                print(f"✅ File saved successfully!")
            return result
        except Exception as e:
            if progress_callback:
                elapsed = time.time() - start_time
                speed = uploaded_bytes / elapsed if elapsed > 0 else 0
                progress_callback(
                    uploaded_bytes,
                    file_size,
                    100.0,
                    speed,
                    operation="upload",
                    filename=filename,
                    status="error",
                    error=f"Error during save: {e}",
                )
            raise PCloudException(f"Error during save: {e}")

    def delete(self, file_id: int) -> Dict[str, Any]:
        """Delete file"""
        response = self.request.get("deletefile", {"fileid": file_id})
        return response.get("metadata", {}).get("isdeleted", response)

    def rename(self, file_id: int, name: str) -> Dict[str, Any]:
        """Rename file"""
        if not name:
            raise PCloudException("Please provide valid file name!")

        params = {"fileid": file_id, "toname": name}
        return self.request.get("renamefile", params)

    def move(self, file_id: int, folder_id: int) -> Dict[str, Any]:
        """Move file to another folder"""
        params = {"fileid": file_id, "tofolderid": folder_id}
        return self.request.get("renamefile", params)

    def copy(self, file_id: int, folder_id: int) -> Dict[str, Any]:
        """Copy file to another folder"""
        params = {"fileid": file_id, "tofolderid": folder_id}
        return self.request.get("copyfile", params)

    def get_info(self, file_id: int) -> Dict[str, Any]:
        """Get file information"""
        return self.request.get("checksumfile", {"fileid": file_id})

    def _create_upload(self) -> Dict[str, Any]:
        """Create upload session"""
        return self.request.get("upload_create")

    def _save(self, upload_id: int, name: str, folder_id: int) -> Dict[str, Any]:
        """Save uploaded file"""
        # Debug: afficher les paramètres reçus
        print(
            f"  🔍 _save debug: upload_id={upload_id}, name='{name}', folder_id={folder_id}"
        )

        params = {"uploadid": upload_id, "name": name}

        # Handle destination folder
        if folder_id is None or folder_id == 0:
            # For root folder, try different approaches
            # First try with folderid=0 (standard approach)
            params["folderid"] = 0
        else:
            params["folderid"] = folder_id

        print(f"  🔍 Paramètres upload_save: {params}")

        try:
            result = self.request.get("upload_save", params)
            print(f"  ✅ upload_save réussi")
            return result
        except PCloudException as e:
            # If it fails with folderid=0, try with path="/"
            if "folderid" in params and params["folderid"] == 0:
                print(f"  🔄 Retry upload_save with path='/' instead of folderid=0")
                params = {"uploadid": upload_id, "name": name, "path": "/"}
                print(f"  🔍 Nouveaux paramètres: {params}")
                return self.request.get("upload_save", params)
            else:
                raise e

    def _write(self, content: bytes, params: Dict[str, Any]):
        """Write content chunk during upload"""
        try:
            self.request.put("upload_write", content, params)
        except Exception as e:
            # Plus de détails sur l'erreur pour debug
            raise PCloudException(f"Erreur lors de l'écriture du chunk: {e}")
