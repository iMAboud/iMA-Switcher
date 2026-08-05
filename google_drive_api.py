import os
import pickle
import sys
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError
from pathlib import Path

class GoogleDriveAPI:
    def __init__(self, user_data_dir):
        self.user_data_dir = user_data_dir
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.credentials_file = Path(sys._MEIPASS) / 'credentials.json'
        else:
            self.credentials_file = Path(__file__).parent / 'credentials.json'
        self.token_file = Path(self.user_data_dir) / 'token.pickle'
        self.scopes = ['https://www.googleapis.com/auth/drive.file']
        self.service = self._get_service()

    def _get_service(self):
        creds = None
        try:
            if self.token_file.exists():
                try:
                    with self.token_file.open('rb') as token:
                        creds = pickle.load(token)
                except Exception as pe:
                    logging.warning(f"Could not load token.pickle: {pe}. Re-authenticating...")
                    creds = None

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as re:
                        logging.warning(f"Could not refresh Google token: {re}. Re-authenticating...")
                        creds = None

                if not creds or not creds.valid:
                    if not self.credentials_file.exists():
                        raise FileNotFoundError(f"Google Drive credentials file not found at {self.credentials_file}")
                    flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_file), self.scopes)
                    creds = flow.run_local_server(port=0, host='127.0.0.1')

                try:
                    with self.token_file.open('wb') as token:
                        pickle.dump(creds, token)
                except Exception as pe:
                    logging.warning(f"Could not save token.pickle: {pe}")

            return build('drive', 'v3', credentials=creds)
        except (HttpError, pickle.PickleError, FileNotFoundError, Exception) as e:
            logging.error(f"Failed to get Google Drive service: {e}")
            raise ConnectionAbortedError(f"Could not connect to Google Drive. Please check your credentials and connection. Details: {e}")

    def upload_file(self, file_path, file_name):
        try:
            file_metadata = {'name': file_name}
            media = MediaFileUpload(file_path, mimetype='application/zip', resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except HttpError as e:
            logging.error(f"Google Drive API error during file upload: {e}")
            raise IOError(f"Failed to upload file to Google Drive: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during file upload: {e}")
            raise

    def find_latest_backup(self, file_prefix):
        """Finds the most recent backup file with the given prefix."""
        try:
            query = f"name contains '{file_prefix}' and mimeType = 'application/zip'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime)',
                orderBy='modifiedTime desc'
            ).execute()
            items = results.get('files', [])
            return items[0] if items else None
        except HttpError as e:
            logging.error(f"Google Drive API error while finding latest backup: {e}")
            raise IOError(f"Failed to find latest backup on Google Drive: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while finding latest backup: {e}")
            raise

    def find_all_backups(self, file_prefix):
        """Finds all backup files with the given prefix."""
        try:
            query = f"name contains '{file_prefix}' and mimeType = 'application/zip'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            return results.get('files', [])
        except HttpError as e:
            logging.error(f"Google Drive API error while finding all backups: {e}")
            raise IOError(f"Failed to find backups on Google Drive: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while finding all backups: {e}")
            raise

    def delete_file(self, file_id):
        """Deletes a file by its ID."""
        try:
            self.service.files().delete(fileId=file_id).execute()
        except HttpError as e:
            logging.error(f"Google Drive API error during file deletion: {e}")
            raise IOError(f"Failed to delete file from Google Drive: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during file deletion: {e}")
            raise

    def download_file(self, file_id, destination):
        try:
            request = self.service.files().get_media(fileId=file_id)
            with open(destination, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
        except HttpError as e:
            logging.error(f"Google Drive API error during file download: {e}")
            raise IOError(f"Failed to download file from Google Drive: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during file download: {e}")
            raise
