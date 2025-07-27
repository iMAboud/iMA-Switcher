import os
import pickle
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

class GoogleDriveAPI:
    def __init__(self, user_data_dir):
        self.user_data_dir = user_data_dir
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.credentials_file = os.path.join(sys._MEIPASS, 'credentials.json')
        else:
            self.credentials_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        self.token_file = os.path.join(self.user_data_dir, 'token.pickle')
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.service = self._get_service()

    def _get_service(self):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        return build('drive', 'v3', credentials=creds)

    def upload_file(self, file_path, file_name):
        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype='application/zip')
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

    def find_latest_backup(self, file_prefix):
        """Finds the most recent backup file with the given prefix."""
        query = f"name contains '{file_prefix}' and mimeType = 'application/zip'"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, modifiedTime)',
            orderBy='modifiedTime desc'
        ).execute()
        items = results.get('files', [])
        return items[0] if items else None

    def find_all_backups(self, file_prefix):
        """Finds all backup files with the given prefix."""
        query = f"name contains '{file_prefix}' and mimeType = 'application/zip'"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        return results.get('files', [])

    def delete_file(self, file_id):
        """Deletes a file by its ID."""
        self.service.files().delete(fileId=file_id).execute()

    def download_file(self, file_id, destination):
        request = self.service.files().get_media(fileId=file_id)
        with open(destination, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
