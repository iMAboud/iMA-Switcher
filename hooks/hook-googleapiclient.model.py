import os
import googleapiclient
from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('google_api_python_client')

docs_dir = os.path.join(os.path.dirname(googleapiclient.__file__), 'discovery_cache', 'documents')
drive_v3 = os.path.join(docs_dir, 'drive.v3.json')
if os.path.exists(drive_v3):
    datas.append((drive_v3, os.path.join('googleapiclient', 'discovery_cache', 'documents')))
