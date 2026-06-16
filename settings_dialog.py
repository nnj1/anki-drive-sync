import os
from aqt.qt import *
from aqt import mw
from aqt.utils import showCritical, showInfo, askUser
from .auth import get_credentials
from .sync import download_collection

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki-Drive-Sync Configuration")
        self.setMinimumWidth(400)
        self.addon_path = os.path.dirname(__file__)
        self.token_path = os.path.join(self.addon_path, 'token.json')

        layout = QVBoxLayout()
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        self.last_sync_label = QLabel()
        self.last_sync_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.last_sync_label)

        self.login_button = QPushButton("Sign In with Google")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        self.restore_button = QPushButton("Restore Collection from Drive")
        self.restore_button.clicked.connect(self.handle_restore)
        layout.addWidget(self.restore_button)

        self.logout_button = QPushButton("Sign Out / Disconnect")
        self.logout_button.clicked.connect(self.handle_logout)
        layout.addWidget(self.logout_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.refresh_ui()

    def refresh_ui(self):
        is_logged_in = os.path.exists(self.token_path)
        self.status_label.setText("Status: Connected" if is_logged_in else "Status: Not Connected")
        self.login_button.setVisible(not is_logged_in)
        self.logout_button.setVisible(is_logged_in)
        self.restore_button.setVisible(is_logged_in)

        config = mw.addonManager.getConfig(__name__) or {}
        self.last_sync_label.setText(f"Last Successful Sync: {config.get('last_synced', 'Never')}")

    def handle_login(self):
        try:
            get_credentials(self.addon_path)
            showInfo("Authenticated successfully!")
            self.refresh_ui()
        except Exception as e:
            showCritical(f"Login Failed: {e}")

    def handle_logout(self):
        if askUser("Sign out?"):
            if os.path.exists(self.token_path): os.remove(self.token_path)
            mw.addonManager.writeConfig(__name__, {"last_synced": "Never"})
            self.refresh_ui()

    def handle_restore(self):
        if not askUser("This will overwrite your local cards with the cloud version. Proceed?"):
            return

        # CRITICAL FIX: Capture the file path while mw.col STILL EXISTS
        if not mw.col:
            showCritical("No active collection found to restore over.")
            return
        current_col_path = mw.col.path 

        def on_progress(p): 
            mw.taskman.run_on_main(lambda: mw.progress.update(label=f"Downloading: {p}%", value=p))

        # This runs AFTER the profile is fully dead and file locks are released
        def start_download_after_unload():
            def do_dl():
                from .sync import download_collection
                # Pass the captured path into the download utility
                return download_collection(current_col_path, on_progress)

            def on_done(fut):
                mw.progress.finish()
                try:
                    fut.result()
                    
                    # Reload profile fresh
                    mw.loadProfile()
                    
                    # Catch the new cloud metadata sync ID and match it locally
                    try:
                        from .sync import get_drive_service, get_or_create_folder, get_file_id, META_FILE
                        import json
                        service = get_drive_service()
                        fid = get_or_create_folder(service)
                        meta_id = get_file_id(service, fid, META_FILE)
                        if meta_id:
                            res = service.files().get_media(fileId=meta_id).execute()
                            if res:
                                remote_meta = json.loads(res)
                                config = mw.addonManager.getConfig(__name__) or {}
                                config["last_sync_id"] = remote_meta.get("last_sync_id")
                                mw.addonManager.writeConfig(__name__, config)
                    except Exception:
                        pass
                    
                    showInfo("Restore complete! Your collection has been updated successfully.")
                    
                except Exception as e: 
                    showCritical(f"Failed to restore: {e}")
                    # Safety net: bring the profile back online if the download errors out
                    mw.loadProfile()

            mw.progress.start(label="Downloading from Drive...", immediate=True)
            mw.taskman.run_in_background(do_dl, on_done)

        # 1. Close the settings dialog FIRST so its UI loops don't conflict with unloadProfile
        self.accept()

        # 2. Trigger the asynchronous profile unload
        mw.unloadProfile(onsuccess=start_download_after_unload)

def show_settings():
    SettingsDialog(mw).exec()