from aqt import mw, gui_hooks
from aqt.utils import showInfo
from aqt.qt import QAction, qconnect
# Import the function from our new file
from .settings_dialog import show_settings

# --- 1. CORE ACTIONS ---

def run_sync():
    """Logic for the actual syncing process."""
    showInfo("Anki-Drive-Sync: Syncing with Google Drive now...")

# --- 2. TOOLBAR INTEGRATION ---

def add_sync_toolbar_button(links, toolbar):
    sync_link = mw.toolbar.create_link(
        "anki-drive-sync-action",
        "Drive Sync",
        run_sync,
        tip="Quick Sync with Google Drive",
        id="sync-btn"
    )
    links.append(sync_link)

gui_hooks.top_toolbar_did_init_links.append(add_sync_toolbar_button)

# --- 3. TOOLS MENU INTEGRATION ---

def setup_menu():
    # Link the menu option to show_settings instead of open_settings
    action = QAction("Anki-Drive-Sync: Configure...", mw)
    qconnect(action.triggered, show_settings)
    mw.form.menuTools.addAction(action)

setup_menu()