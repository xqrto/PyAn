from __main__ import BasePlugin
import os
import tempfile
import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit,
    QLineEdit, QLabel
)

class DeveloperTimelinePlugin(BasePlugin):
    name = "Logs"
    version = "1.0"

    def on_startup(self, ide):
        self._ide = ide

        self.log_file = os.path.join(
            tempfile.gettempdir(),
            "pyan_dev_timeline.log"
        )

        self._write_log("PLUGIN_START", "Logs Started")

    def _write_log(self, event, message):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        line = f"[{ts}] [{event}] {message}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except:
            pass

    def on_file_open(self, path, editor):
        self._write_log("FILE_OPEN", path)

    def on_file_save(self, path, content):
        self._write_log("FILE_SAVE", path)

    def on_before_run(self, script_path):
        self._write_log("RUN_START", script_path)

    def on_build_done(self, success, exe_path):
        self._write_log("BUILD_DONE", f"{success} | {exe_path}")

    def on_tab_change(self, editor):
        self._write_log("TAB_CHANGE", "Tab gewechselt")

    def on_key_press(self, event, editor):
        # bewusst NICHT jedes keypress loggen (zu viel)
        pass

    def add_menu_items(self):
        return [
            ("📜 Show Logs", self.show_logs),
            ("🧹 Clear Logs", self.clear_logs),
        ]

    def add_toolbar_items(self):
        return [
            ("Logs", self.show_logs),
        ]

    def clear_logs(self):
        try:
            open(self.log_file, "w").close()
            self._write_log("CLEAR", "Logs gelöscht")
        except:
            pass

    def show_logs(self):
        dlg = QDialog(self._ide)
        dlg.setWindowTitle("Developer Timeline Logs")
        dlg.resize(700, 500)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🔍 Search Logs:"))
        search = QLineEdit()
        search.setPlaceholderText("Type to filter logs...")
        layout.addWidget(search)
        text = QTextEdit()
        text.setReadOnly(True)
        layout.addWidget(text)
        dlg.setLayout(layout)
        def load_logs(filter_text=""):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                if filter_text:
                    lines = [l for l in lines if filter_text.lower() in l.lower()]
                text.setPlainText("".join(lines))
            except:
                text.setPlainText("No logs found")
        load_logs()
        def on_search():
            load_logs(search.text())
        search.textChanged.connect(on_search)
        dlg.show()
def register(registry):
    registry.register(DeveloperTimelinePlugin())