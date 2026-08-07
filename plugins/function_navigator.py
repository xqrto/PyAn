import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (QDockWidget, QListWidget, QListWidgetItem,
                               QLabel, QVBoxLayout, QWidget)


class FunctionNavigatorPlugin(BasePlugin):
    name        = "Datei-/Funktions-Navigator"
    version     = "1.0"
    author      = "xqrto"
    description = "Listet alle def/class mit Zeilennummer, Klick springt zur Zeile."

    def on_startup(self, ide):
        self._ide = ide
        self._dock = None
        self._list = None

    # ── Dock-Widget ───────────────────────────────────────────────────────
    def _ensure_dock(self):
        if self._dock is not None:
            return self._dock
        self._list = QListWidget()
        self._list.setStyleSheet(
            "background:#1E1E1E;color:#D4D4D4;border:none;font:9pt Consolas;")
        self._list.itemDoubleClicked.connect(self._jump)
        self._list.itemActivated.connect(self._jump)

        header = QLabel(" FUNCTIONS / CLASSES ")
        header.setStyleSheet(
            "background:#2B2B2B;color:#007ACC;font-size:10px;font-weight:bold;"
            "padding:4px;border-bottom:1px solid #3F3F3F;")

        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(header)
        lay.addWidget(self._list)

        self._dock = QDockWidget("Navigator", self._ide)
        self._dock.setObjectName("FunctionNavigatorDock")
        self._dock.setWidget(box)
        self._ide.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dock)
        return self._dock

    # ── Scan ──────────────────────────────────────────────────────────────
    def _scan(self, editor=None):
        if editor is None:
            editor = self._ide._ed()
        if editor is None:
            return
        text = editor.toPlainText()
        lines = text.split("\n")
        items = []
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("def ") or stripped.startswith("class "):
                kind, rest = stripped.split(None, 1)
                # nur Deklarationen mit Namen, keine Dekoratoren-Zeilen
                name = rest.split("(", 1)[0].strip().rstrip(":")
                items.append((i, kind, name))
        self._list.clear()
        for i, kind, name in items:
            marker = "fun " if kind == "def" else "cls"
            label = f"{marker}  {name}   [{i}]"
            it = QListWidgetItem(label)
            it.setToolTip(f"Zeile {i}")
            it.setData(Qt.ItemDataRole.UserRole, (i, name))
            self._list.addItem(it)

    def _jump(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
        line, name = data
        editor = self._ide._ed()
        if editor is None:
            return
        block = editor.document().findBlockByLineNumber(line - 1)
        if not block.isValid():
            return
        cursor = QTextCursor(block)
        editor.setTextCursor(cursor)
        editor.setFocus()
        self._ide._toast_msg(f"{name}  →  Zeile {line}", "#007ACC")

    def _toggle_dock(self):
        dock = self._ensure_dock()
        if dock.isVisible():
            dock.hide()
        else:
            self._scan()
            dock.show(); dock.raise_()

    # ── Hooks ─────────────────────────────────────────────────────────────
    def on_tab_change(self, editor):
        if self._dock is not None and self._dock.isVisible():
            self._scan(editor)

    def on_file_open(self, path, editor):
        if self._dock is not None and self._dock.isVisible():
            self._scan(editor)

    def on_file_save(self, path, content):
        if self._dock is not None and self._dock.isVisible():
            self._scan()

    def add_menu_items(self):
        return [("Navigator anzeigen", self._toggle_dock)]

    def add_toolbar_items(self):
        return [("Navigator", self._toggle_dock)]


def register(registry):
    registry.register(FunctionNavigatorPlugin())