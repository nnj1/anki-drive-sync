from aqt import mw, gui_hooks
from aqt.utils import showInfo
from aqt.qt import QAction, qconnect

# --- 1. CORE ACTIONS ---

def run_sync():
    """Logic for the actual syncing process."""
    # This will eventually hold your Google Drive upload/download code
    showInfo("Anki-Drive-Sync: Syncing with Google Drive now...")

def open_settings():
    """Logic for the configuration and Google Login."""
    # This will eventually open a popup window for OAuth and settings
    showInfo("Anki-Drive-Sync Settings: Please sign into Google Drive.")

# --- 2. TOOLBAR INTEGRATION (The 'Sync' Button) ---

def add_sync_toolbar_button(links, toolbar):
    """Adds the quick-sync button to the top toolbar."""
    sync_link = mw.toolbar.create_link(
        "anki-drive-sync-action",
        "Drive Sync",
        run_sync, # Note: This calls the SYNC function
        tip="Quick Sync with Google Drive",
        id="sync-btn"
    )
    links.append(sync_link)

gui_hooks.top_toolbar_did_init_links.append(add_sync_toolbar_button)

# --- 3. TOOLS MENU INTEGRATION (The 'Settings' Option) ---

def setup_menu():
    """Adds the configuration option under the Tools menu."""
    # Create the menu item
    action = QAction("Google Drive Sync Configuration", mw)
    # Link it to the SETTINGS function
    qconnect(action.triggered, open_settings)
    # Add to Tools menu
    mw.form.menuTools.addAction(action)

setup_menu()