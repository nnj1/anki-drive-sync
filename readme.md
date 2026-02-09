# anki-drive-sync

**anki-drive-sync** is an add-on for Anki that enables users to sync their flashcard decks using their own personal Google Drive storage. 

This add-on is designed for users who want full ownership of their data or need to sync large media collections that exceed standard cloud limits.

## ✨ Features

* **Quick Sync Button:** A dedicated "Drive Sync" button in the top toolbar for one-click synchronization.
* **Centralized Configuration:** Manage your Google account association and sync settings via the `Tools` menu.
* **Personal Cloud Storage:** Uses your private Google Drive space to store backups and collection data.
* **Privacy-First:** Data is transferred directly between Anki and Google; no third-party servers are involved.

## 🚀 Installation

### For Users
1.  Open Anki.
2.  Go to `Tools` -> `Add-ons`.
3.  Click `Get Add-ons...`.
4.  Enter the code: `[Your-Add-on-Code-Here]` (Placeholder).
5.  Restart Anki.

### For Developers (Manual Setup)
1.  Navigate to your Anki add-ons folder:
    * **Windows:** `%APPDATA%\Anki2\addons21`
    * **macOS:** `~/Library/Application Support/Anki2/addons21`
2.  Clone this repository into the `anki-drive-sync` folder:
    ```bash
    git clone [https://github.com/your-username/anki-drive-sync.git](https://github.com/your-username/anki-drive-sync.git)
    ```
3.  Install the required Python dependencies in your virtual environment:
    ```bash
    pip install -r requirements.txt
    ```

## 🛠️ How to Use

1.  **Account Setup:** Go to `Tools` -> `Anki-Drive-Sync: Configure...`. Follow the prompts to sign into your Google account and authorize the add-on.
2.  **Syncing:** Click the **Drive Sync** button in the top toolbar next to "Decks" to upload/download your latest changes.

## 📂 Project Structure

* `__init__.py`: Handles UI hooks for the toolbar and Tools menu.
* `manifest.json`: Metadata for the Anki add-on manager.
* `requirements.txt`: List of dependencies including `google-api-python-client`.

## 📄 License
This project is licensed under the MIT License.