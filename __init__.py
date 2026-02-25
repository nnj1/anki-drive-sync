import json
from aqt import mw, gui_hooks
from aqt.utils import showInfo, askUser, showCritical
from aqt.qt import QAction, qconnect
from .sync import upload_collection, sync_media, get_drive_service, get_or_create_folder, get_file_id, META_FILE
from .settings_dialog import show_settings
from .log_window import SyncLogWindow

def run_full_sync():
    log_win = SyncLogWindow(mw)
    log_win.show()

    def log_msg(m):
        mw.taskman.run_on_main(lambda: log_win.log(m))

    def do_sync():
        service = get_drive_service()
        fid = get_or_create_folder(service)
        meta_id = get_file_id(service, fid, META_FILE)

        # Conflict Check
        if meta_id:
            res = service.files().get_media(fileId=meta_id).execute()
            remote_meta = json.loads(res)
            local_sync_id = mw.addonManager.getConfig(__name__).get("last_sync_id")
            if local_sync_id and remote_meta["last_sync_id"] != local_sync_id:
                if not askUser("Cloud version is newer/different. Overwrite Cloud?"):
                    return "cancelled"

        log_msg("Starting Database Sync...")
        new_id = upload_collection()

        log_msg("Starting Media Sync (Hashing files)...")
        sync_media(log_callback=log_msg)

        return new_id

    def on_finished(future):
        try:
            res = future.result()
            if res != "cancelled":
                # Get existing config or start with empty dict
                config = mw.addonManager.getConfig(__name__) or {}
                
                config["last_sync_id"] = res
                mw.addonManager.writeConfig(__name__, config)
                
                log_msg("--- Sync Successfully Finished ---")
                showInfo("Sync Complete!")
        except Exception as e:
            showCritical(f"Sync Failed: {e}")

    mw.taskman.run_in_background(do_sync, on_finished)

# Setup Menu and Toolbar
def setup_ui():
    # Toolbar Button
    gui_hooks.top_toolbar_did_init_links.append(
        lambda l, t: l.append(mw.toolbar.create_link("sync-btn", "Drive Sync", run_full_sync))
    )
    # Tools Menu
    action = QAction("Anki-Drive-Sync: Configure...", mw)
    qconnect(action.triggered, show_settings)
    mw.form.menuTools.addAction(action)

setup_ui()