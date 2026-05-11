import sys
import os
import traceback
from pathlib import Path

# Crash log — written before any GUI so we always know what went wrong
_LOG = Path(os.environ.get("APPDATA", Path.home())) / "CodeClouds" / "EODTracker" / "crash.log"

def _write_crash(exc):
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "w") as f:
            f.write(traceback.format_exc())
    except Exception:
        pass

for d in ("data", "assets", "templates"):
    try:
        (Path(__file__).parent / d).mkdir(exist_ok=True)
    except Exception:
        pass

try:
    from PyQt6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
    from PyQt6.QtCore import Qt
    from app.database import init_db, get_setting, set_setting
except Exception as _e:
    _write_crash(_e)
    raise


def _apply_theme(app):
    from app.themes import get_colors, build_stylesheet
    theme = get_setting('theme', 'dark')
    app.setStyleSheet(build_stylesheet(get_colors(theme)))


def _setup_autostart():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(
            key, "EODTracker", 0, winreg.REG_SZ,
            f'"{sys.executable}" "{Path(__file__).resolve()}"'
        )
        winreg.CloseKey(key)
    except Exception:
        pass


def main():
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("EOD Tracker")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")

    init_db()
    _apply_theme(app)

    # Set app-wide window icon
    from app.icon_utils import app_icon
    app.setWindowIcon(app_icon())

    # First-run: employee name
    if not get_setting('employee_name'):
        name, ok = QInputDialog.getText(
            None,
            "Welcome to EOD Tracker",
            "Enter your name (used in Excel reports and task assignments):",
            QLineEdit.EchoMode.Normal
        )
        if ok and name.strip():
            set_setting('employee_name', name.strip())
        elif not ok:
            sys.exit(0)

    # First-run: auto-start
    if get_setting('autostart_asked', 'false') == 'false':
        set_setting('autostart_asked', 'true')
        msg = QMessageBox()
        msg.setWindowTitle("Auto-Start with Windows?")
        msg.setText("Start EOD Tracker automatically when Windows starts?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if msg.exec() == QMessageBox.StandardButton.Yes:
            _setup_autostart()

    from app.tray import TrayApp
    TrayApp(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception as _e:
        _write_crash(_e)
        raise
