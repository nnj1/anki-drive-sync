import os, io
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from .auth import get_credentials
from aqt import mw

FOLDER_NAME = "Anki-Drive-Sync"

def get_drive_service():
    addon_path = os.path.dirname(__file__)
    creds = get_credentials(addon_path)
    return build('drive', 'v3', credentials=creds)

def get_or_create_folder(service):
    query = f"name = '{FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    if files: return files[0]['id']
    folder = service.files().create(body={'name': FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder'}, fields='id').execute()
    return folder.get('id')

def get_existing_file_id(service, folder_id, file_name):
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def upload_collection(on_progress=None):
    service = get_drive_service()
    folder_id = get_or_create_folder(service)
    file_path = mw.col.path
    file_name = os.path.basename(file_path)
    existing_id = get_existing_file_id(service, folder_id, file_name)

    media = MediaFileUpload(file_path, mimetype='application/octet-stream', resumable=True, chunksize=1024*1024)
    if existing_id:
        request = service.files().update(fileId=existing_id, media_body=media, fields='id')
    else:
        request = service.files().create(body={'name': file_name, 'parents': [folder_id]}, media_body=media, fields='id')

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and on_progress: on_progress(int(status.progress() * 100))
    return response.get('id')

def download_collection(on_progress=None):
    service = get_drive_service()
    folder_id = get_or_create_folder(service)
    file_path = mw.col.path
    file_id = get_existing_file_id(service, folder_id, os.path.basename(file_path))
    if not file_id: raise FileNotFoundError("No cloud backup found.")

    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status and on_progress: on_progress(int(status.progress() * 100))
    return True