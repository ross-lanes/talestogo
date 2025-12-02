"""
Google Drive Client for NSTXView

Provides read-only access to the NSTX papers folder in Google Drive.
Supports listing, downloading, and syncing papers.
"""

import os
import io
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from app.config import NSTXVIEW_DRIVE_FOLDER_ID, NSTXVIEW_STORAGE_BUCKET

logger = logging.getLogger(__name__)


class DriveFile:
    """Represents a file from Google Drive"""
    def __init__(self, file_data: Dict[str, Any]):
        self.id = file_data.get('id')
        self.name = file_data.get('name')
        self.mime_type = file_data.get('mimeType')
        self.size = int(file_data.get('size', 0))
        self.created_time = file_data.get('createdTime')
        self.modified_time = file_data.get('modifiedTime')
        self.parents = file_data.get('parents', [])
        self.web_view_link = file_data.get('webViewLink')

    def is_pdf(self) -> bool:
        return self.mime_type == 'application/pdf'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'mime_type': self.mime_type,
            'size': self.size,
            'created_time': self.created_time,
            'modified_time': self.modified_time,
            'web_view_link': self.web_view_link
        }


class DriveClient:
    """
    Client for interacting with Google Drive to access NSTX papers.

    Supports:
    - Listing all PDFs in the source folder (including subfolders)
    - Downloading PDFs to local storage or cloud storage
    - Tracking file metadata for sync operations
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize the Drive client.

        Args:
            credentials_path: Path to service account JSON file.
                            If not provided, uses GOOGLE_APPLICATION_CREDENTIALS env var.
        """
        self.folder_id = NSTXVIEW_DRIVE_FOLDER_ID
        self.service = None
        self._credentials_path = credentials_path or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    def _get_service(self):
        """Get or create the Drive service"""
        if self.service is None:
            if not self._credentials_path:
                raise ValueError(
                    "Google credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS "
                    "environment variable or provide credentials_path."
                )

            credentials = service_account.Credentials.from_service_account_file(
                self._credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)

        return self.service

    def list_pdfs(self, folder_id: Optional[str] = None) -> List[DriveFile]:
        """
        List all PDF files in the folder and subfolders.

        Args:
            folder_id: Folder ID to search. Defaults to configured folder.

        Returns:
            List of DriveFile objects for all PDFs found.
        """
        folder_id = folder_id or self.folder_id
        service = self._get_service()
        all_files = []

        try:
            # Get all items in this folder
            query = f"'{folder_id}' in parents and trashed = false"
            page_token = None

            while True:
                results = service.files().list(
                    q=query,
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink)",
                    pageToken=page_token
                ).execute()

                items = results.get('files', [])

                for item in items:
                    drive_file = DriveFile(item)

                    if drive_file.is_pdf():
                        all_files.append(drive_file)
                    elif drive_file.mime_type == 'application/vnd.google-apps.folder':
                        # Recursively search subfolders
                        subfolder_files = self.list_pdfs(drive_file.id)
                        all_files.extend(subfolder_files)

                page_token = results.get('nextPageToken')
                if not page_token:
                    break

            logger.info(f"Found {len(all_files)} PDF files in Drive folder")
            return all_files

        except HttpError as e:
            logger.error(f"Error listing files from Drive: {e}")
            raise

    def get_folder_structure(self, folder_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get mapping of folder IDs to folder paths.

        Returns:
            Dict mapping folder ID to full path (e.g., "subfolder1/subfolder2")
        """
        folder_id = folder_id or self.folder_id
        service = self._get_service()
        folder_paths = {folder_id: ""}

        def get_subfolders(parent_id: str, parent_path: str):
            query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

            results = service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()

            for folder in results.get('files', []):
                folder_path = f"{parent_path}/{folder['name']}" if parent_path else folder['name']
                folder_paths[folder['id']] = folder_path
                get_subfolders(folder['id'], folder_path)

        try:
            get_subfolders(folder_id, "")
            return folder_paths
        except HttpError as e:
            logger.error(f"Error getting folder structure: {e}")
            raise

    def download_file(self, file_id: str, destination: str) -> str:
        """
        Download a file from Drive to local storage.

        Args:
            file_id: Google Drive file ID
            destination: Local path to save the file

        Returns:
            Path to the downloaded file
        """
        service = self._get_service()

        try:
            # Ensure destination directory exists
            Path(destination).parent.mkdir(parents=True, exist_ok=True)

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            # Write to file
            fh.seek(0)
            with open(destination, 'wb') as f:
                f.write(fh.read())

            logger.info(f"Downloaded file {file_id} to {destination}")
            return destination

        except HttpError as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise

    def download_to_bytes(self, file_id: str) -> bytes:
        """
        Download a file from Drive to memory.

        Args:
            file_id: Google Drive file ID

        Returns:
            File contents as bytes
        """
        service = self._get_service()

        try:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            return fh.read()

        except HttpError as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise

    def get_file_metadata(self, file_id: str) -> DriveFile:
        """
        Get metadata for a specific file.

        Args:
            file_id: Google Drive file ID

        Returns:
            DriveFile object with metadata
        """
        service = self._get_service()

        try:
            file_data = service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime, parents, webViewLink"
            ).execute()

            return DriveFile(file_data)

        except HttpError as e:
            logger.error(f"Error getting file metadata for {file_id}: {e}")
            raise

    def sync_with_database(self, db_file_ids: set) -> Dict[str, List[DriveFile]]:
        """
        Compare Drive contents with database to find new/removed files.

        Args:
            db_file_ids: Set of Drive file IDs already in database

        Returns:
            Dict with 'new' and 'removed' lists of files
        """
        drive_files = self.list_pdfs()
        drive_file_ids = {f.id for f in drive_files}

        new_files = [f for f in drive_files if f.id not in db_file_ids]
        removed_ids = db_file_ids - drive_file_ids

        logger.info(f"Sync result: {len(new_files)} new files, {len(removed_ids)} removed")

        return {
            'new': new_files,
            'removed_ids': list(removed_ids)
        }


# Convenience function for quick access
def get_drive_client() -> DriveClient:
    """Get a configured DriveClient instance"""
    return DriveClient()
