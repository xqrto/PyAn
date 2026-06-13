import os
import urllib.request
import threading
from __main__ import BasePlugin
from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QMessageBox, QLabel
from PySide6.QtCore import Qt, Slot, QMetaObject, Q_ARG

class PluginBrowserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyANIDE - Plugin Browser")
        self.resize(380, 480)
        self.layout = QVBoxLayout(self)

        self.status_label = QLabel("Loading available plugins...", self)
        self.layout.addWidget(self.status_label)

        self.list_widget = QListWidget(self)
        self.layout.addWidget(self.list_widget)

        self.download_btn = QPushButton("Install Plugin", self)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.download_selected)
        self.layout.addWidget(self.download_btn)

        self.list_widget.itemSelectionChanged.connect(self.on_selection_changed)

        self.plugins_raw = []
        self.fetch_plugin_list()

    def fetch_plugin_list(self):
        url = "https://raw.githubusercontent.com/xqrto/PyAn/main/plugins/plugins.txt"
        threading.Thread(target=self._fetch_action, args=(url,), daemon=True).start()

    def _fetch_action(self, url):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
            self.plugins_raw = [line.strip() for line in content.splitlines() if line.strip()]
            QMetaObject.invokeMethod(self, "populate_list", Qt.QueuedConnection)
        except Exception:
            QMetaObject.invokeMethod(self, "show_fetch_error", Qt.QueuedConnection)

    @Slot()
    def populate_list(self):
        self.list_widget.clear()
        for plugin in self.plugins_raw:
            display_name = plugin[:-3] if plugin.lower().endswith(".py") else plugin
            self.list_widget.addItem(display_name)
        self.status_label.setText(f"{len(self.plugins_raw)} plugins found.")

    @Slot()
    def show_fetch_error(self):
        self.status_label.setText("Error fetching the plugin list.")
        QMessageBox.critical(self, "Error", "Could not fetch the plugin list from GitHub.")

    def on_selection_changed(self):
        self.download_btn.setEnabled(len(self.list_widget.selectedItems()) > 0)

    def download_selected(self):
        selected_index = self.list_widget.currentRow()
        if selected_index < 0 or selected_index >= len(self.plugins_raw):
            return
        plugin_filename = self.plugins_raw[selected_index]
        if not plugin_filename.lower().endswith(".py"):
            plugin_filename += ".py"

        appdata = os.environ.get("APPDATA")
        if not appdata:
            appdata = os.path.expanduser("~")
        dest_dir = os.path.join(appdata, "pyan", "plugins")
        dest_path = os.path.join(dest_dir, plugin_filename)
        raw_download_url = f"https://raw.githubusercontent.com/xqrto/PyAn/main/plugins/{plugin_filename}"
        self.status_label.setText(f"Installing {plugin_filename}...")
        self.download_btn.setEnabled(False)
        threading.Thread(
            target=self._download_action,
            args=(raw_download_url, dest_path, plugin_filename),
            daemon=True
        ).start()

    def _download_action(self, url, dest_path, filename):
        try:
            with urllib.request.urlopen(url, timeout=15) as response:
                code = response.read()

            # Make folders if they don't exist yet
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            with open(dest_path, "wb") as f:
                f.write(code)

            QMetaObject.invokeMethod(self, "show_success", Qt.QueuedConnection, Q_ARG(str, filename))
        except Exception as e:
            QMetaObject.invokeMethod(self, "show_download_error", Qt.QueuedConnection, Q_ARG(str, str(e)))

    @Slot(str)
    def show_success(self, filename):
        self.status_label.setText("Installation completed.")
        self.download_btn.setEnabled(True)
        QMessageBox.information(
            self,
            "Success",
            f"The plugin '{filename}' was successfully installed to your plugins directory!\n\nPlease restart PyANIDE to load it."
        )

    @Slot(str)
    def show_download_error(self, error_msg):
        self.status_label.setText("Installation failed.")
        self.download_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Error", f"Failed to download the plugin:\n{error_msg}")

class PluginBrowserPlugin(BasePlugin):
    name = "Plugin Browser"
    version = "1.0"
    author = "PyANIDE Developer"

    def on_startup(self, ide):
        self._ide = ide

    def add_toolbar_items(self):
        return [
            ("Browse Plugins", self.open_browser)
        ]

    def open_browser(self):
        dialog = PluginBrowserDialog()
        dialog.exec()

def register(registry):
    registry.register(PluginBrowserPlugin())

