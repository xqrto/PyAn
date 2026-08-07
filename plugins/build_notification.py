import os

class BuildNotificationPlugin(BasePlugin):
    name        = "Build-Benachrichtigung"
    version     = "1.0"
    author      = "xqrto"
    description = "Zeigt Build-Ergebnis, EXE-Pfad und -Größe; öffnet den EXE-Ordner."

    def on_startup(self, ide):
        self._ide = ide
        self.auto_open = False      # Ordner nach erfolgreichem Build automatisch öffnen

    # ── Hooks ─────────────────────────────────────────────────────────────
    def on_build_done(self, success, exe_path):
        try:
            ide = self._ide
            self._last_exe = exe_path
            if not success:
                ide.console.err("\n[BuildNotification] Build fehlgeschlagen.\n")
                ide._toast_msg("Build fehlgeschlagen — siehe Output", "#F44747", 5000)
                return

            ide.console.ok("\n[BuildNotification] Erfolgreich: ")
            ide.console.write(f"{exe_path}\n", "#D4D4D4")

            if exe_path and os.path.isfile(exe_path):
                size = os.path.getsize(exe_path) / 1024 / 1024
                ide.console.dim(f"    Größe: {size:.2f} MB\n")
                ide.console.dim("    Ordner öffnen? → Menü/Toolbar 'EXE-Ordner'\n")
                ide._toast_msg(f"Build OK  →  {os.path.basename(exe_path)} ({size:.2f} MB)",
                               "#4EC9B0", 5000)
                if self.auto_open:
                    self._open_folder(exe_path)
            else:
                ide.console.dim(f"    EXE nicht gefunden: {exe_path}\n")
                ide._toast_msg("Build OK (EXE-Pfad unklar)", "#DCDCAA", 4000)
        except Exception as e:
            self._ide.console.err(f"[build_notify] {e}\n")

    def _open_folder(self, exe_path=None):
        ide = self._ide
        if not exe_path:
            exe_path = getattr(self, "_last_exe", None)
        if not exe_path:
            ide._toast_msg("Noch kein Build-Ergebnis", "#DCDCAA")
            return
        folder = os.path.dirname(exe_path)
        try:
            os.startfile(folder)
            ide._toast_msg(f"Ordner geöffnet: {folder}", "#007ACC")
        except Exception as e:
            ide.console.err(f"[Build] Konnte Ordner nicht öffnen: {e}\n")

    def _store_exe(self, exe_path):
        if exe_path:
            self._last_exe = exe_path

    def _toggle_auto_open(self):
        self.auto_open = not self.auto_open
        self._ide._toast_msg(
            f"EXE-Ordner nach Build {'AUTO-ÖFFNEN' if self.auto_open else 'AUS'}",
            "#4EC9B0" if self.auto_open else "#F44747")

    def add_menu_items(self):
        return [
            ("EXE-Ordner öffnen", lambda: self._open_folder()),
            ("Auto-Öffnen nach Build", self._toggle_auto_open),
        ]

    def add_toolbar_items(self):
        return [("EXE-Ordner", lambda: self._open_folder())]


def register(registry):
    registry.register(BuildNotificationPlugin())