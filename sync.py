import os, io, json, hashlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from .auth import get_credentials
from aqt import mw

FOLDER_NAME = "Anki-Drive-Sync"
META_FILE = "sync_meta.json"
MEDIA_META_FILE = "media_meta.json"

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

def get_file_id(service, folder_id, file_name):
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def get_hash(path):
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# --- Collection Logic ---

def download_collection(on_progress=None):
    service = get_drive_service()
    folder_id = get_or_create_folder(service)
    file_path = mw.col.path
    file_id = get_file_id(service, folder_id, os.path.basename(file_path))
    
    if not file_id: 
        raise FileNotFoundError("No cloud backup found.")

    # 1. Define a temporary path
    temp_path = file_path + ".tmp"
    
    # 2. Download to the temporary file
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(temp_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status and on_progress: 
                on_progress(int(status.progress() * 100))
    
    # 3. ATOMIC SWAP: Only replace the real database if download finished
    try:
        # Move the current database to a backup just in case
        backup_path = file_path + ".bak"
        if os.path.exists(file_path):
            os.replace(file_path, backup_path)
            
        # Move the downloaded temp file to the live location
        os.replace(temp_path, file_path)
        
        # Optionally remove the backup after success
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
    except Exception as e:
        # If the swap fails, try to restore the backup
        if os.path.exists(backup_path):
            os.replace(backup_path, file_path)
        raise e

    return True

def upload_collection(on_progress=None):
    service = get_drive_service()
    folder_id = get_or_create_folder(service)
    file_path = mw.col.path
    file_name = os.path.basename(file_path)

    sync_id = hashlib.sha1(os.urandom(16)).hexdigest()
    meta = {"last_sync_id": sync_id, "timestamp": os.path.getmtime(file_path)}
    
    # Database Upload (Uses Path)
    media = MediaFileUpload(file_path, mimetype='application/octet-stream', resumable=True)
    existing_id = get_file_id(service, folder_id, file_name)

    if existing_id:
        service.files().update(fileId=existing_id, media_body=media).execute()
    else:
        service.files().create(body={'name': file_name, 'parents': [folder_id]}, media_body=media).execute()

    # --- FIX: Metadata Upload (Uses BytesIO + MediaIoBaseUpload) ---
    meta_json = io.BytesIO(json.dumps(meta).encode('utf-8'))
    meta_body = MediaIoBaseUpload(meta_json, mimetype='application/json', resumable=False)

    meta_id = get_file_id(service, folder_id, META_FILE)
    if meta_id:
        service.files().update(fileId=meta_id, media_body=meta_body).execute()
    else:
        service.files().create(body={'name': META_FILE, 'parents': [folder_id]}, media_body=meta_body).execute()

    return sync_id

# --- Media Logic ---

def sync_media(log_callback=None):
    service = get_drive_service()
    folder_id = get_or_create_folder(service)
    media_dir = mw.col.media.dir()

    # Fix: Ensure remote_ledger is always a dict
    ledger_id = get_file_id(service, folder_id, MEDIA_META_FILE)
    remote_ledger = {}
    if ledger_id:
        try:
            request = service.files().get_media(fileId=ledger_id)
            remote_ledger = json.loads(request.execute())
        except Exception as e:
            if log_callback: log_callback(f"Ledger parse error: {e}")
            remote_ledger = {}

    local_files = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f)) and not f.startswith("_")]

    # Uploads
    for filename in local_files:
        path = os.path.join(media_dir, filename)
        local_hash = get_hash(path)

        # Check if we need to upload
        needs_upload = False
        if filename not in remote_ledger:
            needs_upload = True
        elif remote_ledger[filename].get('hash') != local_hash:
            needs_upload = True

        if needs_upload:
            if log_callback: log_callback(f"Uploading: {filename}")
            media_body = MediaFileUpload(path, resumable=True)
            
            # Check if file exists on Drive but is missing from our ledger
            drive_id = get_file_id(service, folder_id, filename)
            
            if drive_id:
                service.files().update(fileId=drive_id, media_body=media_body).execute()
            else:
                file_metadata = {'name': filename, 'parents': [folder_id]}
                f = service.files().create(body=file_metadata, media_body=media_body, fields='id').execute()
                drive_id = f.get('id')
            
            # Safety check to prevent NoneType assignment
            if drive_id:
                remote_ledger[filename] = {'hash': local_hash, 'id': drive_id}
            else:
                if log_callback: log_callback(f"Failed to get Drive ID for {filename}")

    # Download missing files from Drive to Local
    for filename, data in remote_ledger.items():
        if not isinstance(data, dict): continue # Guard against corrupted ledger entries
        local_path = os.path.join(media_dir, filename)
        if not os.path.exists(local_path):
            if log_callback: log_callback(f"Downloading: {filename}")
            try:
                request = service.files().get_media(fileId=data['id'])
                with open(local_path, "wb") as f:
                    f.write(request.execute())
            except Exception as e:
                if log_callback: log_callback(f"Error downloading {filename}: {e}")

    # --- FIX: Finalize Ledger (Uses BytesIO + MediaIoBaseUpload) ---
    ledger_json = io.BytesIO(json.dumps(remote_ledger).encode('utf-8'))
    ledger_body = MediaIoBaseUpload(ledger_json, mimetype='application/json', resumable=False)

    if ledger_id:
        service.files().update(fileId=ledger_id, media_body=ledger_body).execute()
    else:
        service.files().create(body={'name': MEDIA_META_FILE, 'parents': [folder_id]}, media_body=ledger_body).execute()