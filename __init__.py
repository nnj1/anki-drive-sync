from datetime import datetime
from aqt import mw, gui_hooks
from aqt.utils import showInfo, showCritical
from aqt.qt import QAction, qconnect
from .settings_dialog import show_settings
from .sync import upload_collection

def run_sync():
    def on_progress(p):
        mw.taskman.run_on_main(lambda: mw.progress.update(label=f"Syncing to Drive: {p}%", value=p, max=100))
    
    def do_sync(): return upload_collection(on_progress)

    def on_finished(future):
        mw.progress.finish()
        try:
            future.result()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            config = mw.addonManager.getConfig(__name__) or {}
            config["last_synced"] = now
            mw.addonManager.writeConfig(__name__, config)
            showInfo(f"Sync Successful!\nTime: {now}")
        except Exception as e: showCritical(f"Sync Failed: {e}")

    mw.progress.start(label="Preparing upload...", max=100, immediate=True)
    mw.taskman.run_in_background(do_sync, on_finished)

def add_sync_toolbar_button(links, toolbar):
    links.append(mw.toolbar.create_link("sync-action", "Drive Sync", run_sync, tip="Sync to Google Drive", id="sync-btn"))

gui_hooks.top_toolbar_did_init_links.append(add_sync_toolbar_button)

def setup_menu():
    action = QAction("Anki-Drive-Sync: Configure...", mw)
    qconnect(action.triggered, show_settings)
    mw.form.menuTools.addAction(action)

setup_menu()