"""
Requirements Installer Plugin für PyANIDE
Installiert Abhängigkeiten aus requirements.txt per Toolbar-Button.
- Findet requirements.txt automatisch im Arbeitsverzeichnis
- Falls keine gefunden: Auswahl aller .txt-Dateien im Verzeichnis
- Nutzt echtes python.exe (PyInstaller-sicher)
"""

from __main__ import BasePlugin
import os
import subprocess
import shutil


def find_python() -> str | None:
    """
    Sucht das echte python.exe — PyInstaller-sicher.
    sys.executable zeigt bei gefrorenen EXEs auf pyan.exe.
    """
    import shutil

    # 1. Windows Launcher
    py = shutil.which("py")
    if py:
        return py

    # 2. PATH
    for candidate in ("python", "python3"):
        path = shutil.which(candidate)
        if path and "pyan" not in path.lower():
            return path

    # 3. Registry
    try:
        import winreg
        for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for subkey in (
                r"SOFTWARE\Python\PythonCore",
                r"SOFTWARE\WOW6432Node\Python\PythonCore",
            ):
                try:
                    with winreg.OpenKey(hive, subkey) as core:
                        i = 0
                        while True:
                            try:
                                ver = winreg.EnumKey(core, i)
                                with winreg.OpenKey(core, rf"{ver}\InstallPath") as ip:
                                    exe, _ = winreg.QueryValueEx(ip, "ExecutablePath")
                                    if exe and "pyan" not in exe.lower():
                                        return exe
                            except OSError:
                                break
                            i += 1
                except OSError:
                    continue
    except Exception:
        pass

    return None


REQUIREMENTS_NAMES = {
    "requirements.txt",
    "requirements-dev.txt",
    "requirements_dev.txt",
    "requirements-prod.txt",
    "requirements_prod.txt",
    "require.txt",
    "deps.txt",
    "dependencies.txt",
}


def get_working_dir(ide) -> str | None:
    """Ermittelt das aktuelle Arbeitsverzeichnis aus der IDE."""
    try:
        editor = ide._ed()
        # Versuche Dateipfad des aktuellen Tabs zu bekommen
        path = getattr(editor, "file_path", None) or getattr(editor, "_file_path", None)
        if path and os.path.isfile(path):
            return os.path.dirname(path)
    except Exception:
        pass

    # Fallback: aktuelles Arbeitsverzeichnis
    return os.getcwd()


def find_requirements(work_dir: str) -> str | None:
    """Sucht nach einer bekannten requirements-Datei im Verzeichnis."""
    for name in REQUIREMENTS_NAMES:
        full = os.path.join(work_dir, name)
        if os.path.isfile(full):
            return full
    return None


def find_all_txt_files(work_dir: str) -> list:
    """Gibt alle .txt-Dateien im Arbeitsverzeichnis zurück."""
    try:
        return [
            os.path.join(work_dir, f)
            for f in os.listdir(work_dir)
            if f.lower().endswith(".txt") and os.path.isfile(os.path.join(work_dir, f))
        ]
    except Exception:
        return []


def run_pip_install_r(req_file: str) -> tuple:
    """Führt pip install -r <datei> aus. Gibt (success, output) zurück."""
    python = find_python()
    if not python:
        return False, (
            "Kein Python-Interpreter gefunden.\n"
            "Bitte stelle sicher, dass Python im PATH eingetragen ist."
        )

    try:
        result = subprocess.run(
            [python, "-m", "pip", "install", "-r", req_file],
            capture_output=True,
            text=True,
            timeout=300
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Timeout — Installation hat zu lange gedauert."
    except Exception as e:
        return False, str(e)


class RequirementsInstallerPlugin(BasePlugin):
    name    = "Requirements Installer"
    version = "1.0"
    author  = "PyANIDE Plugin"

    def on_startup(self, ide):
        self._ide = ide

    # ------------------------------------------------------------------
    # Toolbar-Button
    # ------------------------------------------------------------------
    def add_toolbar_items(self):
        return [
            ("📦 Install Requirements", self._install)
        ]

    # ------------------------------------------------------------------
    # Menüeintrag (Plugins-Tab)
    # ------------------------------------------------------------------
    def add_menu_items(self):
        return [
            ("Install from Requirements", self._install)
        ]

    # ------------------------------------------------------------------
    # Hauptlogik
    # ------------------------------------------------------------------
    def _install(self):
        from PySide6.QtWidgets import (
            QMessageBox, QInputDialog, QListWidget,
            QDialog, QVBoxLayout, QDialogButtonBox,
            QLabel, QListWidgetItem, QAbstractItemView
        )

        work_dir = get_working_dir(self._ide)
        if not work_dir or not os.path.isdir(work_dir):
            QMessageBox.warning(
                None,
                "Requirements Installer",
                "Kein gültiges Arbeitsverzeichnis gefunden.\n"
                "Bitte öffne zuerst eine Datei."
            )
            return

        # Automatisch bekannte requirements.txt suchen
        req_file = find_requirements(work_dir)

        if req_file:
            # Gefunden → direkt bestätigen lassen
            reply = QMessageBox.question(
                None,
                "Requirements gefunden",
                f"Gefunden:\n{req_file}\n\nJetzt installieren?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        else:
            # Nicht gefunden → alle .txt-Dateien zur Auswahl anbieten
            txt_files = find_all_txt_files(work_dir)

            if not txt_files:
                QMessageBox.information(
                    None,
                    "Requirements Installer",
                    f"Keine .txt-Dateien in:\n{work_dir}\n\n"
                    "Lege eine requirements.txt an und versuche es erneut."
                )
                return

            # Auswahl-Dialog
            dialog = QDialog()
            dialog.setWindowTitle("Keine requirements.txt gefunden")
            dialog.setMinimumWidth(420)
            layout = QVBoxLayout(dialog)

            label = QLabel(
                f"Keine requirements.txt in:\n{work_dir}\n\n"
                "Wähle eine .txt-Datei aus:"
            )
            label.setWordWrap(True)
            layout.addWidget(label)

            list_widget = QListWidget()
            list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
            for f in txt_files:
                item = QListWidgetItem(os.path.basename(f))
                item.setData(256, f)  # voller Pfad im UserRole
                list_widget.addItem(item)
            list_widget.setCurrentRow(0)
            layout.addWidget(list_widget)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)

            if dialog.exec() != QDialog.Accepted:
                return

            selected = list_widget.currentItem()
            if not selected:
                return

            req_file = selected.data(256)

        # Installation durchführen
        success, output = run_pip_install_r(req_file)

        if success:
            QMessageBox.information(
                None,
                "Installation abgeschlossen ✓",
                f"Alle Pakete aus\n{os.path.basename(req_file)}\n"
                f"wurden erfolgreich installiert."
            )
        else:
            # Ausgabe kürzen falls zu lang
            short_output = output[:800] + ("..." if len(output) > 800 else "")
            QMessageBox.critical(
                None,
                "Installationsfehler",
                f"pip meldete einen Fehler:\n\n{short_output}"
            )


def register(registry):
    registry.register(RequirementsInstallerPlugin())