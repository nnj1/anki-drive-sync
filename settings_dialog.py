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
        if not askUser("This will overwrite your local cards. Anki will restart. Proceed?"): return
        def on_progress(p): mw.taskman.run_on_main(lambda: mw.progress.update(label=f"Downloading: {p}%", value=p))
        def do_dl():
            mw.col.close()
            return download_collection(on_progress)
        def on_done(fut):
            mw.progress.finish()
            try:
                fut.result()
                showInfo("Restore complete. Restarting Anki...")
                mw.close()
            except Exception as e: showCritical(f"Failed: {e}")
        mw.progress.start(label="Downloading...", immediate=True)
        mw.taskman.run_in_background(do_dl, on_done)

def show_settings():
    SettingsDialog(mw).exec()