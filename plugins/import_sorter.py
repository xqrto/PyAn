import re

class ImportSorterPlugin(BasePlugin):
    name        = "Import-Sortierer / Aufraeumer"
    version     = "1.0"
    author      = "xqrto"
    description = "Sortiert, dedupliziert und bereinigt den import-Block."

    def on_startup(self, ide):
        self._ide = ide
        self.auto = True   # automatisch beim Speichern

    # ── Kern-Logik ────────────────────────────────────────────────────────
    @staticmethod
    def sort_import_block(code):
        lines = code.split("\n")

        # Kopf (leere Zeilen / Kommentare / Docstring) unangetastet lassen
        head = 0
        while head < len(lines):
            s = lines[head].strip()
            if s == "" or s.startswith("#"):
                head += 1
            elif s.startswith('"""') or s.startswith("'''"):
                delim = '"""' if s.startswith('"""') else "'''"
                head += 1
                while head < len(lines) and delim not in lines[head]:
                    head += 1
                head += 1
            else:
                break

        # zusammenhängende import-Zeilen sammeln
        imps = []
        end = head
        while end < len(lines):
            s = lines[end].strip()
            if s.startswith("import ") or s.startswith("from "):
                imps.append(lines[end])
                end += 1
            elif s == "":
                end += 1
            else:
                break

        if not imps:
            return code

        def key(line):
            first = line.strip().split()[0]
            return (0 if first == "import" else 1, line.strip())

        unique = {}
        for l in imps:
            if not l.strip():
                continue
            norm = re.sub(r"\s+", " ", l.strip())
            unique[norm] = norm

        sorted_imps = [unique[k] for k in sorted(unique, key=key)]
        rest = lines[end:]
        # überflüssige Leerzeilen direkt nach dem Block reduzieren
        while rest and rest[0].strip() == "":
            rest = rest[1:]

        result = "\n".join(lines[:head])
        if lines[:head]:
            result += "\n"
        result += "\n".join(sorted_imps)
        if rest:
            result += "\n\n" + "\n".join(rest)
        else:
            result += "\n"

        return result

    # ── Anwendung auf aktuellen Editor ────────────────────────────────────
    def _apply_to_editor(self, editor, text=None):
        if editor is None:
            return False
        code = text if text is not None else editor.toPlainText()
        new = self.sort_import_block(code)
        if new != code:
            editor.apply_fix(new)
            return True
        return False

    def _editor_for_path(self, path):
        try:
            tabs = self._ide.tabs
            for i in range(tabs.count()):
                w = tabs.widget(i)
                if getattr(w, "_file_path", None) == path:
                    return w
        except Exception:
            pass
        return None

    # ── Hooks ─────────────────────────────────────────────────────────────
    def on_file_save(self, path, content):
        if not self.auto:
            return
        try:
            ed = self._editor_for_path(path)
            if ed is None:
                ed = self._ide._ed()
            if self._apply_to_editor(ed, content):
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(ed.toPlainText())
                    self._ide._mark_saved(ed)
                    self._ide._toast_msg("Imports sortiert", "#4EC9B0")
                except Exception as e:
                    self._ide.console.err(f"[import_sorter] {e}\n")
        except Exception as e:
            self._ide.console.err(f"[import_sorter] {e}\n")

    def _sort_now(self):
        ed = self._ide._ed()
        if ed is None:
            self._ide._toast_msg("No editor active", "#F44747")
            return
        if self._apply_to_editor(ed):
            ed._modified = True
            self._ide._toast_msg("Imports sortiert", "#4EC9B0")
        else:
            self._ide._toast_msg("Nichts zu sortieren", "#DCDCAA")

    def _toggle_auto(self):
        self.auto = not self.auto
        self._ide._toast_msg(
            f"Auto-Sortieren {'AN' if self.auto else 'AUS'}",
            "#4EC9B0" if self.auto else "#F44747")

    def add_menu_items(self):
        return [
            ("Imports sortieren", self._sort_now),
            ("Auto-Sort beim Speichern", self._toggle_auto),
        ]

    def add_toolbar_items(self):
        return [("Sort Imports", self._sort_now), ("Auto", self._toggle_auto)]


def register(registry):
    registry.register(ImportSorterPlugin())