"""
Google Drive Uploader Module
Upload videos to Google Drive with automatic folder creation and naming
"""

import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

# Google API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    DRIVE_AVAILABLE = True
except ImportError:
    DRIVE_AVAILABLE = False


class DriveUploader:
    """Google Drive uploader with Service Account authentication"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(
        self, 
        credentials_path: Optional[str] = None,
        root_folder_id: Optional[str] = None
    ):
        """
        Initialize Drive uploader
        
        Args:
            credentials_path: Path to service account JSON file
            root_folder_id: Parent folder ID where project folders will be created
        """
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        self.root_folder_id = root_folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.service = None
        self._authenticated = False
        
    @property
    def is_available(self) -> bool:
        """Check if Google Drive API is available"""
        return DRIVE_AVAILABLE
    
    @property
    def is_configured(self) -> bool:
        """Check if credentials are configured"""
        return bool(self.credentials_path and self.root_folder_id)
    
    def authenticate(self) -> bool:
        """
        Authenticate with Google Drive using Service Account
        
        Returns:
            True if authentication successful
        """
        if not DRIVE_AVAILABLE:
            raise RuntimeError("Google API libraries not installed. Run: pip install google-api-python-client google-auth")
        
        if not self.credentials_path:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE not configured")
        
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Service account file not found: {self.credentials_path}")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials)
            self._authenticated = True
            return True
        except Exception as e:
            raise RuntimeError(f"Authentication failed: {e}")
    
    def _ensure_authenticated(self):
        """Ensure service is authenticated before operations"""
        if not self._authenticated:
            self.authenticate()
    
    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid characters from filename"""
        # Replace invalid chars with underscore
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        return sanitized or "Untitled"
    
    def find_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find a folder by name in the specified parent
        
        Args:
            folder_name: Name of folder to find
            parent_id: Parent folder ID (uses root if not specified)
            
        Returns:
            Folder ID if found, None otherwise
        """
        self._ensure_authenticated()
        
        parent = parent_id or self.root_folder_id
        
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent:
            query += f" and '{parent}' in parents"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        files = results.get('files', [])
        return files[0]['id'] if files else None
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive
        
        Args:
            folder_name: Name of the folder
            parent_id: Parent folder ID (uses root if not specified)
            
        Returns:
            Created folder ID
        """
        self._ensure_authenticated()
        
        safe_name = self._sanitize_filename(folder_name)
        parent = parent_id or self.root_folder_id
        
        file_metadata = {
            'name': safe_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent:
            file_metadata['parents'] = [parent]
        
        folder = self.service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    
    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Get existing folder or create if not exists
        
        Args:
            folder_name: Name of the folder
            parent_id: Parent folder ID
            
        Returns:
            Folder ID
        """
        existing = self.find_folder(folder_name, parent_id)
        if existing:
            return existing
        return self.create_folder(folder_name, parent_id)
    
    def create_project_folder(self, project_title: str) -> str:
        """
        Create a project folder inside root folder
        
        Args:
            project_title: Project title for folder name
            
        Returns:
            Project folder ID
        """
        # Add timestamp to make folder unique
        timestamp = datetime.now().strftime("%Y%m%d")
        folder_name = f"{project_title}_{timestamp}"
        
        return self.get_or_create_folder(folder_name, self.root_folder_id)
    
    def upload_video(
        self,
        file_path: str,
        scene_number: int,
        project_folder_id: str,
        custom_name: Optional[str] = None
    ) -> dict:
        """
        Upload a video file to Google Drive
        
        Args:
            file_path: Local path to video file
            scene_number: Scene number for naming (1, 2, 3...)
            project_folder_id: Target folder ID
            custom_name: Optional custom filename
            
        Returns:
            Dict with 'id', 'name', 'webViewLink'
        """
        self._ensure_authenticated()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Video file not found: {file_path}")
        
        # Determine file extension
        ext = Path(file_path).suffix or '.mp4'
        
        # Generate filename: Scene_01.mp4, Scene_02.mp4, etc.
        if custom_name:
            filename = self._sanitize_filename(custom_name)
        else:
            filename = f"Scene_{scene_number:02d}{ext}"
        
        # Determine MIME type
        mime_types = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
        }
        mime_type = mime_types.get(ext.lower(), 'video/mp4')
        
        file_metadata = {
            'name': filename,
            'parents': [project_folder_id]
        }
        
        # Use resumable upload for large files
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'webViewLink': file.get('webViewLink')
        }
    
    def upload_scene_videos(
        self,
        video_files: list[tuple[str, int]],
        project_title: str,
        progress_callback: Optional[callable] = None
    ) -> dict:
        """
        Upload multiple scene videos to a project folder
        
        Args:
            video_files: List of (file_path, scene_number) tuples
            project_title: Project title for folder naming
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            Dict with 'folder_id', 'folder_url', 'files' (list of uploaded files)
        """
        self._ensure_authenticated()
        
        # Create project folder
        folder_id = self.create_project_folder(project_title)
        
        # Get folder URL
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
        
        uploaded_files = []
        total = len(video_files)
        
        for i, (file_path, scene_number) in enumerate(video_files, 1):
            if progress_callback:
                progress_callback(i, total, Path(file_path).name)
            
            try:
                result = self.upload_video(file_path, scene_number, folder_id)
                uploaded_files.append({
                    'scene': scene_number,
                    **result
                })
            except Exception as e:
                uploaded_files.append({
                    'scene': scene_number,
                    'error': str(e)
                })
        
        return {
            'folder_id': folder_id,
            'folder_url': folder_url,
            'files': uploaded_files
        }
    
    def list_files(self, folder_id: Optional[str] = None) -> list[dict]:
        """
        List files in a folder
        
        Args:
            folder_id: Folder ID (uses root if not specified)
            
        Returns:
            List of file dicts with 'id', 'name', 'mimeType'
        """
        self._ensure_authenticated()
        
        parent = folder_id or self.root_folder_id
        
        query = f"'{parent}' in parents and trashed=false"
        
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType, webViewLink, size)',
            orderBy='name'
        ).execute()
        
        return results.get('files', [])


# Singleton instance for easy import
_uploader: Optional[DriveUploader] = None

def get_drive_uploader() -> DriveUploader:
    """Get or create singleton DriveUploader instance"""
    global _uploader
    if _uploader is None:
        _uploader = DriveUploader()
    return _uploader
