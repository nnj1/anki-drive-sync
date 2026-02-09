import os
from aqt.qt import *
from aqt import mw
from aqt.utils import showCritical, showInfo, askUser
from .auth import get_credentials

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anki-Drive-Sync Configuration")
        self.setMinimumWidth(400)
        
        # Path to this addon folder
        self.addon_path = os.path.dirname(__file__)
        self.token_path = os.path.join(self.addon_path, 'token.json')

        layout = QVBoxLayout()
        
        # Status Label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

        # Action Buttons Container
        self.button_layout = QVBoxLayout()
        
        self.login_button = QPushButton("Sign In with Google")
        self.login_button.clicked.connect(self.handle_login)
        
        self.logout_button = QPushButton("Sign Out / Disconnect Account")
        self.logout_button.clicked.connect(self.handle_logout)
        
        self.button_layout.addWidget(self.login_button)
        self.button_layout.addWidget(self.logout_button)
        layout.addLayout(self.button_layout)

        # Standard Close Button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        self.refresh_ui()

    def refresh_ui(self):
        """Updates the label and button visibility based on login state."""
        if os.path.exists(self.token_path):
            self.status_label.setText("Status: Connected to Google Drive")
            self.login_button.hide()
            self.logout_button.show()
        else:
            self.status_label.setText("Status: Not Connected")
            self.login_button.show()
            self.logout_button.hide()

    def handle_login(self):
        try:
            self.status_label.setText("Status: Check your web browser...")
            get_credentials(self.addon_path)
            showInfo("Google Drive access granted successfully.")
            self.refresh_ui()
        except Exception as e:
            showCritical(f"Error during login: {str(e)}")
            self.refresh_ui()

    def handle_logout(self):
        if askUser("Are you sure you want to sign out? This will remove your local Google Drive session."):
            if os.path.exists(self.token_path):
                os.remove(self.token_path)
            self.refresh_ui()
            showInfo("Signed out successfully.")

def show_settings():
    dialog = SettingsDialog(mw)
    dialog.exec()